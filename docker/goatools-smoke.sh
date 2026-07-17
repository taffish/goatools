#!/bin/sh
set -eu

mode="${1:-all}"

make_fixture() {
  fixture_dir="$1"
  rm -rf "${fixture_dir}"
  mkdir -p "${fixture_dir}"

  cat > "${fixture_dir}/go.obo" <<'EOF'
format-version: 1.2
data-version: taf-smoke

[Term]
id: GO:0008150
name: biological_process
namespace: biological_process

[Term]
id: GO:0000001
name: alpha process
namespace: biological_process
is_a: GO:0008150 ! biological_process

[Term]
id: GO:0000002
name: beta process
namespace: biological_process
is_a: GO:0008150 ! biological_process
EOF

  cat > "${fixture_dir}/slim.obo" <<'EOF'
format-version: 1.2
data-version: taf-smoke

[Term]
id: GO:0008150
name: biological_process
namespace: biological_process
EOF

  printf 'gene1\ngene2\n' > "${fixture_dir}/study.txt"
  printf 'gene1\ngene2\ngene3\ngene4\n' > "${fixture_dir}/population.txt"
  printf '%s\n' \
    'gene1 GO:0000001' \
    'gene2 GO:0000001' \
    'gene3 GO:0000002' \
    'gene4 GO:0000002' \
    > "${fixture_dir}/association.txt"
}

run_identity() {
  tmp="/tmp/taf-goatools-identity-$$"
  rm -rf "${tmp}"
  mkdir -p "${tmp}"

  goatools --version 2>&1 | grep -Fx '1.6.5' >/dev/null
  goatools --help 2>&1 | grep -F 'Run GO enrichment analysis.' >/dev/null
  goatools --help 2>&1 | grep -F 'fetch_associations' >/dev/null

  for subcommand in \
    compare_gos \
    fetch_associations \
    find_enrichment \
    go_plot \
    map_to_slim \
    ncbi_gene_results_to_python \
    plot_go_term \
    prt_terms \
    wr_hier \
    wr_sections; do \
    goatools help "${subcommand}" > "${tmp}/${subcommand}.help" 2>&1
    test -s "${tmp}/${subcommand}.help"
  done

  find_enrichment.py --help 2>&1 | grep -F 'functional enrichment' >/dev/null
  go_plot.py --help 2>&1 | grep -F 'goatools go_plot' >/dev/null
  map_to_slim.py --help 2>&1 | grep -F 'Map GO terms' >/dev/null
  wr_hier.py --help 2>&1 | grep -F 'hierarchy' >/dev/null
  plot_go_term.py --help 2>&1 | grep -F 'lineage' >/dev/null
  ncbi_gene_results_to_python.py --help 2>&1 \
    | grep -F 'NCBI Gene' >/dev/null

  python <<'PY'
import importlib.metadata as md

import ftpretty
import goatools
import goatools.anno
import goatools.godag
import goatools.goea
import goatools.gosubdag
import goatools.obo_parser
import goatools.semantic
import networkx
import numpy
import openpyxl
import pandas
import pydot
import pygraphviz
import pysolr
import requests
import rich
import scipy
import statsmodels
import xlsxwriter
from goatools.base import nopen

assert goatools.__version__ == "1.6.5"
assert md.version("goatools") == "1.6.5"
assert md.version("networkx") == "3.6.1"
assert md.version("pysolr") == "3.11.0"
assert md.version("pygraphviz") == "2.0"
proc = nopen("|printf 'goatools-shell\\n'")
assert proc.stdout.read().strip() == "goatools-shell"
assert proc.wait() == 0
PY

  rm -rf "${tmp}"
}

run_goea() {
  tmp="/tmp/taf-goatools-goea-$$"
  make_fixture "${tmp}"

  goatools find_enrichment \
    "${tmp}/study.txt" \
    "${tmp}/population.txt" \
    "${tmp}/association.txt" \
    --annofmt=id2gos \
    --obo="${tmp}/go.obo" \
    --pval=1 \
    --outfile="${tmp}/enrichment.tsv"
  test -s "${tmp}/enrichment.tsv"
  grep -F 'GO:0000001' "${tmp}/enrichment.tsv" >/dev/null
  grep -F 'p_uncorrected' "${tmp}/enrichment.tsv" >/dev/null

  rm -rf "${tmp}"
}

run_spreadsheet() {
  tmp="/tmp/taf-goatools-spreadsheet-$$"
  make_fixture "${tmp}"

  goatools find_enrichment \
    "${tmp}/study.txt" \
    "${tmp}/population.txt" \
    "${tmp}/association.txt" \
    --annofmt=id2gos \
    --obo="${tmp}/go.obo" \
    --pval=1 \
    --outfile="${tmp}/enrichment.xlsx"
  test -s "${tmp}/enrichment.xlsx"
  python - "${tmp}/enrichment.xlsx" <<'PY'
import sys
from openpyxl import load_workbook

book = load_workbook(sys.argv[1], read_only=True)
assert book.sheetnames
sheet = book[book.sheetnames[0]]
assert sheet.max_row >= 2
assert sheet.max_column >= 5
PY

  rm -rf "${tmp}"
}

run_slim() {
  tmp="/tmp/taf-goatools-slim-$$"
  make_fixture "${tmp}"

  goatools map_to_slim \
    "${tmp}/go.obo" \
    "${tmp}/slim.obo" \
    --term=GO:0000001 \
    > "${tmp}/mapping.txt"
  grep -F 'GO:0008150' "${tmp}/mapping.txt" >/dev/null

  rm -rf "${tmp}"
}

run_graphics() {
  tmp="/tmp/taf-goatools-graphics-$$"
  make_fixture "${tmp}"

  goatools plot_go_term \
    "${tmp}/go.obo" \
    --term=GO:0000001 \
    --engine=pydot \
    --gml \
    --output="${tmp}/pydot.svg"
  test -s "${tmp}/pydot.svg"
  grep -F '<svg' "${tmp}/pydot.svg" >/dev/null
  test -s "${tmp}/pydot.gml"
  grep -F 'graph [' "${tmp}/pydot.gml" >/dev/null

  goatools plot_go_term \
    "${tmp}/go.obo" \
    --term=GO:0000001 \
    --engine=pygraphviz \
    --gml \
    --output="${tmp}/pygraphviz.svg"
  test -s "${tmp}/pygraphviz.svg"
  grep -F '<svg' "${tmp}/pygraphviz.svg" >/dev/null
  test -s "${tmp}/pygraphviz.gml"
  grep -F 'graph [' "${tmp}/pygraphviz.gml" >/dev/null

  rm -rf "${tmp}"
}

case "${mode}" in
  identity)
    run_identity
    ;;
  goea)
    run_goea
    ;;
  spreadsheet)
    run_spreadsheet
    ;;
  slim)
    run_slim
    ;;
  graphics)
    run_graphics
    ;;
  buildtime)
    run_identity
    run_goea
    ;;
  all)
    run_identity
    run_goea
    run_spreadsheet
    run_slim
    run_graphics
    ;;
  *)
    echo "unknown smoke mode: ${mode}" >&2
    exit 2
    ;;
esac
