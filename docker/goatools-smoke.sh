#!/bin/sh
set -eu

mode="${1:-all}"
tmp=""
cleanup() { test -z "$tmp" || rm -rf "$tmp"; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

make_fixture() {
  fixture_dir="$1"
  test -d "${fixture_dir}"

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
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/taf-goatools-identity.XXXXXX")"

  goatools --version 2>&1 | grep -Fx '1.6.6' >/dev/null
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
    if goatools help "${subcommand}" > "${tmp}/${subcommand}.help" 2>&1; then :; else
      status=$?
      printf >&2 'GOATOOLS_SMOKE_FAIL help %s exit=%s\n' "$subcommand" "$status"
      tail -60 "${tmp}/${subcommand}.help" >&2
      exit "$status"
    fi
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

assert goatools.__version__ == "1.6.6"
assert md.version("goatools") == "1.6.6"
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
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/taf-goatools-goea.XXXXXX")"
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
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/taf-goatools-spreadsheet.XXXXXX")"
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
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/taf-goatools-slim.XXXXXX")"
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
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/taf-goatools-graphics.XXXXXX")"
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

run_algorithms() {
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/taf-goatools-algorithms.XXXXXX")"
  make_fixture "$tmp"
  goatools find_enrichment "$tmp/study.txt" "$tmp/population.txt" "$tmp/association.txt" \
    --annofmt=id2gos --obo="$tmp/go.obo" --algorithm=elim --pval=1 --outfile="$tmp/elim.tsv"
  grep -F 'GO:0000001' "$tmp/elim.tsv" >/dev/null
  python - "$tmp/go.obo" <<'PY'
import random
import sys
from goatools.obo_parser import GODag
from goatools.go_enrichment import GOEnrichmentStudy
dag = GODag(sys.argv[1])
population = list(range(20))
assoc = {i: {"GO:0000001" if i < 4 else "GO:0000002"} for i in population}
study = list(range(4))
for alg, alternative in (("classic", "two-sided"), ("elim", "greater")):
    random.seed(17)
    goea = GOEnrichmentStudy(population, assoc, dag, algorithm=alg,
                            alternative=alternative, methods=["fdr_bh"])
    results = goea.run_study(study)
    by_id = {r.GO: r for r in results}
    assert 0 < by_id["GO:0000001"].p_uncorrected < 0.01
    assert all(0 <= r.p_uncorrected <= 1 for r in results)
    assert "GO:0008150" in by_id
    assert len(goea.run_study(study)) == len(results)
print("ALGORITHM_CLASSIC_ELIM_PASS")
PY
}

printf 'GOATOOLS_SMOKE_STAGE %s\n' "$mode"
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
  algorithms)
    run_algorithms
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
    run_algorithms
    ;;
  *)
    echo "unknown smoke mode: ${mode}" >&2
    exit 2
    ;;
esac
printf 'GOATOOLS_SMOKE_PASS %s\n' "$mode"
