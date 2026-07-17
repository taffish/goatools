FROM python:3.12-slim-bookworm AS builder

ARG TARGETARCH
ARG GOATOOLS_VERSION=1.6.5
ARG GOATOOLS_COMMIT=c5fedea21e9f66c3c2c13da788ea04a5c760329f
ARG GOATOOLS_WHEEL_URL=https://files.pythonhosted.org/packages/20/53/1020a7b32651289a68ec853d43fb412c8982d6d1de2289e6cb6f55bc4b7b/goatools-1.6.5-py3-none-any.whl
ARG GOATOOLS_WHEEL_SHA256=2b093ded287178b494e28350bce6beb60b920ff5f923fc5aaef227dd6ffb935a
ARG GOATOOLS_SDIST_URL=https://files.pythonhosted.org/packages/e6/87/07e80f31af72d8e2c35936d1e5670ac05ff6009cc4a9412eb99e18efd24a/goatools-1.6.5.tar.gz
ARG GOATOOLS_SDIST_SHA256=0d799706dc3ae4480feda25f411f8e9b2741c0d8ea7ad73af0b05730198a4be1
ARG PYSOLR_VERSION=3.11.0
ARG PYSOLR_SDIST_URL=https://files.pythonhosted.org/packages/0d/2a/b6c793a17e173524ccc7a90cdd8ebb65264f6ebcdb1942eba2478ec3a85e/pysolr-3.11.0.tar.gz
ARG PYSOLR_SDIST_SHA256=bbd0e7467835316880f994b55386c9bc3c146733c17d85a3fed317755976c40a
ARG NETWORKX_VERSION=3.6.1
ARG NETWORKX_WHEEL_URL=https://files.pythonhosted.org/packages/9e/c9/b2622292ea83fbb4ec318f5b9ab867d0a28ab43c5717bb85b0a5f6b3b0a4/networkx-3.6.1-py3-none-any.whl
ARG NETWORKX_WHEEL_SHA256=d47fbf302e7d9cbbb9e2555a0d267983d2aa476bac30e90dfbe5669bd57f3762
ARG NETWORKX_SDIST_URL=https://files.pythonhosted.org/packages/6a/51/63fe664f3908c97be9d2e4f1158eb633317598cfa6e1fc14af5383f17512/networkx-3.6.1.tar.gz
ARG NETWORKX_SDIST_SHA256=26b7c357accc0c8cde558ad486283728b65b6a95d85ee1cd66bafab4c8168509
ARG PYGRAPHVIZ_VERSION=2.0
ARG PYGRAPHVIZ_SDIST_URL=https://files.pythonhosted.org/packages/4f/03/14ba7e94e2a9107324b5435052a34c92df2637274343c26aa44361626b01/pygraphviz-2.0.tar.gz
ARG PYGRAPHVIZ_SDIST_SHA256=7cc6cfff4bfa6c1bf389cbbf72f5995a717c69de69c18763544c04b41181f59e
ARG PYGRAPHVIZ_AMD64_WHEEL_URL=https://files.pythonhosted.org/packages/2b/3a/aff603c4e479b2d71182903f0c15942c0a0c2aa8ac3d91bc463e9436822c/pygraphviz-2.0-cp312-cp312-manylinux_2_28_x86_64.whl
ARG PYGRAPHVIZ_AMD64_WHEEL_SHA256=57bc07983a58aa59854aba8c90cd0b12293de7a7013fcc999c3c35b1f6321ae3
ARG PYGRAPHVIZ_ARM64_WHEEL_URL=https://files.pythonhosted.org/packages/ce/49/823567597311a4b76b6ea7dbd117f7d87abcc9e774a5f83b4d6d9d4f52c6/pygraphviz-2.0-cp312-cp312-manylinux_2_28_aarch64.whl
ARG PYGRAPHVIZ_ARM64_WHEEL_SHA256=5d14b9b69ff87a5c51f5207557fdb868b67f99c2222d8f131a2a1d9a3bbf01bd

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONNOUSERSITE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/opt/goatools/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin

RUN set -eux; \
    for attempt in 1 2 3 4 5; do \
      if apt-get -o Acquire::Retries=5 update \
       && apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
            ca-certificates \
            curl \
            patch \
            tar; then \
        break; \
      fi; \
      if [ "${attempt}" = "5" ]; then exit 1; fi; \
      sleep 5; \
    done; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb

WORKDIR /tmp/goatools-build

COPY docker/goatools-1.6.5-pydot-wrap-width.patch /tmp/goatools-pydot.patch

