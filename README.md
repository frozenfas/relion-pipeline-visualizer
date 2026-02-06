relion-pipeline-visualizer
==========================

Visualize RELION 5 cryo-EM processing pipelines as structured, readable diagrams.

This project parses RELION pipeline STAR files and converts them into graph
representations (e.g. Mermaid diagrams, SVGs) that make complex workflows
easier to understand, debug, and communicate.

The tool is intended for:
- RELION 5 users
- Cryo-EM pipeline inspection and documentation
- Academic and reproducible research workflows


Features (current / planned)
----------------------------

- Parse RELION 5 pipeline STAR files
- Extract job dependencies and data flow
- Generate Mermaid diagrams of pipelines
- Job-type–aware styling (import, classification, refinement, etc.)
- SVG output suitable for Chrome and documentation



Installation
------------

Installation uses a Conda environment defined by environment.yml.

1. Clone the repository

    git clone https://github.com/<your-username>/relion-pipeline-visualizer.git
    cd relion-pipeline-visualizer


2. Create the Conda environment

    conda env create -f environment.yml
    conda activate relion-pipeline-visualizer

If the environment file changes, update with:

    conda env update -f environment.yml --prune


3. Verify the environment

    python -c "import starfile; print('starfile import OK')"



Usage (early example)
---------------------

WARNING: The interface is under active development and may change.

    python -m relion_pipeline_visualizer \
        examples/pipeline.star \
        --format mermaid \
        --output pipeline.mmd

This produces a Mermaid (.mmd) file describing the RELION pipeline graph.


Rendering Mermaid diagrams
--------------------------

Convert to SVG using the Mermaid CLI:

    npm install -g @mermaid-js/mermaid-cli
    mmdc -i pipeline.mmd -o pipeline.svg

View in Chrome:

    google-chrome pipeline.svg

The generated SVG is suitable for zooming and embedding in documentation.


Project structure
-----------------

relion-pipeline-visualizer/
├── relion_pipeline_visualizer/
│   ├── cli.py
│   ├── parser/
│   │   └── relion4_star.py
│   ├── graph/
│   │   └── mermaid.py
│   └── validate.py
├── examples/
├── tests/
├── environment.yml
├── README.md
└── LICENSE


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
