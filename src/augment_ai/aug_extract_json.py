#!/usr/bin/env python3
import argparse
from .aug_common import extract_json_from_xml, save_json_output

def main():
    parser = argparse.ArgumentParser(description="Extract JSON from XML")
    parser.add_argument("input_file", help="Input XML file path")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    json_data = extract_json_from_xml(args.input_file)
    save_json_output(json_data, args.output)

if __name__ == "__main__":
    main()