RUN --mount=type=cache,target=/root/.cache/pip set -eux; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "${GOATOOLS_WHEEL_URL}" -o "goatools-${GOATOOLS_VERSION}-py3-none-any.whl"; \
    echo "${GOATOOLS_WHEEL_SHA256}  goatools-${GOATOOLS_VERSION}-py3-none-any.whl" | sha256sum -c -; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "${GOATOOLS_SDIST_URL}" -o "goatools-${GOATOOLS_VERSION}.tar.gz"; \
    echo "${GOATOOLS_SDIST_SHA256}  goatools-${GOATOOLS_VERSION}.tar.gz" | sha256sum -c -; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "${PYSOLR_SDIST_URL}" -o "pysolr-${PYSOLR_VERSION}.tar.gz"; \
    echo "${PYSOLR_SDIST_SHA256}  pysolr-${PYSOLR_VERSION}.tar.gz" | sha256sum -c -; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "${NETWORKX_WHEEL_URL}" -o "networkx-${NETWORKX_VERSION}-py3-none-any.whl"; \
    echo "${NETWORKX_WHEEL_SHA256}  networkx-${NETWORKX_VERSION}-py3-none-any.whl" | sha256sum -c -; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "${NETWORKX_SDIST_URL}" -o "networkx-${NETWORKX_VERSION}.tar.gz"; \
    echo "${NETWORKX_SDIST_SHA256}  networkx-${NETWORKX_VERSION}.tar.gz" | sha256sum -c -; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "${PYGRAPHVIZ_SDIST_URL}" -o "pygraphviz-${PYGRAPHVIZ_VERSION}.tar.gz"; \
    echo "${PYGRAPHVIZ_SDIST_SHA256}  pygraphviz-${PYGRAPHVIZ_VERSION}.tar.gz" | sha256sum -c -; \
    case "${TARGETARCH}" in \
      amd64) \
        pygraphviz_wheel="pygraphviz-${PYGRAPHVIZ_VERSION}-cp312-cp312-manylinux_2_28_x86_64.whl"; \
        pygraphviz_url="${PYGRAPHVIZ_AMD64_WHEEL_URL}"; \
        pygraphviz_sha256="${PYGRAPHVIZ_AMD64_WHEEL_SHA256}"; \
        ;; \
      arm64) \
        pygraphviz_wheel="pygraphviz-${PYGRAPHVIZ_VERSION}-cp312-cp312-manylinux_2_28_aarch64.whl"; \
        pygraphviz_url="${PYGRAPHVIZ_ARM64_WHEEL_URL}"; \
        pygraphviz_sha256="${PYGRAPHVIZ_ARM64_WHEEL_SHA256}"; \
        ;; \
      *) \
        echo "unsupported TARGETARCH: ${TARGETARCH}" >&2; \
        exit 1; \
        ;; \
    esac; \
    curl --retry 5 --retry-delay 2 --retry-all-errors -fsSL \
      "${pygraphviz_url}" -o "${pygraphviz_wheel}"; \
    echo "${pygraphviz_sha256}  ${pygraphviz_wheel}" | sha256sum -c -; \
    mkdir -p \
      /tmp/goatools-src \
      /tmp/networkx-src \
      /tmp/pysolr-src \
      /tmp/pygraphviz-src; \
    tar --no-same-owner -xzf "goatools-${GOATOOLS_VERSION}.tar.gz" \
      -C /tmp/goatools-src --strip-components=1; \
    tar --no-same-owner -xzf "pysolr-${PYSOLR_VERSION}.tar.gz" \
      -C /tmp/pysolr-src --strip-components=1; \
    tar --no-same-owner -xzf "networkx-${NETWORKX_VERSION}.tar.gz" \
      -C /tmp/networkx-src --strip-components=1; \
    tar --no-same-owner -xzf "pygraphviz-${PYGRAPHVIZ_VERSION}.tar.gz" \
      -C /tmp/pygraphviz-src --strip-components=1; \
    python -m venv --copies /opt/goatools/venv; \
    /opt/goatools/venv/bin/python -m pip install --no-cache-dir \
      "./pysolr-${PYSOLR_VERSION}.tar.gz" \
      "./networkx-${NETWORKX_VERSION}-py3-none-any.whl" \
      "./${pygraphviz_wheel}" \
      "./goatools-${GOATOOLS_VERSION}-py3-none-any.whl"; \
    /opt/goatools/venv/bin/python -m pip check; \
    site_packages="$(/opt/goatools/venv/bin/python -c \
      'import sysconfig; print(sysconfig.get_paths()["purelib"])')"; \
    patch -d "${site_packages}" -p1 < /tmp/goatools-pydot.patch; \
    grep -A6 -F 'grph = self.make_graph_pydot(' \
      "${site_packages}/goatools/obo_parser.py" | grep -F 'wrap_width,' >/dev/null; \
    rm -f "${site_packages}/goatools/obo_parser.py.orig"; \
    mkdir -p \
      /opt/goatools/share/doc/goatools \
      /opt/goatools/share/licenses/goatools \
      /opt/goatools/share/licenses/networkx \
      /opt/goatools/share/licenses/pysolr \
      /opt/goatools/share/licenses/pygraphviz \
      /opt/goatools/share/patches \
      /opt/goatools/share/provenance \
      /opt/goatools/share/sources \
      /opt/goatools/share/testdata; \
    install -m 0644 /tmp/goatools-src/LICENSE \
      /opt/goatools/share/licenses/goatools/LICENSE; \
    install -m 0644 /tmp/networkx-src/LICENSE.txt \
      /opt/goatools/share/licenses/networkx/LICENSE.txt; \
    install -m 0644 /tmp/pysolr-src/LICENSE \
      /opt/goatools/share/licenses/pysolr/LICENSE; \
    install -m 0644 /tmp/pygraphviz-src/LICENSE \
      /opt/goatools/share/licenses/pygraphviz/LICENSE; \
    install -m 0644 /tmp/pygraphviz-src/LICENSE.graphviz \
      /opt/goatools/share/licenses/pygraphviz/LICENSE.graphviz; \
    install -m 0644 /tmp/goatools-src/README.md \
      /opt/goatools/share/doc/goatools/README-upstream.md; \
    install -m 0644 /tmp/goatools-src/CHANGELOG.md \
      /opt/goatools/share/doc/goatools/CHANGELOG.md; \
    install -m 0644 /tmp/goatools-src/pyproject.toml \
      /opt/goatools/share/doc/goatools/pyproject.toml; \
    install -m 0644 /tmp/goatools-src/setup.cfg \
      /opt/goatools/share/doc/goatools/setup.cfg; \
    install -m 0644 "goatools-${GOATOOLS_VERSION}.tar.gz" \
      "/opt/goatools/share/sources/goatools-${GOATOOLS_VERSION}.tar.gz"; \
    install -m 0644 "pysolr-${PYSOLR_VERSION}.tar.gz" \
      "/opt/goatools/share/sources/pysolr-${PYSOLR_VERSION}.tar.gz"; \
    install -m 0644 "networkx-${NETWORKX_VERSION}.tar.gz" \
      "/opt/goatools/share/sources/networkx-${NETWORKX_VERSION}.tar.gz"; \
    install -m 0644 "pygraphviz-${PYGRAPHVIZ_VERSION}.tar.gz" \
      "/opt/goatools/share/sources/pygraphviz-${PYGRAPHVIZ_VERSION}.tar.gz"; \
    install -m 0644 /tmp/goatools-pydot.patch \
      /opt/goatools/share/patches/goatools-1.6.5-pydot-wrap-width.patch; \
    (cd /opt/goatools/share/patches \
      && sha256sum goatools-1.6.5-pydot-wrap-width.patch > SHA256SUMS); \
    /opt/goatools/venv/bin/python -m pip freeze \
      > /opt/goatools/share/provenance/python-packages.txt; \
    { \
      printf 'goatools_version=%s\n' "${GOATOOLS_VERSION}"; \
      printf 'goatools_upstream_tag=v%s\n' "${GOATOOLS_VERSION}"; \
      printf 'goatools_upstream_commit=%s\n' "${GOATOOLS_COMMIT}"; \
      printf 'goatools_wheel_url=%s\n' "${GOATOOLS_WHEEL_URL}"; \
      printf 'goatools_wheel_sha256=%s\n' "${GOATOOLS_WHEEL_SHA256}"; \
      printf 'goatools_sdist_url=%s\n' "${GOATOOLS_SDIST_URL}"; \
      printf 'goatools_sdist_sha256=%s\n' "${GOATOOLS_SDIST_SHA256}"; \
      printf 'pysolr_version=%s\n' "${PYSOLR_VERSION}"; \
      printf 'pysolr_sdist_sha256=%s\n' "${PYSOLR_SDIST_SHA256}"; \
      printf 'networkx_version=%s\n' "${NETWORKX_VERSION}"; \
      printf 'networkx_wheel_sha256=%s\n' "${NETWORKX_WHEEL_SHA256}"; \
      printf 'networkx_sdist_sha256=%s\n' "${NETWORKX_SDIST_SHA256}"; \
      printf 'networkx_scope=GOATOOLS plot_go_term --gml conversion for Cytoscape\n'; \
      printf 'pygraphviz_version=%s\n' "${PYGRAPHVIZ_VERSION}"; \
      printf 'pygraphviz_sdist_sha256=%s\n' "${PYGRAPHVIZ_SDIST_SHA256}"; \
      printf 'compatibility_patch=goatools-1.6.5-pydot-wrap-width.patch\n'; \
      printf 'compatibility_patch_scope=pass the advertised wrap_width option to the pydot graph builder\n'; \
      printf 'external_data=GO OBO, GO slim, GAF, GPAD, gene2go, and id2gos files are user supplied and not bundled\n'; \
      printf 'goatools_test_data_retained=true\n'; \
    } > /opt/goatools/share/provenance/source.txt

