# relion-pipeline-visualizer
# Copyright (C) 2025 Sean Connell <sean.connell@gmail.com>
# Structural Biology of Cellular Machines Laboratory, Biobizkaia
# Licensed under the GNU General Public License v3.0 (GPL-3.0)

from __future__ import annotations

from collections import defaultdict, deque

from relion_pipeline_visualizer.parser import Pipeline


def get_full_graph(pipeline: Pipeline) -> tuple[set[str], set[tuple[str, str]]]:
    """Return all jobs and edges."""
    return set(pipeline.jobs.keys()), set(pipeline.edges)


def get_ancestors(pipeline: Pipeline, job_name: str) -> tuple[set[str], set[tuple[str, str]]]:
    """BFS backwards from job_name, returning upstream jobs and edges."""
    # Build reverse adjacency: target -> set of sources
    reverse_adj: dict[str, set[str]] = defaultdict(set)
    for src, tgt in pipeline.edges:
        reverse_adj[tgt].add(src)

    visited: set[str] = {job_name}
    queue = deque([job_name])
    edges: set[tuple[str, str]] = set()

    while queue:
        current = queue.popleft()
        for parent in reverse_adj.get(current, set()):
            edges.add((parent, current))
            if parent not in visited:
                visited.add(parent)
                queue.append(parent)

    return visited, edges


def get_descendants(pipeline: Pipeline, job_name: str) -> tuple[set[str], set[tuple[str, str]]]:
    """BFS forwards from job_name, returning downstream jobs and edges."""
    forward_adj: dict[str, set[str]] = defaultdict(set)
    for src, tgt in pipeline.edges:
        forward_adj[src].add(tgt)

    visited: set[str] = {job_name}
    queue = deque([job_name])
    edges: set[tuple[str, str]] = set()

    while queue:
        current = queue.popleft()
        for child in forward_adj.get(current, set()):
            edges.add((current, child))
            if child not in visited:
                visited.add(child)
                queue.append(child)

    return visited, edges


def get_subgraph(
    pipeline: Pipeline,
    job_name: str,
    upstream: bool = True,
    downstream: bool = False,
) -> tuple[set[str], set[tuple[str, str]]]:
    """Combine ancestors and/or descendants based on flags."""
    jobs: set[str] = {job_name}
    edges: set[tuple[str, str]] = set()

    if upstream:
        up_jobs, up_edges = get_ancestors(pipeline, job_name)
        jobs |= up_jobs
        edges |= up_edges

    if downstream:
        down_jobs, down_edges = get_descendants(pipeline, job_name)
        jobs |= down_jobs
        edges |= down_edges

    return jobs, edges
