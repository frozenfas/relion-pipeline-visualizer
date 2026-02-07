# relion-pipeline-visualizer
# Copyright (C) 2025 Sean Connell <sean.connell@gmail.com>
# Structural Biology of Cellular Machines Laboratory, Biobizkaia
# Licensed under the GNU General Public License v3.0 (GPL-3.0)

from __future__ import annotations

from relion_pipeline_visualizer.parser import Pipeline

# Color palette by job type
TYPE_STYLES = {
    "Import": "fill:#4CAF50,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "Extract": "fill:#8BC34A,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "Refine3D": "fill:#2196F3,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "Class3D": "fill:#FF9800,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "Select": "fill:#9C27B0,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "MaskCreate": "fill:#607D8B,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "PostProcess": "fill:#00BCD4,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "CtfRefine": "fill:#3F51B5,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "MultiBody": "fill:#E91E63,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "Subtract": "fill:#795548,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
    "JoinStar": "fill:#009688,color:#fff,font-size:48px,stroke:#333,stroke-width:4px",
}

STATUS_STYLES = {
    "Failed": "stroke:#f44336,stroke-width:6px",
    "Running": "stroke:#FF9800,stroke-width:6px,stroke-dasharray:5",
}


def render_mermaid(
    jobs: set[str],
    edges: set[tuple[str, str]],
    pipeline: Pipeline,
) -> str:
    lines = ["graph TD"]

    # Group jobs by type for class assignment
    type_members: dict[str, list[str]] = {}
    status_members: dict[str, list[str]] = {}

    # Sort jobs for deterministic output
    for job_name in sorted(jobs):
        job = pipeline.jobs.get(job_name)
        if job is None:
            continue
        node_id = job.job_id
        label = job.display_label
        lines.append(f'    {node_id}["{label}"]')

        job_type = job.job_type
        if job_type in TYPE_STYLES:
            type_members.setdefault(job_type, []).append(node_id)

        if job.status in STATUS_STYLES:
            status_members.setdefault(job.status, []).append(node_id)

    lines.append("")

    # Edges (sorted for deterministic output)
    for src, tgt in sorted(edges):
        src_job = pipeline.jobs.get(src)
        tgt_job = pipeline.jobs.get(tgt)
        if src_job and tgt_job:
            lines.append(f"    {src_job.job_id} --> {tgt_job.job_id}")

    lines.append("")

    # classDef for each job type
    for type_name, style in TYPE_STYLES.items():
        css_class = type_name.lower()
        lines.append(f"    classDef {css_class} {style}")

    # classDef for status overrides
    for status, style in STATUS_STYLES.items():
        css_class = status.lower()
        lines.append(f"    classDef {css_class} {style}")

    lines.append("")

    # Apply type classes
    for type_name, members in sorted(type_members.items()):
        css_class = type_name.lower()
        member_list = ",".join(sorted(members))
        lines.append(f"    class {member_list} {css_class}")

    # Apply status classes (these override the border/stroke only)
    for status, members in sorted(status_members.items()):
        css_class = status.lower()
        member_list = ",".join(sorted(members))
        lines.append(f"    class {member_list} {css_class}")

    return "\n".join(lines) + "\n"
