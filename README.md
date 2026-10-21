# goatools

`goatools` packages GOATOOLS for TAFFISH.

Package identity:

- name: `goatools`; command: `taf-goatools`; kind: `tool`
- version: `1.6.6-r1`; TAFFISH packaging license: Apache-2.0
- upstream: [GOATOOLS v1.6.6](https://github.com/tanghaibao/goatools/tree/v1.6.6)
- upstream commit: `ffcdfcdbee22f652dd600561ffabb67e60fccb8b`; upstream license: BSD-2-Clause
- native platforms: `linux/amd64`, `linux/arm64`

## What This App Packages

The official PyPI wheel, Python 3.12 and declared dependencies, the GOATOOLS
dispatcher and standalone commands, Graphviz, pydot, pygraphviz, NetworkX
(for GML export), pysolr (for the advertised GOlr command), curl and gzip.
The Python API and upstream `goatools.test_data` remain available.

Version 1.6.6 introduces pluggable GOEA scoring and `elim`, per-run Fisher
calculation reuse, and FDR null scoring that follows the study algorithm,
alternative and in-population study size. The default remains classic.
No enrichment algorithm is patched by TAFFISH. The existing one-line
1.6.5-origin patch passing `wrap_width` to pydot remains necessary in 1.6.6;
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
taf install goatools 1.6.6-r1
```

For local candidate testing, run `taf build` in this repository and use
`target/taf-goatools-v1.6.6-r1` with the matching locally built image.
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
installation verifies and skips it. The helper never replaces an existing member,
even with `--force`; choose a new root to repair a corrupt installed member.
`--force` explicitly resets bad/partial download cache only.

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
members share a filesystem; publication is an atomic rename. Peak per-member
space is cache + stage + 64 MiB reserve. Cache is reusable; retained verified
downloads consume approximately the installed data size again. SIGINT/TERM/HUP
must preserve existing members. SIGKILL may leave a private staging directory;
it is not visible as an installed member and requires administrator inspection.
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
Final image sizes are 571,026,040 bytes (amd64 Docker, 544.57 MiB) and
611,741,384 bytes (arm64 Podman, 583.40 MiB). `/opt/goatools` accounts for about
362/379 MiB; scientific Python libraries and retained upstream example data dominate.
Approximately 20 MiB of
official source archives are deliberately retained for provenance/license review.
Small headers in the pinned Python base and NumPy's public include interface
are retained; deleting files in the immutable base in another layer would not
reclaim the downloaded base layer. There is no copied compiler/sysroot or
production GO database.

## Testing and Boundaries

Direct smoke covers combined/individual command existence, all CLI help paths,
classic enrichment, independent XLSX, slim mapping, both plotting engines/GML,
new elim behavior and offline resource contracts. Each test is independent and
does not require production mounts or network. Runtime writes are limited to
unique TMPDIR scratch/cache and explicitly requested output/resource directories.

Validation on 2026-10-20:

| Evidence axis | Result |
| --- | --- |
| Native amd64 (xjp Docker) and arm64 (local Podman Linux VM) | Both built from app-root context `.` using `-f docker/Dockerfile`; no QEMU claim; final-stage version ARG is explicit for both builders |
| Docker / Podman on native amd64 and arm64 | 24 independent offline probes in normal rootfs plus the same 24 in read-only rootfs for each tested combination |
| Apptainer, native amd64 | 24 independent offline probes using the read-only SIF from that exact amd64 OCI; 216 direct probes in total |
| Built wrapper, all five tested backend/platform combinations | 34 main-flow/resource checks and 58 new fail-closed/identity/recovery checks each; actual host binds and paths containing spaces |
| Resource interruption, amd64 three backends | 30 checks each: lock/download/staging INT/TERM, old-member preservation, recovery, idempotence and verification |
| Shared resources | Three fixed official members installed/read; explicitly opted-in HTTPS slim setup, offline reuse without opt-in, root-owned member read by non-root and write rejection on each backend |
| Discovery | 46 isolated contract cases including personal/site priorities, override/disable, symlinks, corrupt/partial roots, no fallback and missing host Python |
| Plotting and diagnostics | Both SVG/PNG engines plus GML; actual PNGs visually checked; injected help error retains stage, exit code and log |
| Final help | 89 lines; real gzip/slim/plot/manual-verify examples passed on three backends; final wrapper executable/source/manifest unchanged by the final help-only note |
| Packaged identity | Eight current helper/validator/policy/smoke files matched byte-for-byte inside each tested backend/platform image |

Source-file checks compare the installed package with the official sdist: the only
Python source difference is the inherited one-line pydot argument fix described
above. The canonical Action is copied byte-for-byte from fresh `taf new` and has
not been customized.

ARM64 Apptainer is **not separately validated for this repair**. Local Docker
Desktop required an explicitly authorized restart; the interrupted attempt is
retained separately, and the full ARM64 Docker suite passed after recovery using
the exact same OCI identity as Podman. Native amd64/arm64 and the three backends
close the independent platform/backend axes. The shared validator and resource
policy are architecture-neutral; Docker/Podman use the same mount arguments and
no architecture-specific Apptainer branch is introduced. Actual deployment into
host `/usr/local/share` or `/opt/taffish` was not performed; priority was tested
in isolation and root-once permission/mount behavior with a representative
root-owned prepared directory. The standard locations remain administrator choices.
Interruption tests exercise locked/offline-transfer/staging transaction phases;
real opted-in HTTPS setup and offline reuse are separately tested, not every
network interruption timing. No production-scale scientific accuracy claim follows from synthetic packaging
tests. The real GO ontology/GAF parser checks do not validate every species/catalog,
live GOlr responses or every analytical API. Future Action/Index failures require
a new immutable successor, not rewriting this version.

## License and Citation

TAFFISH packaging: Apache-2.0. GOATOOLS: BSD-2-Clause. Explicit optional packages,
Graphviz and their bundled components retain upstream licenses. Exact sources,
licenses, patch and package inventories are retained in the image.

Klopfenstein DV et al. GOATOOLS: A Python library for Gene Ontology analyses.
Scientific Reports. 2018;8:10872. https://doi.org/10.1038/s41598-018-28948-z

Upstream manual: https://github.com/tanghaibao/goatools/blob/v1.6.6/README.md