RUN set -eux; \
    site_packages="$(/opt/goatools/venv/bin/python -c \
      'import sysconfig; print(sysconfig.get_paths()["purelib"])')"; \
    test -d "${site_packages}/goatools/test_data"; \
    find "${site_packages}" -depth -type d \( -name test -o -name tests \) \
      -exec rm -rf '{}' +; \
    test -d "${site_packages}/goatools/test_data"; \
    find /opt/goatools/venv -type f -name '*.a' -delete; \
    rm -rf \
      "${site_packages}/pip" \
      "${site_packages}"/pip-*.dist-info \
      "${site_packages}/wheel" \
      "${site_packages}"/wheel-*.dist-info; \
    rm -f \
      /opt/goatools/venv/bin/pip \
      /opt/goatools/venv/bin/pip3 \
      /opt/goatools/venv/bin/pip3.12 \
      /opt/goatools/venv/bin/wheel; \
    find /opt/goatools/venv -type d -name '__pycache__' -prune -exec rm -rf '{}' +; \
    find /opt/goatools/venv -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete; \
    chmod -R a+rX /opt/goatools; \
    rm -rf \
      /root/.cache \
      /tmp/goatools-build \
      /tmp/goatools-src \
      /tmp/networkx-src \
      /tmp/pysolr-src \
      /tmp/pygraphviz-src \
      /tmp/goatools-pydot.patch

