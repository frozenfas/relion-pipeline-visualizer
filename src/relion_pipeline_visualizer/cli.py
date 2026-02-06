from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from relion_pipeline_visualizer.parser import parse_pipeline, enrich_jobs
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
      white-space: pre-wrap;
      max-width: 700px;
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
    var jobInfo = {job_info_json};

    mermaid.initialize({{ startOnLoad: false, fontSize: 48 }});

    mermaid.run().then(function() {{
      var tip = document.createElement("div");
      tip.className = "job-tooltip";
      tip.style.display = "none";
      document.body.appendChild(tip);

      function findJobId(node) {{
        var did = node.getAttribute("data-id");
        if (did && jobInfo[did]) return did;
        var m = node.id.match(/job\\d+/);
        return m ? m[0] : null;
      }}

      document.querySelectorAll(".node").forEach(function(node) {{
        var jobId = findJobId(node);
        if (!jobId) return;
        var info = jobInfo[jobId];
        if (!info) return;

        node.style.cursor = "pointer";
        node.addEventListener("mouseenter", function(e) {{
          var lines = [];
          lines.push("Job:    " + info.name);
          if (info.alias) lines.push("Alias:  " + info.alias);
          lines.push("Type:   " + info.type_label);
          lines.push("Status: " + info.status);

          if (info.last_command) {{
            lines.push("");
            lines.push("Command:");
            var cmd = info.last_command;
            if (cmd.length > 300) cmd = cmd.substring(0, 300) + "...";
            lines.push("  " + cmd);
          }}

          if (info.model_classes && info.model_classes.length > 0) {{
            lines.push("");
            if (info.model_classes.length === 1) {{
              var mc = info.model_classes[0];
              lines.push("Resolution:   " + mc.resolution.toFixed(2) + " A");
              lines.push("Completeness: " + (mc.completeness * 100).toFixed(1) + "%");
              lines.push("Distribution: " + (mc.distribution * 100).toFixed(1) + "%");
              lines.push("Acc. rot:     " + mc.accuracy_rot.toFixed(2) + " deg");
              lines.push("Acc. trans:   " + mc.accuracy_trans.toFixed(2) + " A");
            }} else {{
              lines.push("Classes:");
              info.model_classes.forEach(function(mc) {{
                lines.push("  Class " + mc.class_index
                  + ": " + mc.resolution.toFixed(2) + " A"
                  + " | " + (mc.completeness * 100).toFixed(1) + "%"
                  + " | " + (mc.distribution * 100).toFixed(1) + "%"
                  + " | " + mc.accuracy_rot.toFixed(2) + " deg");
              }});
            }}
          }}

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


def _resolve_job_name(query: str, pipeline) -> str | None:
    """Resolve a shorthand job query to a full pipeline job name.

    Accepts: '93', 'job093', or 'Refine3D/job093/' (full name).
    """
    import re as _re

    # Exact match first
    if query in pipeline.jobs:
        return query

    # Normalise bare number to jobNNN
    if _re.fullmatch(r"\d+", query):
        query = f"job{query.zfill(3)}"

    # Match by job ID suffix (e.g. "job093" matches "Refine3D/job093/")
    matches = [name for name in pipeline.jobs if f"/{query}" in name or name.startswith(f"{query}/")]
    if len(matches) == 1:
        return matches[0]

    # Also try without leading zeros for high numbers
    if matches:
        return matches[0]

    return None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Visualize a RELION pipeline STAR file as a Mermaid diagram.",
    )
    parser.add_argument("star_file", help="Path to default_pipeline.star")
    parser.add_argument("--job", help="Focus on a specific job (e.g. '93', 'job093', or 'Refine3D/job093/')")
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
        help="Base name for output files, e.g. 'my_pipeline' produces my_pipeline.mmd and my_pipeline.html (default: pipeline.mmd/.html next to star_file)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Open the diagram in mermaid.live in your browser",
    )
    parser.add_argument(
        "--kroki",
        action="store_true",
        help="Open the diagram as SVG via kroki.io in your browser",
    )

    args = parser.parse_args(argv)
    star_path = Path(args.star_file)
    project_dir = star_path.parent

    print(f"Reading pipeline from: {star_path}", file=sys.stderr)
    pipeline = parse_pipeline(args.star_file)
    print(f"Found {len(pipeline.jobs)} jobs and {len(pipeline.edges)} edges", file=sys.stderr)

    print("Enriching jobs with note.txt commands and model statistics...", file=sys.stderr)
    enrich_jobs(pipeline, project_dir)
    n_commands = sum(1 for j in pipeline.jobs.values() if j.last_command)
    n_models = sum(1 for j in pipeline.jobs.values() if j.model_classes)
    print(f"  {n_commands} jobs with commands, {n_models} jobs with model data", file=sys.stderr)

    if args.job:
        job_name = _resolve_job_name(args.job, pipeline)
        if job_name is None:
            print(f"Error: job '{args.job}' not found in pipeline.", file=sys.stderr)
            print("Available jobs:", file=sys.stderr)
            for name in sorted(pipeline.jobs):
                print(f"  {name}", file=sys.stderr)
            sys.exit(1)

        upstream = args.upstream
        downstream = args.downstream
        # Default to upstream if neither flag given
        if not upstream and not downstream:
            upstream = True

        direction = []
        if upstream:
            direction.append("upstream")
        if downstream:
            direction.append("downstream")
        print(f"Extracting subgraph for {job_name} ({' + '.join(direction)})...", file=sys.stderr)
        jobs, edges = get_subgraph(pipeline, job_name, upstream=upstream, downstream=downstream)
        print(f"  Subgraph: {len(jobs)} jobs, {len(edges)} edges", file=sys.stderr)
    else:
        print("Rendering full pipeline...", file=sys.stderr)
        jobs, edges = get_full_graph(pipeline)

    mermaid_text = render_mermaid(jobs, edges, pipeline)

    # Determine output paths
    if args.output:
        out = Path(args.output)
        # If user gave a path with extension, use it; otherwise treat as base name
        if out.suffix in (".mmd", ".html"):
            mmd_path = out.with_suffix(".mmd")
        else:
            mmd_path = out.with_suffix(".mmd")
    else:
        mmd_path = star_path.parent / "pipeline.mmd"

    html_path = mmd_path.with_suffix(".html")

    # Write .mmd file
    mmd_path.write_text(mermaid_text)
    print(f"Wrote Mermaid diagram: {mmd_path}", file=sys.stderr)

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
                "last_command": job.last_command,
                "model_classes": [
                    {
                        "class_index": mc.class_index,
                        "resolution": mc.estimated_resolution,
                        "completeness": mc.overall_fourier_completeness,
                        "distribution": mc.class_distribution,
                        "accuracy_rot": mc.accuracy_rotations,
                        "accuracy_trans": mc.accuracy_translations_angst,
                    }
                    for mc in job.model_classes
                ] if job.model_classes else None,
            }

    # Write .html file
    title = "RELION Pipeline"
    if args.job:
        title = f"RELION Pipeline — {job_name}"
    html_content = HTML_TEMPLATE.format(
        title=title,
        mermaid=mermaid_text,
        job_info_json=json.dumps(job_info),
    )
    html_path.write_text(html_content)
    print(f"Wrote HTML viewer:    {html_path}", file=sys.stderr)

    if args.live:
        import base64
        import webbrowser
        state = json.dumps({
            "code": mermaid_text,
            "mermaid": {"theme": "default"},
            "autoSync": True,
            "updateDiagram": True,
        })
        encoded = base64.urlsafe_b64encode(state.encode()).decode().rstrip("=")
        url = f"https://mermaid.live/edit#base64:{encoded}"
        print(f"mermaid.live URL:     {url}", file=sys.stderr)
        webbrowser.open(url)

    if args.kroki:
        import base64
        import webbrowser
        import zlib
        compressed = zlib.compress(mermaid_text.encode(), 9)
        encoded = base64.urlsafe_b64encode(compressed).decode()
        url = f"https://kroki.io/mermaid/svg/{encoded}"
        print(f"kroki.io URL:         {url}", file=sys.stderr)
        webbrowser.open(url)

    if args.live or args.kroki:
        print("Note: enriched tooltips (commands, model stats) only work in the HTML output.", file=sys.stderr)

    print("Done.", file=sys.stderr)
