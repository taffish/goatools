taf-goatools 1.6.5-r1

GOATOOLS command-line and Python runtime for Gene Ontology enrichment,
ontology DAG analysis, GO slim mapping, annotation parsing, and plotting.

Usage:
  taf-goatools --help              Show this TAFFISH help
  taf-goatools --version           Show TAFFISH package version
  taf-goatools -- --help           Show upstream goatools help
  taf-goatools -- --version        Show upstream GOATOOLS version
  taf-goatools goatools COMMAND [ARGS...]
  taf-goatools COMMAND [ARGS...]

Command mode:
  Prefer an explicit goatools dispatcher for upstream subcommands so TAFFISH
  does not interpret the subcommand name as another container executable:
  taf-goatools goatools help find_enrichment
  taf-goatools goatools find_enrichment --help

Included command groups:
  compare_gos, find_enrichment, map_to_slim, prt_terms
  go_plot, plot_go_term, wr_hier, wr_sections
  fetch_associations, ncbi_gene_results_to_python
  find_enrichment.py, go_plot.py, map_to_slim.py, wr_hier.py,
  plot_go_term.py, ncbi_gene_results_to_python.py

Prepare ontology data:
  mkdir -p goatools-data
  taf-goatools curl -fL \
    https://current.geneontology.org/ontology/go-basic.obo \
    -o goatools-data/go-basic.obo
  taf-goatools curl -fL \
    https://current.geneontology.org/ontology/subsets/goslim_generic.obo \
    -o goatools-data/goslim_generic.obo

Prepare common annotation data:
  taf-goatools curl -fL \
    https://current.geneontology.org/annotations/goa_human.gaf.gz \
    -o goatools-data/goa_human.gaf.gz
  taf-goatools curl -fL \
    https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2go.gz \
    -o goatools-data/gene2go.gz

Record mutable data snapshots:
  taf-goatools sha256sum goatools-data/go-basic.obo \
    goatools-data/goslim_generic.obo goatools-data/goa_human.gaf.gz \
    goatools-data/gene2go.gz > goatools-data/SHA256SUMS
  Also record retrieval dates and source URLs because current-release
  endpoints can change independently of this app version.

GO enrichment:
  taf-goatools goatools find_enrichment \
    study.txt population.txt association.txt \
    --annofmt=id2gos \
    --obo=goatools-data/go-basic.obo \
    --outfile=goea.tsv
  Study and population files contain one identifier per line. id2gos uses an
  identifier followed by semicolon-separated GO IDs. GAF, GPAD, and NCBI
  gene2go are also supported. Use an .xlsx suffix for spreadsheet output.

GO slim mapping:
  taf-goatools goatools map_to_slim \
    goatools-data/go-basic.obo goatools-data/goslim_generic.obo \
    --term=GO:0008135
  Use --association_file=association.txt to map a complete association file.

Lineage plotting:
  taf-goatools goatools plot_go_term \
    goatools-data/go-basic.obo --term=GO:0008135 \
    --engine=pygraphviz --gml --output=GO_0008135.svg
  --gml also writes GO_0008135.gml for Cytoscape. NetworkX, pygraphviz, and
  pydot are installed; a recorded patch restores the advertised pydot path.

Python API:
  taf-goatools python analysis.py
  The complete GOATOOLS package and upstream goatools.test_data are retained.

Online association query:
  taf-goatools goatools fetch_associations --taxon_id=9606 \
    -o human.id2gos.txt
  pysolr is included for this official command. GOlr contents and network
  availability are external; prefer versioned local annotations for workflows.

Platform and data boundary:
  Native images: linux/amd64 and linux/arm64.
  No ontology, GO slim, GAF, GPAD, gene2go, or study dataset is embedded.
  There is no fixed database path; pass normal local paths on each command.
  Explicit local --obo files avoid GOATOOLS implicit-download data drift.

Scientific boundary:
  The app does not choose the background population, identifier mapping,
  annotation release, evidence-code policy, ontology relationships, or
  multiple-testing method. Validate these choices for the study design.

Detailed documentation:
  https://github.com/taffish/goatools
  https://github.com/tanghaibao/goatools/tree/v1.6.5
  https://geneontology.org/docs/download-ontology/
  https://geneontology.org/docs/download-go-annotations/
