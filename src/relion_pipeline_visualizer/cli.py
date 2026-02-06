from __future__ import annotations

import argparse
import sys

from relion_pipeline_visualizer.parser import parse_pipeline
from relion_pipeline_visualizer.graph import get_full_graph, get_subgraph
from relion_pipeline_visualizer.mermaid import render_mermaid


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Visualize a RELION pipeline STAR file as a Mermaid diagram.",
    )
    parser.add_argument("star_file", help="Path to default_pipeline.star")
    parser.add_argument("--job", help="Focus on a specific job (e.g. 'Refine3D/job058/')")
    parser.add_argument(
        "--upstream",
        action="store_true",
        help="Include upstream ancestors (default when --job is given)",
    )
    parser.add_argument(
        "--downstream",
        action="store_true",
        help="Include downstream descendants",
    )
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")

    args = parser.parse_args(argv)
    pipeline = parse_pipeline(args.star_file)

    if args.job:
        job_name = args.job
        if job_name not in pipeline.jobs:
            print(f"Error: job '{job_name}' not found in pipeline.", file=sys.stderr)
            print("Available jobs:", file=sys.stderr)
            for name in sorted(pipeline.jobs):
                print(f"  {name}", file=sys.stderr)
            sys.exit(1)

        upstream = args.upstream
        downstream = args.downstream
        # Default to upstream if neither flag given
        if not upstream and not downstream:
            upstream = True

        jobs, edges = get_subgraph(pipeline, job_name, upstream=upstream, downstream=downstream)
    else:
        jobs, edges = get_full_graph(pipeline)

    mermaid = render_mermaid(jobs, edges, pipeline)

    if args.output:
        with open(args.output, "w") as f:
            f.write(mermaid)
        print(f"Wrote Mermaid diagram to {args.output}", file=sys.stderr)
    else:
        print(mermaid)
