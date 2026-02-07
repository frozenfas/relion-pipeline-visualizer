from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import starfile


@dataclass
class ModelClassInfo:
    """Per-class statistics from a RELION model STAR file."""
    class_index: int
    class_distribution: float
    accuracy_rotations: float
    accuracy_translations_angst: float
    estimated_resolution: float
    overall_fourier_completeness: float


@dataclass
class Job:
    name: str  # e.g. "Refine3D/job058/"
    alias: str | None  # e.g. "Refine3D/j087_J068_c01/" or None
    type_label: str  # e.g. "relion.refine3d"
    status: str  # e.g. "Succeeded", "Failed", "Running"
    last_command: str | None = None
    model_classes: list[ModelClassInfo] | None = None

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
            return f"{alias_short}<br/>{self.job_type}"
        return self.name.rstrip("/")


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


def parse_note_txt(project_dir: Path, job_name: str) -> str | None:
    """Extract the last executed command from a job's note.txt file."""
    note_path = project_dir / job_name / "note.txt"
    if not note_path.is_file():
        return None
    text = note_path.read_text()
    # Each command block: line starting with ` through to the next ++++ line
    commands = re.findall(r"^(`[^\n]+)", text, re.MULTILINE)
    return commands[-1].strip() if commands else None


def parse_model_star(model_path: Path) -> list[ModelClassInfo] | None:
    """Parse a RELION model STAR file and extract per-class statistics."""
    if not model_path.is_file():
        return None
    try:
        data = starfile.read(str(model_path))
    except Exception:
        return None

    table_key = None
    for key in data:
        if "model_classes" in key:
            table_key = key
            break
    if table_key is None:
        return None

    df = data[table_key]
    results = []
    for _, row in df.iterrows():
        results.append(ModelClassInfo(
            class_index=len(results) + 1,
            class_distribution=float(row.get("rlnClassDistribution", 0.0)),
            accuracy_rotations=float(row.get("rlnAccuracyRotations", 0.0)),
            accuracy_translations_angst=float(row.get("rlnAccuracyTranslationsAngst", 0.0)),
            estimated_resolution=float(row.get("rlnEstimatedResolution", 0.0)),
            overall_fourier_completeness=float(row.get("rlnOverallFourierCompleteness", 0.0)),
        ))
    return results if results else None


def find_last_iteration_model(project_dir: Path, job_name: str) -> Path | None:
    """Find the last iteration model STAR file for a Class3D job."""
    job_dir = project_dir / job_name
    model_files = sorted(job_dir.glob("run_it*_model.star"))
    return model_files[-1] if model_files else None


def enrich_jobs(pipeline: Pipeline, project_dir: Path) -> None:
    """Enrich jobs with note.txt commands and model data. Modifies in-place."""
    for job_name, job in pipeline.jobs.items():
        job.last_command = parse_note_txt(project_dir, job_name)

        if job.job_type == "Refine3D":
            model_path = project_dir / job_name / "run_model.star"
            job.model_classes = parse_model_star(model_path)
        elif job.job_type == "Class3D":
            model_path = find_last_iteration_model(project_dir, job_name)
            if model_path:
                job.model_classes = parse_model_star(model_path)
