from __future__ import annotations

import argparse
import sys
from pathlib import Path

from relion_pipeline_visualizer.parser import parse_pipeline
from relion_pipeline_visualizer.graph import get_full_graph, get_subgraph
from relion_pipeline_visualizer.mermaid import render_mermaid


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ margin: 0; padding: 20px; background: #fff; }}
    #diagram {{ text-align: center; }}
  </style>
</head>
<body>
  <div id="diagram">
    <pre class="mermaid">
{mermaid}
    </pre>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{ startOnLoad: true, fontSize: 16 }});</script>
</body>
</html>
"""


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
    parser.add_argument(
        "--output", "-o",
        help="Output path for .mmd file (default: pipeline.mmd next to star_file)",
    )

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

    mermaid_text = render_mermaid(jobs, edges, pipeline)

    # Determine output paths
    star_path = Path(args.star_file)
    if args.output:
        mmd_path = Path(args.output)
    else:
        mmd_path = star_path.parent / "pipeline.mmd"

    html_path = mmd_path.with_suffix(".html")

    # Write .mmd file
    mmd_path.write_text(mermaid_text)
    print(f"Wrote {mmd_path}", file=sys.stderr)

    # Write .html file
    title = "RELION Pipeline"
    if args.job:
        title = f"RELION Pipeline — {args.job}"
    html_path.write_text(HTML_TEMPLATE.format(title=title, mermaid=mermaid_text))
    print(f"Wrote {html_path}", file=sys.stderr)
