# goatools

`goatools` packages GOATOOLS for TAFFISH.

Package identity:

- name: `goatools`; command: `taf-goatools`; kind: `tool`
- version: `1.6.8-r1`; TAFFISH packaging license: Apache-2.0
- upstream: [GOATOOLS v1.6.8](https://github.com/tanghaibao/goatools/tree/v1.6.8)
- upstream commit: `2711506289bd47d50feb07a11add729d9bc6e684`; upstream license: BSD-2-Clause
- native platforms: `linux/amd64`, `linux/arm64`

## What This App Packages

The official PyPI wheel, Python 3.12 and declared dependencies, the GOATOOLS
dispatcher and standalone commands, Graphviz, pydot, pygraphviz, NetworkX
(for GML export), pysolr (for the advertised GOlr command), curl and gzip.
The Python API and upstream `goatools.test_data` remain available.

Version 1.6.8 adds GPAD 2.0 reading alongside 1.1, preserves the first annotation
after a GPAD header, and fixes NCBI chromosome-column parsing and Python module
section lookup. GPAD 2.0's multiple taxa are represented as a list and repeated
properties as lists of values. Previously omitted first rows are now included,
so GPAD-derived results can change. These are upstream fixes, not TAFFISH changes.
The 1.6.7 MICA semantic-similarity correction and classic/elim GOEA remain available.
No enrichment algorithm is patched by TAFFISH. The existing one-line
1.6.5-origin patch passing `wrap_width` to pydot remains necessary in 1.6.8;
its source, checksum and scope are retained under `/opt/goatools/share/patches`.

## Scope and Interfaces

Supported: enrichment, GO DAG traversal/semantic Python APIs, GO-list comparison,
GO slim mapping, GAF/GPAD/gene2go/id2gos input, hierarchy text, TSV/XLSX,
SVG/PNG and optional GML. Upstream commands include `compare_gos`,
`fetch_associations`, `find_enrichment`, `go_plot`, `map_to_slim`,
`ncbi_gene_results_to_python`, `plot_go_term`, `prt_terms`, `wr_hier`,
and `wr_sections`.

The optional plotting dependencies, entry points, recommended installations and
linked projects were reviewed. GOATOOLS has no packaged GUI/service entry point.
Graphviz is a headless renderer; notebooks are examples, and Cytoscape is a
separate general-purpose downstream graph editor, not a GOATOOLS companion
server. GML export is included; a Cytoscape desktop session is not bundled.
No browser service, port or GUI lifecycle is implied by SVG output.

## Installation

After this candidate has been published and indexed:

```sh
taf install goatools 1.6.8-r1
```

For local candidate testing, run `taf build` in this repository and use
`target/taf-goatools-v1.6.8-r1` with the matching locally built image.
The validation status below is not a claim that the candidate is already published.

## Usage and Command Mode

```sh
taf-goatools --help
taf-goatools --version
taf-goatools -- --help
taf-goatools -- --version
taf-goatools goatools help find_enrichment
taf-goatools find_enrichment.py --help
taf-goatools python analysis.py
```

Automatic command mode accepts a packaged executable. For upstream subcommands,
use `taf-goatools goatools subcommand ...`, not a bare subcommand.
Paths in ordinary environment variables use shell quotes. For command arguments
containing spaces, preserve literal inner quotes through the wrapper:

```sh
taf-goatools goatools find_enrichment '"study set.txt"' population.txt association.txt \
  --annofmt=id2gos --obo=go.obo --outfile='"result table.tsv"'
```

## Inputs and Outputs

Study/population files contain one compatible gene identifier per line.
An id2gos association line is `gene1 GO:0000001;GO:0000002`; use the appropriate
`--annofmt` for GAF, GPAD or gene2go. Ontology and annotation releases,
species and identifier namespaces must be chosen explicitly and consistently.

```sh
taf-goatools goatools find_enrichment study.txt population.txt association.txt \
  --annofmt=id2gos --obo=/go-resources/go-2026-08-05-basic/go-basic.obo --outfile=goea.tsv
taf-goatools goatools plot_go_term /go-resources/go-2026-08-05-basic/go-basic.obo \
  --term=GO:0008135 --engine=pygraphviz --gml --output=lineage.svg
```

An `.xlsx` output requests a workbook. Plotting also supports pydot.
The resource helper preserves original downloaded bytes. GOATOOLS `GafReader`
expects plain text, so decompress a GAF archive to a writable project directory
before passing it to the reader or enrichment command:

```sh
taf-goatools gzip -cd /go-resources/go-2026-08-05-yeast-gaf/YEAST-mod.gaf.gz > yeast.gaf
```

`--algorithm=elim` is separate from `--method` (multiple-testing correction).
Consult upstream help for the one-sided Fisher requirement and the interpretation
of additional correction on elim. TAFFISH does not choose scientific defaults
or certify a background population, evidence-code policy or annotation release.

## Resources, Databases, and Platform

The image does not bundle production ontologies or annotations. Resource units are
individual fixed ontology/slim/GAF/GPAD/gene2go snapshots. Study lists and custom
id2gos tables remain project inputs. GOlr queries are explicitly online dynamic
results, not a reproducible global database.

The `goatools-resources` helper installs explicitly selected members, never a
whole family by default. Built-in recipes are:

| ID | Named file | Bytes |
| --- | --- | ---: |
| go-2026-08-05-basic | go-basic.obo | 32,227,785 |
| go-2026-08-05-slim-generic | goslim_generic.obo | 125,864 |
| go-2026-08-05-yeast-gaf | YEAST-mod.gaf.gz | 2,249,310 |

These use the dated GO 2026-08-05 release, SHA256 and exact sizes. Ontology headers
identify 2026-07-26, which is distinct from the distribution date and app version.
Recipes reside in `docker/resource-catalog.json`. GO data are CC-BY-4.0, separate
from the software license; preserve attribution and cite the selected release.
See [GO terms and citation](https://geneontology.org/docs/go-citation-policy/).

### Personal setup and administrator-once sharing

```sh
mkdir -p "$HOME/.local/share/taffish/databases"
cd "$HOME/.local/share/taffish/databases"
export TAFFISH_GOATOOLS_DB_AUTO_MOUNT=0
taf-goatools goatools-resources --db-root goatools --resource go-2026-08-05-basic --dry-run
taf-goatools goatools-resources --db-root goatools --resource go-2026-08-05-basic --allow-network
taf-goatools goatools-resources --db-root goatools --resource go-2026-08-05-slim-generic --allow-network
taf-goatools goatools-resources --db-root goatools --verify
unset TAFFISH_GOATOOLS_DB_AUTO_MOUNT
```

Each selected versioned member has its own subdirectory, original data bytes,
recipe, resource license, SHA256 inventory and READY receipt. Repeating a complete
installation verifies the entire existing resource root before skipping the selected member.
A corrupt sibling is rejected without changing any previously installed data. The helper never replaces an existing member,
even with `--force`; choose a new root to repair a corrupt installed member.
`--force` explicitly resets bad/partial download cache only.
Installation uses Linux directory descriptors to pin its resource root, private
cache and newly created staging directory. If a path is replaced during an
installation, it fails with a diagnostic and never follows that replacement for
cleanup. Unrecognized or identity-changed staging directories are retained for
inspection. Atomic no-replace publication also refuses an empty destination
created by another process. Host shares without Linux no-replace rename (including
Docker Desktop gRPC FUSE) use an exclusive new directory and hardlinks, with READY
committed atomically last. Automatic discovery and helper verification require that complete marker/inventory;
concurrent reads may fail closed while installation is in progress. A failed
uncommitted install removes only this transaction's files, never a foreign child.
The filesystem must support either no-replace rename or same-filesystem hardlinks.
These are packaging safety checks, not GO algorithms.

Administrators can run the same setup once under
`/usr/local/share/taffish/databases/goatools` or
`/opt/taffish/databases/goatools`. Prepare and authorize the writable parent
outside this app; it never runs sudo or changes existing directory ownership/mode.
New published directories are 0755 and files 0644, including with umask 077.
Consumers mount them read-only and need neither network nor write permission.

Setup is serialized by an advisory lock in a caller-owned private sibling
`.<root-name>.goatools-cache` directory. Downloads have bounded retries, resumable
partials and full SHA/size verification; a zero-byte partial restarts normally.
Invalid completed caches fail closed unless explicitly reset. Staging and final
members share a filesystem; publication is an atomic rename or READY-last commit. Peak per-member
space is cache + stage + 64 MiB reserve. Cache is reusable; retained verified
downloads consume approximately the installed data size again. SIGINT/TERM/HUP
must preserve existing members. SIGKILL may leave private staging or an incomplete
READY-last member; verification rejects an incomplete member and an administrator
must inspect it before reuse. Do not treat an unverified directory as installed.
Do not remove locks/caches while another installation runs.

### Discovery, override, disable, and backend fallback

Priority: `TAFFISH_GOATOOLS_DB_PATH`, then
`~/.local/share/taffish/databases/goatools`, then `/usr/local/share/...`,
then `/opt/taffish/...`. The first existing root must pass schema-marker and
full inventory hashes; valid root symlinks are physically resolved, internal
symlinks and dangling roots are rejected. Partial catalogs are allowed only when
all installed members validate. No cross-root search or missing-member download
occurs. Shared storage is exposed at `/go-resources`; the caller still selects
the exact data file. Automatic validation requires host Python 3 (standard library
only, isolated mode). The frozen `src/resource_validation.py` is also copied into
the image and imported by the installer: both paths check the same recipe schema,
member ID/directory, filename, size, content SHA256, inventory, READY and license/source.
A renamed or re-signed but inconsistent member fails before mounting. A valid root
symlink is resolved physically; inner symlinks are rejected.
If host Python 3 is unavailable, disable discovery, use `goatools-resources --verify`
inside the container against an explicit read-only bind, then use that verified
root manually. Missing Python is an error, not permission to skip verification.

`TAFFISH_GOATOOLS_DB_AUTO_MOUNT=0` disables discovery for setup or manual paths.
`TAFFISH_GOATOOLS_DB_PATH="/absolute/prepared root"` overrides discovery.
Roots containing a colon or comma cannot use automatic mounts; use a safe alias
or backend-supported manual mapping instead.

| Capability | Docker | Podman | Apptainer |
| --- | --- | --- | --- |
| Select backend | TAFFISH_CONTAINER_BACKEND=docker | TAFFISH_CONTAINER_BACKEND=podman | TAFFISH_CONTAINER_BACKEND=apptainer |
| Automatic shared root | read-only volume | read-only volume | read-only bind |
| Manual read-only mapping | TAFFISH_DOCKER_RUN_ARGS="-v /srv/go:/go-resources:ro" | TAFFISH_PODMAN_RUN_ARGS="-v /srv/go:/go-resources:ro" | TAFFISH_APPTAINER_RUN_ARGS="--bind /srv/go:/go-resources:ro" |
| Setup parent mapping | TAFFISH_DOCKER_RUN_ARGS="-v /srv/taffish/databases:/install" | TAFFISH_PODMAN_RUN_ARGS="-v /srv/taffish/databases:/install" | TAFFISH_APPTAINER_RUN_ARGS="--bind /srv/taffish/databases:/install" |
| Offline policy | --network none | --network none | --net --network none (site permission required) |

For the setup mappings, disable discovery and pass `--db-root /install/goatools`.
Do not map only a read-only resource member or omit the writable sibling cache
parent. Project-local inputs in the working directory remain a backend-neutral
fallback. Apptainer requires native compatible Linux; macOS is not an Apptainer host.

### Other fixed snapshots and online boundaries

`--recipe FILE.json` supports an explicitly chosen single resource without changing
the app. Required fields are `id`, `version`, `filename`, HTTPS `url`,
64-character lowercase `sha256`, positive `size` in bytes, `license` and
`attribution`. Use a new versioned ID for different bytes; do not repoint an old
identity. Inspect the built-in catalog for exact examples.
`--archive-dir DIR` supplies the original named files offline, with identical
SHA/size validation. A recipe records provenance, not an automatic license grant:
review the selected provider's terms before installation or site redistribution.

The built-in catalog is deliberately not a list of every organism. Other GO
GAF/GPAD/slim snapshots use the same locked recipe contract. NCBI gene2go uses a
mutable FTP/HTTPS endpoint: retain an exact snapshot, its digest/size, attribution
and applicable [NCBI policies](https://www.ncbi.nlm.nih.gov/home/about/policies/);
supply an offline archive when upstream no longer serves those bytes. Study
inputs and dynamic GOlr responses have no implied canonical global identity.

Upstream source files and algorithms are retained, but a separate Python startup
hook blocks legacy implicit resource I/O (`base.dnld_file`, HTTP/FTP fetches and
remote `nopen`). Legacy convenience calls for missing default or explicit local
OBO/annotation paths fail with `GOATOOLS_RESOURCE_MISSING` before a request or
download temporary is created. Ordinary local-file readers retain upstream errors.
Existing local inputs retain upstream behavior; no ontology, scoring or statistical
code is replaced. This guard is packaging policy, not an upstream algorithm patch.
Downloads belong to the explicit `goatools-resources` setup command:
without `--allow-network` it only reuses verified installed members/cache or
`--archive-dir` files. Opt-in downloads use the selected fixed recipe's HTTPS URL,
size and checksum and the explicit persistent `--db-root`; the flag does not enable
mutable analysis-time fallback. `--dry-run` reports the effective network policy.
The old mutable downloader URLs are not the shared
installer's integrity contract. Pass existing local paths and enforce offline
backend policy for reproducible analysis. `fetch_associations` remains an explicit
online command; a live endpoint, server dataset or result completeness is not
guaranteed. The explicit GOlr query is separate from resource installation and is
not made offline or reproducible by this packaging policy. This is not a network
sandbox for arbitrary user Python or shell programs.

## Build, Image Size and Reproducibility

The official wheel/sdist and explicit optional packages have fixed URLs and SHA256.
The base is pinned to a multi-platform digest. Transitive PyPI and Bookworm APT
resolution can still change; inventories are receipts, not full input locks.
Risk-point Dockerfile comments explain recovery: never bypass an integrity check
or substitute new bytes under an old release. Future upstream retention is not
guaranteed by a successful current build.

The application venv removes generic dependency tests, venv pip/wheel, static
archives and bytecode, but preserves runtime imports, upstream example data, licenses,
source archives and inventories under `/opt/goatools/share`.
Build-time checks are version/help/import/tiny enrichment only. Graphics run in
separate runtime smoke, not as a fragile ARM64 build gate.
The final native images are 574,497,328 bytes on amd64 (574.5 MB / 547.9 MiB)
and 604,961,134 bytes on ARM64 (605.0 MB / 576.9 MiB).
Scientific Python, upstream example data, source archives and license/provenance
material are retained. The image contains no build compiler or temporary build
tree; the remaining major dependencies support the advertised APIs.

## Testing and Boundaries

Direct smoke covers combined/individual command existence, all CLI help paths,
classic enrichment, independent XLSX, slim mapping, both plotting engines/GML,
new elim behavior and offline resource contracts. Each test is independent and
does not require production mounts or network. Runtime writes are limited to
unique TMPDIR scratch/cache and explicitly requested output/resource directories.

The 1.6.8 candidate was freshly built and verified on 2026-10-29; previous
1.6.7 results were not used to certify this successor:

| Native environment | Actual validated backends | Evidence |
| --- | --- | --- |
| xjp Linux amd64 | Docker, Podman, Apptainer | PASS: fresh offline smoke; D/P non-root read-only roots; same-OCI SIF; real-wrapper main paths, resources and interruption/recovery |
| macOS-hosted Linux arm64 | Docker, Podman | PASS: native build; offline and non-root read-only smoke; real-wrapper paths, resources and host-bind transaction regressions |

The passing direct matrix contains 234 independent probes: 26 per mode, including
combined command existence, 15 individual commands and ten manifest tests.
Real-wrapper checks cover quoted paths, both rendering engines, explicit
HTTPS/offline resource setup, administrator-once read-only consumption, corrupt
resource rejection and interrupted-install recovery. The 1.6.8 GPAD/Python fixes
and prior MICA correction use small independent synthetic fixtures.
Seventeen transaction regressions cover early interruption, output failure,
parent/staging substitution, existing destinations and READY-last publication.
They also pass through the actual wrapper on writable host mounts in all five
tested platform/backend combinations. On xjp, actual INT/TERM interruption,
recovery and repeated installation preserve old resources. Fixed official slim
HTTPS installation, offline basic/GAF installation, root-once read-only sharing
and a real HTTPS partial-resume check passed. These tests use synthetic or small
public fixtures, not production research data.

The Action is unchanged and byte-identical to fresh taf new. ARM64 Apptainer is
not separately validated: the native platform and backend axes are covered,
but this cross-combination is not claimed as tested. Full production-scale
scientific accuracy, every organism/catalog, live GOlr services and future public
CI/GHCR/Index are not certified by these packaging tests. Public images require
their own post-publication digest, non-root permission and Index/SIF checks.
Local publish dry-run and candidate readiness do not mean this version is published.

## License and Citation

TAFFISH packaging: Apache-2.0. GOATOOLS: BSD-2-Clause. Explicit optional packages,
Graphviz and their bundled components retain upstream licenses. Exact sources,
licenses, patch and package inventories are retained in the image.

Klopfenstein DV et al. GOATOOLS: A Python library for Gene Ontology analyses.
Scientific Reports. 2018;8:10872. https://doi.org/10.1038/s41598-018-28948-z

Upstream manual: https://github.com/tanghaibao/goatools/blob/v1.6.8/README.md
