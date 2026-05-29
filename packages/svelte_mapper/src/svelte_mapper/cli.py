#!/usr/bin/env python3
"""
svelte-map — Print a compact structural map of a Svelte/TS project.

Usage:
    svelte-map                         # scan current dir, all layers
    svelte-map /path/to/project        # explicit root
    svelte-map --layers file_tree import_graph
    svelte-map --format json           # output as JSON dict
    svelte-map --out map.yaml          # write to file
"""
import argparse
import json
import sys
from pathlib import Path

from svelte_mapper.scanner import Scanner
from svelte_mapper.graph import ImportGraph
from svelte_mapper.renderer import MapRenderer, RendererConfig, OutputLayer, _ALL_LAYERS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="svelte-map",
        description="Compact structural map of a Svelte/TS codebase for LLM agents.",
    )
    p.add_argument(
        "root", nargs="?", default=".",
        help="Project root directory (default: current directory).",
    )
    p.add_argument(
        "--layers", nargs="+",
        choices=[l.value for l in _ALL_LAYERS],
        default=None,
        metavar="LAYER",
        help="Layers to include. Choices: file_tree import_graph component_signatures store_topology",
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--out", metavar="FILE",
        help="Write output to FILE instead of stdout.",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Error: '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Scan
    project = Scanner.scan(root)
    graph = ImportGraph.build(project)

    # Render
    layers = (
        [OutputLayer(v) for v in args.layers]
        if args.layers
        else None
    )
    config = RendererConfig(layers=layers)
    renderer = MapRenderer(project=project, graph=graph, config=config)

    if args.format == "json":
        output = json.dumps(renderer.render_to_dict(), indent=2)
    else:
        output = renderer.render()

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Written to {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
