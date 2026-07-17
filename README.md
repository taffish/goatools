# goatools

`goatools` packages GOATOOLS for TAFFISH.

Package identity:

- name: `goatools`
- command: `taf-goatools`
- kind: `tool`
- version: `1.6.5-r1`
- TAFFISH app license: Apache-2.0
- upstream: <https://github.com/tanghaibao/goatools>

## What This App Packages

This app provides the official GOATOOLS 1.6.5 command-line dispatcher and
Python package, its declared Python dependencies, both supported Graphviz
bindings, and small Unix utilities needed for local data acquisition and
compressed inputs.

The default command is `goatools`. TAFFISH automatic command mode also exposes
the packaged Python interpreter, standalone upstream entry points, `curl`,
`gzip`, and Graphviz commands from the same container.

## Scope

This app supports:

- Gene Ontology enrichment analysis with Fisher's exact test and multiple-test
  corrections
- OBO DAG parsing, traversal, hierarchy and section reports, GO-list
  comparison, and semantic-analysis APIs
- GAF, GPAD, NCBI `gene2go`, and simple `id2gos` association readers
- GO term and association mapping to GO slim subsets
- GO hierarchy and lineage rendering through Graphviz with `pygraphviz` or
  `pydot`, with optional GML export for Cytoscape
- TSV and XLSX result writing
- the importable GOATOOLS Python API and upstream packaged example/test data
- online GOlr association retrieval through the upstream
  `fetch_associations` command

This app does not bundle a dated copy of the Gene Ontology, GO slim subsets,
organism annotations, NCBI `gene2go`, a GOlr/Solr server, or study-specific
gene identifiers. These resources change independently of GOATOOLS and must be
provided explicitly.

## Container Contents

- `goatools`: upstream dispatcher with ten subcommands
- `find_enrichment.py`, `go_plot.py`, `map_to_slim.py`, `wr_hier.py`,
  `plot_go_term.py`, `ncbi_gene_results_to_python.py`: upstream standalone
  entry points
- `python`: Python 3.12 with the GOATOOLS library and declared dependencies
- `dot`, `pygraphviz`, `pydot`: headless Graphviz rendering runtime
- `pysolr`: explicit optional dependency required by the advertised
  `fetch_associations` subcommand
- `networkx`: explicit optional dependency required by `plot_go_term --gml`
- `curl`, `gzip`: utilities for obtaining and unpacking mutable external data

Resolved Python and Debian package inventories, upstream source archives,
licenses, source checksums, and the compatibility patch are retained under
`/opt/goatools/share/` in the image.

## Usage

Wrapper help and identity:

```sh
taf-goatools --help
taf-goatools --version
```

Upstream help and identity:

```sh
taf-goatools -- --help
taf-goatools -- --version
taf-goatools goatools help find_enrichment
```

GOATOOLS has upstream subcommands. With TAFFISH command mode, use the explicit
dispatcher form so the subcommand is not mistaken for another executable:

```sh
taf-goatools goatools find_enrichment --help
taf-goatools goatools map_to_slim --help
taf-goatools goatools plot_go_term --help
```

The equivalent upstream standalone entry points remain available:

```sh
taf-goatools find_enrichment.py --help
taf-goatools map_to_slim.py --help
taf-goatools plot_go_term.py --help
```

## Prepare Ontology and Annotation Data

Create a project-local data directory and download only the resources needed
by the analysis. The following commands run the packaged `curl` executable and
write into the current mounted working directory:

```sh
mkdir -p goatools-data

taf-goatools curl -fL \
  https://current.geneontology.org/ontology/go-basic.obo \
  -o goatools-data/go-basic.obo

taf-goatools curl -fL \
  https://current.geneontology.org/ontology/subsets/goslim_generic.obo \
  -o goatools-data/goslim_generic.obo
```

Two common annotation sources are GOA GAF and NCBI `gene2go`:

```sh
taf-goatools curl -fL \
  https://current.geneontology.org/annotations/goa_human.gaf.gz \
  -o goatools-data/goa_human.gaf.gz

taf-goatools curl -fL \
  https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz \
  -o goatools-data/gene2go.gz
```

These URLs are mutable current-release endpoints. For reproducible work,
record the retrieval date and checksums and retain the exact files with the
analysis:

```sh
taf-goatools sha256sum goatools-data/go-basic.obo \
  goatools-data/goslim_generic.obo \
  goatools-data/goa_human.gaf.gz \
  goatools-data/gene2go.gz \
  > goatools-data/SHA256SUMS
```

GOATOOLS can download some missing default resources itself, but an implicit
download is network-dependent and can silently select a newer ontology.
Production workflows should pass explicit local paths instead.

## Enrichment Analysis

Prepare:

- `study.txt`: one study gene or protein identifier per line
- `population.txt`: one background identifier per line
- `association.txt`: one identifier and one or more semicolon-separated GO IDs
  per line for `id2gos`, or a supported GAF/GPAD/gene2go file

Run an enrichment analysis and write TSV output:

```sh
taf-goatools goatools find_enrichment \
  study.txt population.txt association.txt \
  --annofmt=id2gos \
  --obo=goatools-data/go-basic.obo \
  --outfile=goea.tsv
```

Use an `.xlsx` suffix for spreadsheet output:

