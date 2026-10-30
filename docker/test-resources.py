#!/usr/bin/env python3
"""Offline packaging tests using synthetic bytes, not production annotations."""
import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

HELPER = Path("/usr/local/bin/goatools-resources")
if not HELPER.exists():
    HELPER = Path(__file__).with_name("goatools-resources.py")
loader = importlib.machinery.SourceFileLoader("go_resources", str(HELPER))
spec = importlib.util.spec_from_loader(loader.name, loader)
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)


def run(*args, ok=True):
    p = subprocess.run([sys.executable, str(HELPER), *map(str, args)],
                       text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if (p.returncode == 0) != ok:
        print(p.stdout)
        raise AssertionError((args, p.returncode))
    if not ok:
        assert "GOATOOLS_RESOURCE_ERROR" in p.stdout or "error:" in p.stdout, p.stdout
    return p.stdout


with tempfile.TemporaryDirectory(prefix="goatools-resource-test-") as td:
    base = Path(td)
    source = base / "archive"
    source.mkdir()
    data = b"format-version: 1.2\n\n[Term]\nid: GO:0008150\nname: synthetic root\n"
    (source / "tiny.obo").write_bytes(data)
    rec = dict(id="synthetic-v1", version="synthetic-v1", filename="tiny.obo",
               url="https://example.invalid/tiny.obo", sha256=hashlib.sha256(data).hexdigest(),
               size=len(data), license="CC0-1.0", attribution="TAFFISH synthetic fixture")
    recipe = base / "recipe.json"
    recipe.write_text(json.dumps(rec))
    root = base / "shared"
    args = ["--recipe", recipe, "--db-root", root, "--archive-dir", source]
    plan = json.loads(run(*args, "--dry-run"))
    assert plan["resources"] == [rec] and not root.exists()
    old_umask = os.umask(0o077)
    try:
        run(*args)
    finally:
        os.umask(old_umask)
    member = root / rec["id"]
    before = {p.name: mod.digest(p) for p in member.iterdir()}
    assert root.stat().st_mode & 0o777 == 0o755
    assert member.stat().st_mode & 0o777 == 0o755
    assert all(p.stat().st_mode & 0o777 == 0o644 for p in member.iterdir())
    assert "ALREADY_READY" in run(*args)
    assert "VERIFY_PASS" in run("--verify", "--db-root", root)
    # Selecting a ready member must not bypass validation of the whole shared root.
    sibling = root / "broken-sibling"
    sibling.mkdir()
    snapshot = {p.name: mod.digest(p) for p in member.iterdir()}
    run(*args, ok=False)
    run(*args, "--force", ok=False)
    assert sibling.is_dir() and not list(sibling.iterdir())
    assert snapshot == {p.name: mod.digest(p) for p in member.iterdir()}
    sibling.rmdir()
    assert "ALREADY_READY" in run(*args)
    # Re-signing an inventory cannot make inconsistent resource identity valid.
    for field, value in (("id", "renamed-v2"), ("size", len(data) + 1),
                         ("sha256", "0" * 64), ("filename", "other.obo"),
                         ("license", "altered-license"), ("url", "http://example.invalid/x")):
        broken = base / ("identity-" + field)
        shutil.copytree(root, broken)
        m = broken / rec["id"]
        changed = dict(rec, **{field: value})
        (m / "recipe.json").write_text(json.dumps(changed))
        (m / "SHA256SUMS").write_text("".join(
            mod.digest(m / name) + "  " + name + "\n"
            for name in sorted(("FORMAT", "recipe.json", "RESOURCE_LICENSE.txt", "tiny.obo"))))
        (m / "READY").write_text(mod.digest(m / "SHA256SUMS") + "\n")
        run("--verify", "--db-root", broken, ok=False)
    network_root = base / "network-denied"
    assert "network disabled" in run("--recipe", recipe, "--db-root", network_root, ok=False)
    assert not network_root.exists()
    # No socket/curl invocation is allowed without explicit opt-in.
    with patch.object(mod.subprocess, "Popen", side_effect=AssertionError("unexpected network")):
        try:
            mod.install(base / "network-mock", rec)
        except ValueError as exc:
            assert "network disabled" in str(exc)
        else:
            raise AssertionError("missing opt-in accepted")
    link = base / "valid-link"
    link.symlink_to(root, target_is_directory=True)
    assert "ALREADY_READY" in run("--recipe", recipe, "--db-root", link)
    badlink = base / "dangling"
    badlink.symlink_to(base / "missing", target_is_directory=True)
    run("--recipe", recipe, "--db-root", badlink, "--archive-dir", source, ok=False)
    assert badlink.is_symlink() and not badlink.exists()
    (member / "tiny.obo").write_bytes(b"corrupt")
    run(*args, "--force", ok=False)
    assert (member / "tiny.obo").read_bytes() == b"corrupt"
    (member / "tiny.obo").write_bytes(data)
    assert before == {p.name: mod.digest(p) for p in member.iterdir()}
    for kind in ("zero", "complete", "bad", "locked", "link"):
        target = base / ("test-" + kind)
        cache = base / ("." + target.name + ".goatools-cache")
        cache.mkdir(mode=0o700)
        partial = cache / (rec["sha256"] + ".partial")
        if kind == "zero":
            partial.touch()
        elif kind == "complete":
            partial.write_bytes(data)
        elif kind == "bad":
            partial.write_bytes(b"X" * len(data))
        elif kind == "link":
            partial.symlink_to(member / "tiny.obo")
        opts = ["--recipe", recipe, "--db-root", target, "--archive-dir", source]
        if kind == "locked":
            with (cache / "install.lock").open("w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                run(*opts, ok=False)
            run(*opts)
        elif kind == "bad":
            run(*opts, ok=False)
            assert not target.exists()
            run(*opts, "--force")
        elif kind == "link":
            run(*opts, "--force", ok=False)
            assert partial.is_symlink()
            continue
        else:
            run(*opts)
        assert "ALREADY_READY" in run(*opts)
        mod.verify_root(target)
        assert not list(cache.glob(".stage-*"))
    # Disk preflight has no installation side effects and does not alter old resources.
    with patch.object(mod.shutil, "disk_usage", return_value=shutil._ntuple_diskusage(1, 1, 0)):
        try:
            mod.install(base / "low-space", rec, source)
        except ValueError as exc:
            assert "disk space" in str(exc)
        else:
            raise AssertionError("space check did not fail")
    assert not (base / "low-space").exists()
    assert before == {p.name: mod.digest(p) for p in member.iterdir()}
    for invalid in ("../escape", ".hidden", "bad/name"):
        bad = dict(rec, id=invalid)
        try:
            mod.recipe_check(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(invalid)
    print("RESOURCE_OFFLINE_TESTS_PASS")
subprocess.run([sys.executable, str(Path(__file__).with_name("test-resource-safety.py"))], check=True)
