"""Tests for the RELION pipeline visualizer using a small 11-job pipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

from relion_pipeline_visualizer.parser import (
    Pipeline,
    parse_pipeline,
    enrich_jobs,
    parse_note_txt,
    parse_model_star,
    find_last_iteration_model,
)
from relion_pipeline_visualizer.graph import (
    get_full_graph,
    get_ancestors,
    get_descendants,
    get_subgraph,
)
from relion_pipeline_visualizer.mermaid import render_mermaid
from relion_pipeline_visualizer.cli import _resolve_job_name

DATA_DIR = Path(__file__).parent / "data"
SMALL_STAR = DATA_DIR / "small_pipeline.star"
SMALL_PROJECT = DATA_DIR / "small_project"
FULL_STAR = DATA_DIR / "default_pipeline.star"


# ── Parser tests ──────────────────────────────────────────────────────


@pytest.fixture
def small_pipeline() -> Pipeline:
    return parse_pipeline(SMALL_STAR)


@pytest.fixture
def full_pipeline() -> Pipeline:
    return parse_pipeline(FULL_STAR)


class TestParsePipeline:
    def test_job_count(self, small_pipeline: Pipeline):
        assert len(small_pipeline.jobs) == 11

    def test_all_job_types_present(self, small_pipeline: Pipeline):
        types = {j.job_type for j in small_pipeline.jobs.values()}
        expected = {
            "Import", "Extract", "JoinStar", "Refine3D", "MaskCreate",
            "Class3D", "Select", "CtfRefine", "PostProcess", "MultiBody",
            "Subtract",
        }
        assert types == expected

    def test_job_statuses(self, small_pipeline: Pipeline):
        statuses = {j.job_type: j.status for j in small_pipeline.jobs.values()}
        assert statuses["Class3D"] == "Failed"
        assert statuses["Subtract"] == "Running"
        assert statuses["Import"] == "Succeeded"

    def test_alias_parsed(self, small_pipeline: Pipeline):
        job = small_pipeline.jobs["Select/job007/"]
        assert job.alias == "Select/j007_best_class/"

    def test_no_alias_is_none(self, small_pipeline: Pipeline):
        job = small_pipeline.jobs["Import/job001/"]
        assert job.alias is None

    def test_edge_count(self, small_pipeline: Pipeline):
        # 11 input edge rows, but some share the same producer, giving unique job pairs
        assert len(small_pipeline.edges) > 0

    def test_expected_edges(self, small_pipeline: Pipeline):
        edges = small_pipeline.edges
        assert ("Import/job001/", "Extract/job002/") in edges
        assert ("Extract/job002/", "JoinStar/job003/") in edges
        assert ("JoinStar/job003/", "Refine3D/job004/") in edges
        assert ("Refine3D/job004/", "MaskCreate/job005/") in edges
        assert ("Refine3D/job004/", "Class3D/job006/") in edges
        assert ("MaskCreate/job005/", "Class3D/job006/") in edges
        assert ("Class3D/job006/", "Select/job007/") in edges
        assert ("Refine3D/job004/", "CtfRefine/job008/") in edges
        assert ("Refine3D/job004/", "MultiBody/job010/") in edges
        assert ("MultiBody/job010/", "Subtract/job011/") in edges

    def test_job_properties(self, small_pipeline: Pipeline):
        job = small_pipeline.jobs["Refine3D/job004/"]
        assert job.job_type == "Refine3D"
        assert job.job_id == "job004"
        assert job.type_label == "relion.refine3d"

    def test_display_label_no_alias(self, small_pipeline: Pipeline):
        job = small_pipeline.jobs["Import/job001/"]
        assert job.display_label == "Import/job001"

    def test_display_label_with_alias(self, small_pipeline: Pipeline):
        job = small_pipeline.jobs["Select/job007/"]
        assert "j007_best_class" in job.display_label
        assert "Select" in job.display_label

    def test_full_pipeline_parses(self, full_pipeline: Pipeline):
        assert len(full_pipeline.jobs) == 98
        assert len(full_pipeline.edges) > 100


# ── Enrichment tests ─────────────────────────────────────────────────


class TestEnrichment:
    def test_parse_note_txt(self):
        cmd = parse_note_txt(SMALL_PROJECT, "Refine3D/job004/")
        assert cmd is not None
        assert "relion_refine_mpi" in cmd
        assert "--particle_diameter 300" in cmd

    def test_parse_note_txt_missing(self):
        cmd = parse_note_txt(SMALL_PROJECT, "Extract/job002/")
        assert cmd is None

    def test_parse_model_star_refine3d(self):
        model_path = SMALL_PROJECT / "Refine3D/job004/run_model.star"
        classes = parse_model_star(model_path)
        assert classes is not None
        assert len(classes) == 1
        mc = classes[0]
        assert mc.class_index == 1
        assert abs(mc.estimated_resolution - 3.2) < 0.01
        assert abs(mc.overall_fourier_completeness - 0.95) < 0.01
        assert abs(mc.class_distribution - 1.0) < 0.01
        assert abs(mc.accuracy_rotations - 1.5) < 0.01
        assert abs(mc.accuracy_translations_angst - 0.35) < 0.01

    def test_parse_model_star_class3d(self):
        model_path = SMALL_PROJECT / "Class3D/job006/run_it025_model.star"
        classes = parse_model_star(model_path)
        assert classes is not None
        assert len(classes) == 3
        assert abs(classes[0].estimated_resolution - 4.5) < 0.01
        assert abs(classes[1].estimated_resolution - 5.2) < 0.01
        assert abs(classes[2].estimated_resolution - 7.1) < 0.01

    def test_parse_model_star_missing(self):
        classes = parse_model_star(SMALL_PROJECT / "nonexistent.star")
        assert classes is None

    def test_find_last_iteration_model(self):
        model = find_last_iteration_model(SMALL_PROJECT, "Class3D/job006/")
        assert model is not None
        assert "run_it025_model.star" in model.name

    def test_find_last_iteration_model_missing(self):
        model = find_last_iteration_model(SMALL_PROJECT, "Import/job001/")
        assert model is None

    def test_enrich_jobs(self):
        pipeline = parse_pipeline(SMALL_STAR)
        enrich_jobs(pipeline, SMALL_PROJECT)

        # Refine3D/job004 should have command and 1-class model
        r3d = pipeline.jobs["Refine3D/job004/"]
        assert r3d.last_command is not None
        assert "relion_refine_mpi" in r3d.last_command
        assert r3d.model_classes is not None
        assert len(r3d.model_classes) == 1

        # Class3D/job006 should have command and 3-class model
        c3d = pipeline.jobs["Class3D/job006/"]
        assert c3d.last_command is not None
        assert c3d.model_classes is not None
        assert len(c3d.model_classes) == 3

        # Import/job001 should have command but no model
        imp = pipeline.jobs["Import/job001/"]
        assert imp.last_command is not None
        assert imp.model_classes is None

        # Extract/job002 has no note.txt
        ext = pipeline.jobs["Extract/job002/"]
        assert ext.last_command is None


# ── Graph tests ──────────────────────────────────────────────────────


class TestGraph:
    def test_full_graph(self, small_pipeline: Pipeline):
        jobs, edges = get_full_graph(small_pipeline)
        assert len(jobs) == 11
        assert edges == small_pipeline.edges

    def test_ancestors_leaf(self, small_pipeline: Pipeline):
        """Select/job007 ancestors: Class3D/job006 <- Refine3D/job004 + MaskCreate/job005 <- ... <- Import/job001"""
        jobs, edges = get_ancestors(small_pipeline, "Select/job007/")
        assert "Select/job007/" in jobs
        assert "Class3D/job006/" in jobs
        assert "Refine3D/job004/" in jobs
        assert "MaskCreate/job005/" in jobs
        assert "Import/job001/" in jobs
        # Should NOT include CtfRefine, PostProcess, MultiBody, Subtract (different branches)
        assert "CtfRefine/job008/" not in jobs
        assert "Subtract/job011/" not in jobs

    def test_ancestors_root(self, small_pipeline: Pipeline):
        """Import/job001 has no ancestors."""
        jobs, edges = get_ancestors(small_pipeline, "Import/job001/")
        assert jobs == {"Import/job001/"}
        assert len(edges) == 0

    def test_descendants_from_refine(self, small_pipeline: Pipeline):
        """Refine3D/job004 feeds into many jobs downstream."""
        jobs, edges = get_descendants(small_pipeline, "Refine3D/job004/")
        assert "Refine3D/job004/" in jobs
        assert "MaskCreate/job005/" in jobs
        assert "Class3D/job006/" in jobs
        assert "Select/job007/" in jobs
        assert "CtfRefine/job008/" in jobs
        assert "PostProcess/job009/" in jobs
        assert "MultiBody/job010/" in jobs
        assert "Subtract/job011/" in jobs
        # Should NOT include upstream jobs
        assert "Import/job001/" not in jobs
        assert "Extract/job002/" not in jobs

    def test_descendants_leaf(self, small_pipeline: Pipeline):
        """Subtract/job011 has no descendants."""
        jobs, edges = get_descendants(small_pipeline, "Subtract/job011/")
        assert jobs == {"Subtract/job011/"}
        assert len(edges) == 0

    def test_subgraph_upstream_only(self, small_pipeline: Pipeline):
        jobs, edges = get_subgraph(small_pipeline, "Select/job007/", upstream=True, downstream=False)
        assert "Import/job001/" in jobs
        assert "Select/job007/" in jobs
        assert "Subtract/job011/" not in jobs

    def test_subgraph_downstream_only(self, small_pipeline: Pipeline):
        jobs, edges = get_subgraph(small_pipeline, "Refine3D/job004/", upstream=False, downstream=True)
        assert "Subtract/job011/" in jobs
        assert "Import/job001/" not in jobs

    def test_subgraph_both_directions(self, small_pipeline: Pipeline):
        jobs, edges = get_subgraph(small_pipeline, "Refine3D/job004/", upstream=True, downstream=True)
        # Should include everything since job004 is central
        assert "Import/job001/" in jobs
        assert "Subtract/job011/" in jobs
        assert "Select/job007/" in jobs


# ── Mermaid rendering tests ──────────────────────────────────────────


class TestMermaid:
    def test_render_full(self, small_pipeline: Pipeline):
        jobs, edges = get_full_graph(small_pipeline)
        mmd = render_mermaid(jobs, edges, small_pipeline)
        assert mmd.startswith("graph TD")
        # All 11 jobs should be nodes
        for i in range(1, 12):
            assert f"job{i:03d}" in mmd

    def test_render_contains_edges(self, small_pipeline: Pipeline):
        jobs, edges = get_full_graph(small_pipeline)
        mmd = render_mermaid(jobs, edges, small_pipeline)
        assert "job001 --> job002" in mmd
        assert "job004 --> job006" in mmd

    def test_render_class_assignments(self, small_pipeline: Pipeline):
        jobs, edges = get_full_graph(small_pipeline)
        mmd = render_mermaid(jobs, edges, small_pipeline)
        assert "classDef import" in mmd
        assert "classDef refine3d" in mmd
        assert "classDef class3d" in mmd
        assert "class job001 import" in mmd
        assert "class job006 class3d" in mmd

    def test_render_status_classes(self, small_pipeline: Pipeline):
        jobs, edges = get_full_graph(small_pipeline)
        mmd = render_mermaid(jobs, edges, small_pipeline)
        assert "classDef failed" in mmd
        assert "classDef running" in mmd
        assert "class job006 failed" in mmd
        assert "class job011 running" in mmd

    def test_render_alias_in_label(self, small_pipeline: Pipeline):
        jobs, edges = get_full_graph(small_pipeline)
        mmd = render_mermaid(jobs, edges, small_pipeline)
        assert "j007_best_class" in mmd

    def test_render_subgraph(self, small_pipeline: Pipeline):
        jobs, edges = get_subgraph(small_pipeline, "Select/job007/", upstream=True)
        mmd = render_mermaid(jobs, edges, small_pipeline)
        assert "job007" in mmd
        assert "job001" in mmd
        # Subtract is in a different branch
        assert "job011" not in mmd

    def test_render_deterministic(self, small_pipeline: Pipeline):
        jobs, edges = get_full_graph(small_pipeline)
        mmd1 = render_mermaid(jobs, edges, small_pipeline)
        mmd2 = render_mermaid(jobs, edges, small_pipeline)
        assert mmd1 == mmd2


# ── CLI job name resolution tests ────────────────────────────────────


class TestResolveJobName:
    def test_bare_number(self, small_pipeline: Pipeline):
        assert _resolve_job_name("4", small_pipeline) == "Refine3D/job004/"

    def test_job_id(self, small_pipeline: Pipeline):
        assert _resolve_job_name("job004", small_pipeline) == "Refine3D/job004/"

    def test_full_name(self, small_pipeline: Pipeline):
        assert _resolve_job_name("Refine3D/job004/", small_pipeline) == "Refine3D/job004/"

    def test_not_found(self, small_pipeline: Pipeline):
        assert _resolve_job_name("999", small_pipeline) is None

    def test_two_digit_number(self, small_pipeline: Pipeline):
        assert _resolve_job_name("11", small_pipeline) == "Subtract/job011/"


# ── CLI integration tests ────────────────────────────────────────────


class TestCLI:
    def test_full_pipeline_output(self, tmp_path: Path):
        from relion_pipeline_visualizer.cli import main
        out = tmp_path / "test_pipeline"
        main([str(SMALL_STAR), "-o", str(out)])
        assert (tmp_path / "test_pipeline.mmd").exists()
        assert (tmp_path / "test_pipeline.html").exists()

    def test_subgraph_output(self, tmp_path: Path):
        from relion_pipeline_visualizer.cli import main
        out = tmp_path / "sub"
        main([str(SMALL_STAR), "--job", "7", "-o", str(out)])
        mmd = (tmp_path / "sub.mmd").read_text()
        assert "job007" in mmd
        assert "job001" in mmd

    def test_force_overwrite(self, tmp_path: Path):
        from relion_pipeline_visualizer.cli import main
        out = tmp_path / "ow"
        main([str(SMALL_STAR), "-o", str(out)])
        # Second run without --force should exit cleanly
        with pytest.raises(SystemExit) as exc_info:
            main([str(SMALL_STAR), "-o", str(out)])
        assert exc_info.value.code == 0

    def test_force_flag_allows_overwrite(self, tmp_path: Path):
        from relion_pipeline_visualizer.cli import main
        out = tmp_path / "ow2"
        main([str(SMALL_STAR), "-o", str(out)])
        # With --force, should succeed
        main([str(SMALL_STAR), "-o", str(out), "--force"])
        assert (tmp_path / "ow2.mmd").exists()

    def test_html_contains_mermaid(self, tmp_path: Path):
        from relion_pipeline_visualizer.cli import main
        out = tmp_path / "html_test"
        main([str(SMALL_STAR), "-o", str(out)])
        html = (tmp_path / "html_test.html").read_text()
        assert "mermaid" in html
        assert "graph TD" in html
        assert "jobInfo" in html

    def test_downstream_flag(self, tmp_path: Path):
        from relion_pipeline_visualizer.cli import main
        out = tmp_path / "down"
        main([str(SMALL_STAR), "--job", "4", "--downstream", "-o", str(out)])
        mmd = (tmp_path / "down.mmd").read_text()
        assert "job011" in mmd  # Subtract is downstream of Refine3D/job004
        assert "job001" not in mmd  # Import is upstream, not included
