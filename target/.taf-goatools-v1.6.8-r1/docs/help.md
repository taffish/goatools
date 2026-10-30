goatools 1.6.8-r1

Purpose:
  Gene Ontology enrichment, GO slim mapping, ontology traversal and plotting.

Usage:
  taf-goatools -- --help
  taf-goatools -- --version
  taf-goatools goatools help find_enrichment
  taf-goatools python analysis.py
  Use "goatools subcommand"; a bare subcommand may be treated as an executable.

Prepare resources (explicit setup; analysis can stay offline):
  Ontologies and annotations are not bundled. Select only the members needed.
  Catalog IDs: go-2026-08-05-basic, go-2026-08-05-slim-generic,
  go-2026-08-05-yeast-gaf. Other fixed snapshots: --recipe recipe.json (README).
  mkdir -p "$HOME/.local/share/taffish/databases"
  cd "$HOME/.local/share/taffish/databases"
  export TAFFISH_GOATOOLS_DB_AUTO_MOUNT=0
  taf-goatools goatools-resources --db-root goatools --resource go-2026-08-05-basic --dry-run
  taf-goatools goatools-resources --db-root goatools --resource go-2026-08-05-basic --allow-network
  taf-goatools goatools-resources --db-root goatools --resource go-2026-08-05-slim-generic --allow-network
  taf-goatools goatools-resources --db-root goatools --verify
  unset TAFFISH_GOATOOLS_DB_AUTO_MOUNT
  Complete members are reused. Retry interrupted installs with the same command.
  Downloads require --allow-network; --archive-dir DIR installs verified files offline.
  For GAF input, decompress the original archive into your writable project first:
  taf-goatools gzip -cd /go-resources/go-2026-08-05-yeast-gaf/YEAST-mod.gaf.gz > yeast.gaf
  --force resets bad download caches only; it never replaces an installed member.
  To repair an invalid installed member, prepare a new root and select it explicitly.
  After interruption, verify first; inspect changed paths, incomplete members or unknown staging before retrying.

Shared resource paths:
  Search order: TAFFISH_GOATOOLS_DB_PATH, personal path above,
  /usr/local/share/taffish/databases/goatools, /opt/taffish/databases/goatools.
  The first existing root must validate; no fallback across broken/partial roots.
  Verified roots (including valid root symlinks) mount read-only at /go-resources.
  Automatic validation needs host Python 3 (standard library only).
  Each versioned member is independent; missing members are not auto-downloaded.
  export TAFFISH_GOATOOLS_DB_PATH="/absolute/prepared root"
  Set TAFFISH_GOATOOLS_DB_AUTO_MOUNT=0 to disable discovery for setup/manual paths.
  An administrator can install once in either system path; users only need read access.

Backend-specific use (same analysis syntax on all three):
  Docker:    TAFFISH_CONTAINER_BACKEND=docker taf-goatools goatools help find_enrichment
  Podman:    TAFFISH_CONTAINER_BACKEND=podman taf-goatools goatools help find_enrichment
  Apptainer: TAFFISH_CONTAINER_BACKEND=apptainer taf-goatools goatools help find_enrichment
  Manual bind /srv/go to /go-resources (disable discovery first):
  export TAFFISH_GOATOOLS_DB_AUTO_MOUNT=0
  Docker:    export TAFFISH_DOCKER_RUN_ARGS="-v /srv/go:/go-resources:ro"
  Podman:    export TAFFISH_PODMAN_RUN_ARGS="-v /srv/go:/go-resources:ro"
  Apptainer: export TAFFISH_APPTAINER_RUN_ARGS="--bind /srv/go:/go-resources:ro"
  Verify a manually mapped root before analysis:
  taf-goatools goatools-resources --db-root /go-resources --verify
  For installation use a writable parent bind and an explicit --db-root below it.
  Native images: linux/amd64 and linux/arm64. Apptainer requires a compatible Linux host.

Enrichment:
  Inputs: study.txt and population.txt contain one matching identifier per line;
  association.txt contains "identifier GO:0000001;GO:0000002" (id2gos).
  taf-goatools goatools find_enrichment study.txt population.txt association.txt --annofmt=id2gos --obo=/go-resources/go-2026-08-05-basic/go-basic.obo --outfile=goea.tsv
  Choose .xlsx for spreadsheet output. GAF, GPAD 1.1/2.0 and gene2go are also supported.
  Add --algorithm=elim for topology-aware scoring; classic is the default.
  --method selects multiple-testing correction, not the scoring algorithm.
  Consult upstream help before changing --alternative or elim correction settings.

GO slim and graphics:
  taf-goatools goatools map_to_slim /go-resources/go-2026-08-05-basic/go-basic.obo /go-resources/go-2026-08-05-slim-generic/goslim_generic.obo --term=GO:0008135
  taf-goatools goatools plot_go_term /go-resources/go-2026-08-05-basic/go-basic.obo --term=GO:0008135 --engine=pygraphviz --output=lineage.svg
  pydot is also included. Add --gml to export a graph for a separate Cytoscape installation.
  Outputs: GOEA TSV/XLSX, mappings, hierarchy text, SVG/PNG and optional GML.

Immediate notes:
  Missing local resources fail explicitly; analysis never downloads them implicitly.
  Prepare them with the helper above, then pass the exact local file path.
  GOlr fetch_associations is an explicit online query, not a fixed shared database.
  Keep literal inner quotes for command arguments containing spaces:
  taf-goatools goatools find_enrichment '"study set.txt"' population.txt association.txt --annofmt=id2gos --obo=go.obo --outfile='"result table.tsv"'
  Shared root environment variables use ordinary shell quotes, without inner quotes.

More help:
  taf-goatools goatools-resources --help
  taf-goatools goatools help plot_go_term
  https://github.com/taffish/goatools
  https://github.com/tanghaibao/goatools/tree/v1.6.8

Wrapper options:
  taf-goatools --help       Show this task help.
  taf-goatools --version    Show wrapper identity.
  taf-goatools --compile    Print generated shell.
