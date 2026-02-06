relion-pipeline-visualizer
==========================

Visualize RELION 5 cryo-EM processing pipelines as structured, readable Mermaid diagrams.

This project parses RELION pipeline STAR files and converts them into
job-level directed acyclic graphs (DAGs), rendering color-coded Mermaid
flowcharts that make complex workflows easier to understand, debug, and
communicate.

The tool is intended for:
- RELION 5 users
- Cryo-EM pipeline inspection and documentation
- Academic and reproducible research workflows


Features
--------

- Parse RELION 5 `default_pipeline.star` files
- Derive job-to-job edges by joining through shared intermediate nodes
- Generate Mermaid `graph TD` flowcharts
- Job-type-aware color coding (Import, Extract, Refine3D, Class3D, Select, MaskCreate, PostProcess, CtfRefine, MultiBody, Subtract, JoinStar)
- Status-aware styling (Failed jobs get red borders, Running jobs get dashed orange borders)
- Full pipeline view or focused subgraph for a specific job
- Upstream (ancestors) and/or downstream (descendants) traversal
- HTML output with interactive hover tooltips showing job details
- Tooltips show last RELION command from `note.txt`
- Refine3D tooltips show resolution, Fourier completeness, class distribution, and accuracy
- Class3D tooltips show per-class statistics from the last iteration model file
- Outputs both `.mmd` (Mermaid source) and `.html` (self-contained browser view)
- Shorthand job selection: `--job 93`, `--job job093`, or `--job Refine3D/job093/`


Installation
------------

Installation uses a Conda environment defined by environment.yml.

1. Clone the repository

```bash
git clone https://github.com/frozenfas/relion-pipeline-visualizer.git
cd relion-pipeline-visualizer
```

2. Create the Conda environment (this also installs the package)

```bash
conda env create -f environment.yml
conda activate relion-pipeline-visualizer
```

If the environment file changes, update with:

```bash
conda env update -f environment.yml --prune
```

3. Verify the installation

```bash
relion_pipeline_visualizer --help
```


Usage
-----

After activating the conda environment, the `relion_pipeline_visualizer` command is available from any directory.

### Full pipeline diagram

```bash
relion_pipeline_visualizer path/to/default_pipeline.star
```

This writes `pipeline.mmd` and `pipeline.html` to the same directory as the STAR file. Open the HTML file in a browser for an interactive diagram with hover tooltips.

### Focused subgraph for a specific job

The `--job` flag accepts shorthand notation -- you can use just the number, the job ID, or the full path:

```bash
# All equivalent:
relion_pipeline_visualizer path/to/default_pipeline.star --job 58
relion_pipeline_visualizer path/to/default_pipeline.star --job job058
relion_pipeline_visualizer path/to/default_pipeline.star --job "Refine3D/job058/"
```

Show upstream ancestors ("how did I get here?" -- default):

```bash
relion_pipeline_visualizer path/to/default_pipeline.star --job 58
```

Show downstream descendants ("what depends on this?"):

```bash
relion_pipeline_visualizer path/to/default_pipeline.star --job 53 --downstream
```

Show both directions:

```bash
relion_pipeline_visualizer path/to/default_pipeline.star --job 40 --upstream --downstream
```

### Custom output path

```bash
relion_pipeline_visualizer path/to/default_pipeline.star \
    -o /some/other/dir/my_pipeline
```

### Open in mermaid.live

Add `--live` to open the diagram in your browser on https://mermaid.live for interactive editing:

```bash
relion_pipeline_visualizer path/to/default_pipeline.star --live
relion_pipeline_visualizer path/to/default_pipeline.star --job 93 --live
```

### CLI options

```
positional arguments:
  star_file             Path to default_pipeline.star

options:
  --job JOB_NAME        Focus on a specific job (e.g. '58', 'job058', or 'Refine3D/job058/')
  --upstream            Include upstream ancestors (default when --job is given)
  --downstream          Include downstream descendants
  -o, --output NAME     Base name for output files (default: pipeline next to star_file)
  --live                Open the diagram in mermaid.live in your browser
```


Viewing diagrams
----------------

**HTML (recommended):** Open the generated `pipeline.html` in any browser. Nodes are color-coded by job type. Hovering over a node shows a tooltip with:

- Job name, alias, type, and status
- Last RELION command executed (from `note.txt`)
- For Refine3D jobs: resolution, Fourier completeness, class distribution, and rotational/translational accuracy (from `run_model.star`)
- For Class3D jobs: per-class statistics from the last iteration model file

**Mermaid source:** Paste the contents of the `.mmd` file into https://mermaid.live to visualize or edit interactively.


Project structure
-----------------

```
relion-pipeline-visualizer/
├── src/
│   └── relion_pipeline_visualizer/
│       ├── __init__.py
│       ├── __main__.py        # Entry point for python -m
│       ├── cli.py             # CLI argument parsing
│       ├── parser.py          # STAR file parsing, job enrichment (note.txt, model stats)
│       ├── graph.py           # DAG operations (ancestors, descendants)
│       └── mermaid.py         # Mermaid diagram rendering
├── tests/
│   └── data/
│       └── default_pipeline.star
├── pyproject.toml
├── environment.yml
├── README.md
└── LICENSE
```


RELION compatibility
--------------------

- Supported: RELION 4 and 5


License
-------

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

You are free to use, modify, and redistribute this software under the terms of
the GPL-3.0. Any redistributed or modified versions must also be licensed
under GPL-3.0.

See the LICENSE file for full details.


Status
------

This project is under active development.
APIs, command-line options, and output formats should be considered unstable
until a first tagged release.

Contributions, issues, and test STAR files are welcome.