```sh
taf-goatools goatools find_enrichment \
  study.txt population.txt association.txt \
  --annofmt=id2gos \
  --obo=goatools-data/go-basic.obo \
  --outfile=goea.xlsx
```

Identifier namespaces must match between the study, population, and
association files. GOATOOLS does not infer or convert Ensembl, Entrez, UniProt,
or project-specific identifiers automatically.

## GO Slim and Visualization

Map one term to the generic GO slim:

```sh
taf-goatools goatools map_to_slim \
  goatools-data/go-basic.obo \
  goatools-data/goslim_generic.obo \
  --term=GO:0008135
```

Map an association file:

```sh
taf-goatools goatools map_to_slim \
  goatools-data/go-basic.obo \
  goatools-data/goslim_generic.obo \
  --association_file=association.txt \
  > association.goslim.txt
```

Render a GO lineage as SVG:

```sh
taf-goatools goatools plot_go_term \
  goatools-data/go-basic.obo \
  --term=GO:0008135 \
  --engine=pygraphviz \
  --output=GO_0008135.svg
```

Add `--gml` to write `GO_0008135.gml` beside the graphic for import into
Cytoscape. NetworkX and its pydot/pygraphviz conversion adapters are included.

Both advertised engines are installed. GOATOOLS 1.6.5 omits the
`wrap_width` argument in its `pydot` call path; this image applies a one-line,
checksum-recorded compatibility patch so `--engine=pydot` works as documented.

## Python API

Run a local script with the packaged API:

```sh
taf-goatools python analysis.py
```

Minimal example:

```python
from goatools.obo_parser import GODag

godag = GODag("goatools-data/go-basic.obo")
term = godag["GO:0008150"]
print(term.id, term.name)
```

The complete upstream `goatools.test_data` package is retained because it is
importable and is referenced by upstream examples. General test directories
from dependency packages, pip, wheel, caches, static archives, and bytecode are
removed from the final runtime.

## Online Association Retrieval

The official dispatcher advertises `fetch_associations`, but upstream does not
declare its `pysolr` dependency. This image installs `pysolr` so the command is
available:

```sh
taf-goatools goatools fetch_associations \
  --taxon_id=9606 \
  -o human.id2gos.txt
```

This command requires network access to a GOlr endpoint. Endpoint availability,
server contents, row limits, and live results are outside the offline image
contract. Prefer a versioned local GAF or gene2go snapshot for reproducible
pipelines.

## Resources, Databases, and Platform

Native images are built for `linux/amd64` and `linux/arm64`. All compiled
Python wheels used by the app are selected per architecture, and both platform
builds use the same command and data contract.

Memory use depends mainly on ontology size, annotation count, population size,
and the selected enrichment/reporting path. Large annotation sets and XLSX
reports may require substantially more memory than the tiny smoke fixtures.

There is no fixed database mount path. GOATOOLS accepts normal file paths, so
project-local or site-managed data can be mounted by TAFFISH with the working
directory and referenced directly on the command line.

## Boundaries

- Network-backed downloads and GOlr queries are supported but are not part of
  offline smoke or scientific reproducibility guarantees.
- The image does not validate whether a chosen background population,
  annotation release, evidence-code policy, ontology relationship set, or
  multiple-testing method is scientifically appropriate.
- GO term obsolescence and annotation changes follow the exact external data
  snapshot supplied by the user.
- Build tools and Python/C development headers are not provided in the final
  runtime; this is an analysis environment, not an extension-development SDK.

## Troubleshooting

- If `taf-goatools find_enrichment ...` is interpreted as a container command,
  use `taf-goatools goatools find_enrichment ...` or the packaged
  `find_enrichment.py` entry point.
- If an ontology is downloaded unexpectedly, pass `--obo` with an existing
  local file and retain that file with the analysis.
- If no study identifiers are associated, verify that the identifier namespace
  and species match the annotation file.
- If a live GOlr request fails, retry only after checking the endpoint and use a
  local annotation snapshot when reproducibility matters.

## Testing

The independent offline smoke commands cover:

- exact GOATOOLS, `pysolr`, NetworkX, and `pygraphviz` identities plus all
  advertised subcommand help paths
- Python imports, packaged entry points, and shell-backed `nopen`
- real tiny GO enrichment to TSV
- independent XLSX enrichment output and workbook parsing
- GO slim term mapping
- SVG and Cytoscape GML lineage rendering with both `pydot` and `pygraphviz`
- dynamic-library closure for Python extension modules

The smoke suite verifies packaging and integration. It does not replace
scientific validation on production ontologies and study data.

## License and Citation

TAFFISH app packaging is Apache-2.0. GOATOOLS remains BSD-2-Clause; its license
and exact source archive are retained in the image. Explicitly added `pysolr`,
NetworkX, `pygraphviz`, and Graphviz components retain their upstream licenses.

Cite GOATOOLS as:

Klopfenstein DV, Zhang L, Pedersen BS, et al. GOATOOLS: A Python library for
Gene Ontology analyses. Scientific Reports. 2018;8:10872.
<https://doi.org/10.1038/s41598-018-28948-z>

Upstream documentation:

- <https://github.com/tanghaibao/goatools/tree/v1.6.5>
- <https://github.com/tanghaibao/goatools/blob/v1.6.5/README.md>
- <https://geneontology.org/docs/download-ontology/>
- <https://geneontology.org/docs/download-go-annotations/>
