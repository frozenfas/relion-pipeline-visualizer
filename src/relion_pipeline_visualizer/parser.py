from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import starfile


@dataclass
class Job:
    name: str  # e.g. "Refine3D/job058/"
    alias: str | None  # e.g. "Refine3D/j087_J068_c01/" or None
    type_label: str  # e.g. "relion.refine3d"
    status: str  # e.g. "Succeeded", "Failed", "Running"

    @property
    def job_type(self) -> str:
        """Extract short type like 'Refine3D' from the job name."""
        return self.name.split("/")[0]

    @property
    def job_id(self) -> str:
        """Extract job ID like 'job058' from the job name."""
        m = re.search(r"(job\d+)", self.name)
        return m.group(1) if m else self.name

    @property
    def display_label(self) -> str:
        """Label for Mermaid node display."""
        if self.alias:
            alias_short = self.alias.rstrip("/").split("/")[-1]
            return f"{alias_short}<br/>{self.job_type} | {self.status}"
        return f"{self.name.rstrip('/')}<br/>{self.status}"


@dataclass
class Pipeline:
    jobs: dict[str, Job] = field(default_factory=dict)
    edges: set[tuple[str, str]] = field(default_factory=set)  # (source_job, target_job)


def parse_pipeline(path: str | Path) -> Pipeline:
    data = starfile.read(str(path))

    processes = data["pipeline_processes"]
    input_edges = data["pipeline_input_edges"]
    output_edges = data["pipeline_output_edges"]

    # Build job lookup
    pipeline = Pipeline()
    for _, row in processes.iterrows():
        name = row["rlnPipeLineProcessName"]
        alias_raw = row["rlnPipeLineProcessAlias"]
        alias = None if alias_raw == "None" else alias_raw
        pipeline.jobs[name] = Job(
            name=name,
            alias=alias,
            type_label=row["rlnPipeLineProcessTypeLabel"],
            status=row["rlnPipeLineProcessStatusLabel"],
        )

    # Build node-to-producing-job map from output edges
    # output_edges: Job -> Node
    node_producer: dict[str, str] = {}
    for _, row in output_edges.iterrows():
        job_name = row["rlnPipeLineEdgeProcess"]
        node_name = row["rlnPipeLineEdgeToNode"]
        node_producer[node_name] = job_name

    # Derive job-to-job edges from input edges
    # input_edges: Node -> Job (node is consumed by job)
    for _, row in input_edges.iterrows():
        node_name = row["rlnPipeLineEdgeFromNode"]
        target_job = row["rlnPipeLineEdgeProcess"]
        source_job = node_producer.get(node_name)
        if source_job and source_job != target_job:
            pipeline.edges.add((source_job, target_job))

    return pipeline
