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

### Focused subgraph for a specific job

Show upstream ancestors ("how did I get here?"):

```bash
relion_pipeline_visualizer path/to/default_pipeline.star \
    --job "Refine3D/job058/"
```

Show downstream descendants ("what depends on this?"):

```bash
relion_pipeline_visualizer path/to/default_pipeline.star \
    --job "Refine3D/job053/" --downstream
```

Show both directions:

```bash
relion_pipeline_visualizer path/to/default_pipeline.star \
    --job "Refine3D/job040/" --upstream --downstream
```

### Write to file

```bash
relion_pipeline_visualizer path/to/default_pipeline.star \
    -o pipeline.mmd
```

### CLI options

```
positional arguments:
  star_file             Path to default_pipeline.star

options:
  --job JOB_NAME        Focus on a specific job (e.g. 'Refine3D/job058/')
  --upstream            Include upstream ancestors (default when --job is given)
  --downstream          Include downstream descendants
  -o, --output FILE     Write output to file instead of stdout
```


Rendering Mermaid diagrams
--------------------------

Paste the output into https://mermaid.live to visualize interactively.

Or convert to SVG using the Mermaid CLI:

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i pipeline.mmd -o pipeline.svg
```


Project structure
-----------------

```
relion-pipeline-visualizer/
├── src/
│   └── relion_pipeline_visualizer/
│       ├── __init__.py
│       ├── __main__.py        # Entry point for python -m
│       ├── cli.py             # CLI argument parsing
│       ├── parser.py          # STAR file parsing → Pipeline dataclass
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
