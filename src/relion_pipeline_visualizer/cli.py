from __future__ import annotations

import argparse
import json
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
    .job-tooltip {{
      position: absolute;
      background: #222;
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      font: 14px/1.4 monospace;
      white-space: pre;
      pointer-events: none;
      z-index: 1000;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}
  </style>
</head>
<body>
  <div id="diagram">
    <pre class="mermaid">
{mermaid}
    </pre>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <script>
    const jobInfo = {job_info_json};

    mermaid.initialize({{ startOnLoad: true, fontSize: 16 }});

    // Attach tooltips after Mermaid renders
    window.addEventListener("load", function() {{
      const tip = document.createElement("div");
      tip.className = "job-tooltip";
      tip.style.display = "none";
      document.body.appendChild(tip);

      document.querySelectorAll(".node").forEach(function(node) {{
        const id = node.getAttribute("data-id") || node.id;
        const info = jobInfo[id];
        if (!info) return;

        node.style.cursor = "pointer";
        node.addEventListener("mouseenter", function(e) {{
          let lines = [];
          lines.push("Job:    " + info.name);
          if (info.alias) lines.push("Alias:  " + info.alias);
          lines.push("Type:   " + info.type_label);
          lines.push("Status: " + info.status);
          tip.textContent = lines.join("\\n");
          tip.style.display = "block";
        }});
        node.addEventListener("mousemove", function(e) {{
          tip.style.left = (e.pageX + 12) + "px";
          tip.style.top = (e.pageY + 12) + "px";
        }});
        node.addEventListener("mouseleave", function() {{
          tip.style.display = "none";
        }});
      }});
    }});
  </script>
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

    # Build tooltip data keyed by Mermaid node ID
    job_info = {}
    for job_name in jobs:
        job = pipeline.jobs.get(job_name)
        if job:
            job_info[job.job_id] = {
                "name": job.name,
                "alias": job.alias,
                "type_label": job.type_label,
                "status": job.status,
            }

    # Write .html file
    title = "RELION Pipeline"
    if args.job:
        title = f"RELION Pipeline — {args.job}"
    html_content = HTML_TEMPLATE.format(
        title=title,
        mermaid=mermaid_text,
        job_info_json=json.dumps(job_info),
    )
    html_path.write_text(html_content)
    print(f"Wrote {html_path}", file=sys.stderr)
