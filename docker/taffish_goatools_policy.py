"""Packaging-only resource I/O guard; leave upstream algorithms and files intact."""
import os
from goatools import base


def deny_download(*_args, **_kwargs):
    raise FileNotFoundError(
        "GOATOOLS_RESOURCE_MISSING: implicit resource downloads are disabled. "
        "Pass an existing local ontology/annotation file. Prepare a fixed resource with "
        "goatools-resources --resource ID --db-root ROOT --allow-network, or use "
        "--archive-dir for offline installation; select the resulting local file explicitly."
    )


def local_file_only(src_ftp, dst_file, prt=None):
    if not os.path.isfile(dst_file):
        deny_download()


_nopen = base.nopen


def local_nopen(f, mode="r"):
    if isinstance(f, str) and f.startswith(("http://", "https://", "ftp://")):
        deny_download()
    return _nopen(f, mode)


# These functions perform resource I/O only, never GOEA or ontology computation.
# Keep existing-file behavior, and fail before creating download temporaries.
base.dnld_file = local_file_only
base.http_get = deny_download
base.ftp_get = deny_download
base.nopen = local_nopen
