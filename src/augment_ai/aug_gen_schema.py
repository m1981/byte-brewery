#!/usr/bin/env python3
import json
import sys
from typing import Dict, List, Any, Union, Optional
import datetime

def get_type(value: Any) -> str:
    """Determine the JSON Schema type of a value."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, str):
        # Check if it's a date-time format
        try:
            datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
            return "string", {"format": "date-time"}
        except (ValueError, TypeError):
            return "string", {}
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    else:
        return "unknown"

def infer_array_schema(array: List[Any]) -> Dict[str, Any]:
    """Infer schema for an array by examining its items."""
    if not array:
        return {"type": "array", "items": {}}

    # Check if all items are of the same type
    item_types = set()
    item_schemas = []

    for item in array:
        if isinstance(item, dict):
            item_schema = infer_object_schema(item)
            item_schemas.append(item_schema)
            item_types.add("object")
        elif isinstance(item, list):
            item_schema = infer_array_schema(item)
            item_schemas.append(item_schema)
            item_types.add("array")
        else:
            type_info = get_type(item)
            if isinstance(type_info, tuple):
                type_name, type_format = type_info
                item_types.add(type_name)
            else:
                item_types.add(type_info)

    # If all items are objects with the same structure, merge their schemas
    if len(item_types) == 1 and "object" in item_types:
        merged_schema = {"type": "object", "properties": {}}
        all_properties = set()

        # Collect all property names
        for schema in item_schemas:
            all_properties.update(schema.get("properties", {}).keys())

        # Merge property schemas
        for prop in all_properties:
            prop_schemas = [s.get("properties", {}).get(prop, {}) for s in item_schemas if prop in s.get("properties", {})]
            if prop_schemas:
                merged_schema["properties"][prop] = prop_schemas[0]  # Use the first schema as a base

        return {"type": "array", "items": merged_schema}

    # If all items are of the same primitive type
    elif len(item_types) == 1 and "object" not in item_types and "array" not in item_types:
        type_name = list(item_types)[0]
        if any(isinstance(get_type(item), tuple) for item in array):
            # Handle formatted strings
            for item in array:
                type_info = get_type(item)
                if isinstance(type_info, tuple):
                    _, type_format = type_info
                    return {"type": "array", "items": {"type": type_name, "format": type_format.get("format")}}
        return {"type": "array", "items": {"type": type_name}}

    # Mixed types
    else:
        return {"type": "array", "items": {}}

def infer_object_schema(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively infer schema for a JSON object."""
    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }

    for key, value in obj.items():
        if value is not None:  # Consider non-null values as required
            schema["required"].append(key)

        if isinstance(value, dict):
            schema["properties"][key] = infer_object_schema(value)
        elif isinstance(value, list):
            schema["properties"][key] = infer_array_schema(value)
        else:
            type_info = get_type(value)
            if isinstance(type_info, tuple):
                type_name, type_format = type_info
                schema["properties"][key] = {"type": type_name, **type_format}
            else:
                schema["properties"][key] = {"type": type_info}

    return schema

def generate_schema(json_data: Union[Dict, List], title: str = "Generated Schema") -> Dict[str, Any]:
    """Generate a JSON Schema from JSON data."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": title,
        "description": "Automatically generated schema"
    }

    if isinstance(json_data, dict):
        schema.update(infer_object_schema(json_data))
    elif isinstance(json_data, list):
        schema.update(infer_array_schema(json_data))
    else:
        type_info = get_type(json_data)
        if isinstance(type_info, tuple):
            type_name, type_format = type_info
            schema.update({"type": type_name, **type_format})
        else:
            schema.update({"type": type_info})

    return schema

def analyze_json_file(json_file: str, output_file: Optional[str] = None) -> None:
    """Analyze a JSON file and generate its schema."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        schema = generate_schema(json_data, title=f"Schema for {json_file}")

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2)
            print(f"Schema generated and saved to {output_file}")
        else:
            print(json.dumps(schema, indent=2))

    except Exception as e:
        print(f"Error analyzing JSON file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python aug_gen_schema.py <json_file> [output_schema_file]")
        sys.exit(1)

    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    analyze_json_file(json_file, output_file)
