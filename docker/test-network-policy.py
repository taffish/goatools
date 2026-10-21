#!/usr/bin/env python3
"""Prove missing-resource paths fail before network I/O or output creation."""
from pathlib import Path
import tempfile
from unittest.mock import patch
from goatools import base

with tempfile.TemporaryDirectory(prefix="goatools-network-policy-") as tmp:
    root = Path(tmp)
    with patch.object(base.requests, "get", side_effect=AssertionError("HTTP attempted")), \
         patch.object(base, "ftpretty", side_effect=AssertionError("FTP attempted")), \
         patch.object(base, "urlopen", side_effect=AssertionError("URL attempted")):
        cases = [
            lambda: base.download_go_basic_obo(str(root / "go-basic.obo")),
            lambda: base.download_ncbi_associations(str(root / "gene2go")),
            lambda: base.dnld_file(src_ftp="https://example.invalid/gaf.gz", dst_file=str(root / "a.gaf")),
            lambda: base.http_get("https://example.invalid/x", str(root / "x")),
            lambda: base.ftp_get("ftp://example.invalid/x", str(root / "x")),
            lambda: base.nopen(f="https://example.invalid/x"),
        ]
        for call in cases:
            try:
                call()
            except FileNotFoundError as exc:
                assert "GOATOOLS_RESOURCE_MISSING" in str(exc)
            else:
                raise AssertionError("resource policy bypass")
        assert not list(root.iterdir())
        local = root / "local.txt"
        local.write_text("preserve local input\n")
        base.dnld_file("https://example.invalid/x", str(local))
        with base.nopen(f=str(local)) as stream:
            assert stream.read() == "preserve local input\n"
        assert local.read_text() == "preserve local input\n"
print("RESOURCE_NETWORK_POLICY_PASS")