FROM python:3.12-slim-bookworm AS runtime

ARG GOATOOLS_VERSION=1.6.5
ARG NETWORKX_VERSION=3.6.1
ARG PYSOLR_VERSION=3.11.0
ARG PYGRAPHVIZ_VERSION=2.0
ARG DEBIAN_FRONTEND=noninteractive

LABEL org.opencontainers.image.title="GOATOOLS" \
      org.opencontainers.image.description="TAFFISH runtime for Gene Ontology enrichment, DAG analysis, GO slim mapping, and plotting" \
      org.opencontainers.image.source="https://github.com/tanghaibao/goatools" \
      org.opencontainers.image.licenses="BSD-2-Clause"

ENV PYTHONNOUSERSITE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SHELL=/bin/sh \
    XDG_CACHE_HOME=/tmp/xdg-cache \
    PATH=/opt/goatools/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
    TAFFISH_ENV=TAFFISH \
    TAFFISH_NAME=goatools \
    TAFFISH_VERSION=${GOATOOLS_VERSION} \
    TAFFISH_RELEASE=1

RUN set -eux; \
    for attempt in 1 2 3 4 5; do \
      if apt-get -o Acquire::Retries=5 update \
       && apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
            ca-certificates \
            coreutils \
            curl \
            findutils \
            fonts-dejavu-core \
            graphviz \
            grep \
            gzip \
            libgomp1; then \
        break; \
      fi; \
      if [ "${attempt}" = "5" ]; then exit 1; fi; \
      sleep 5; \
    done; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb

COPY --from=builder /opt/goatools /opt/goatools
COPY docker/goatools-smoke.sh /opt/goatools/share/testdata/goatools-smoke.sh

FROM runtime AS final

RUN set -eux; \
    chmod 0755 /opt/goatools/share/testdata/goatools-smoke.sh; \
    dpkg-query -W -f='${binary:Package}\t${Version}\n' | sort \
      > /opt/goatools/share/provenance/debian-packages.tsv; \
    goatools --version 2>&1 | grep -Fx "${GOATOOLS_VERSION}" >/dev/null; \
    python -c 'import importlib.metadata as md; import goatools, networkx, pygraphviz, pysolr; assert md.version("goatools") == "1.6.5"; assert md.version("networkx") == "3.6.1"; assert md.version("pygraphviz") == "2.0"; assert md.version("pysolr") == "3.11.0"; print(goatools.__version__)' \
      | grep -Fx "${GOATOOLS_VERSION}" >/dev/null; \
    /opt/goatools/share/testdata/goatools-smoke.sh buildtime; \
    find /opt/goatools/venv -type f -name '*.so' -print0 \
      | xargs -0 -r ldd > /tmp/goatools-ldd.txt; \
    if grep -F 'not found' /tmp/goatools-ldd.txt; then exit 1; fi; \
    rm -rf /tmp/taf-goatools-* /tmp/goatools-ldd.txt /tmp/xdg-cache /root/.cache

WORKDIR /root
