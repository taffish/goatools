#!/usr/bin/env python3
"""Synthetic namespace-race regressions for the installed Linux resource helper."""
import builtins
import hashlib
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import signal
import tempfile
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader("resource_safety", "/usr/local/bin/goatools-resources")
spec = importlib.util.spec_from_loader(loader.name, loader)
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)


def snapshot(path):
    return {str(p.relative_to(path)): mod.digest(p) for p in path.rglob("*") if p.is_file()}


for case in ("before-copy", "after-copy", "closed-output", "cache-parent", "root-parent",
             "ancestor", "stage-symlink", "stage-directory", "destination-race", "partial-hardlink",
             "stage-created-signal"):
    with tempfile.TemporaryDirectory(prefix="goatools-safety-") as tmp:
        base = Path(tmp)
        work = base / "work"
        work.mkdir()
        archive = base / "archive"
        archive.mkdir()
        data = b"synthetic immutable content\n"
        (archive / "tiny.txt").write_bytes(data)
        rec = dict(id="old-v1", version="v1", filename="tiny.txt", size=len(data),
                   sha256=hashlib.sha256(data).hexdigest(), url="https://example.invalid/tiny",
                   license="CC0-1.0", attribution="TAFFISH synthetic fixture")
        root = work / "root"
        cache = work / ".root.goatools-cache"
        mod.install(root, rec, archive)
        old = snapshot(root)
        retained = cache / ".stage-previous"
        retained.mkdir()
        (retained / "keep").write_bytes(b"previous recovery data")
        outside = base / "outside"
        outside.mkdir()
        (outside / "keep").write_bytes(b"outside sentinel")
        new = dict(rec, id="new-v1")
        restore = []
        staged = []
        copy = mod.copy_file
        promote = mod.promote
        printer = builtins.print
        make_stage = mod.tempfile.mkdtemp

        def swap(path, replacement):
            saved = path.with_name(path.name + ".saved")
            path.rename(saved)
            path.symlink_to(replacement, target_is_directory=True)
            restore.append((path, saved))

        def injection(source, dest, exclusive=False):
            if not exclusive:
                return copy(source, dest, exclusive)
            stage = Path(os.readlink(Path(dest).parent))
            staged.append(stage.name)
            if case == "before-copy":
                raise SystemExit(143)
            copy(source, dest, exclusive)
            if case == "after-copy":
                raise SystemExit(130)
            if case == "cache-parent":
                (outside / stage.name).mkdir()
                (outside / stage.name / "keep").write_bytes(b"outside staging sentinel")
                swap(cache, outside)
            elif case == "root-parent":
                swap(root, outside)
            elif case == "ancestor":
                (outside / ".root.goatools-cache" / stage.name).mkdir(parents=True)
                (outside / ".root.goatools-cache" / stage.name / "keep").write_bytes(b"outside staging sentinel")
                swap(work, outside)
            elif case == "stage-symlink":
                swap(stage, outside)
            elif case == "stage-directory":
                saved = stage.with_name(stage.name + ".saved")
                stage.rename(saved)
                stage.mkdir()
                (stage / "keep").write_bytes(b"replacement stage")
                restore.append((stage, saved))
            if case in ("stage-symlink", "stage-directory"):
                raise SystemExit(143)

        def early_signal(*args, **kwargs):
            result = make_stage(*args, **kwargs)
            if case == "stage-created-signal":
                os.kill(os.getpid(), signal.SIGTERM)
            return result

        def publish(cache_fd, name, root_fd, member):
            if case == "destination-race":
                (mod.anchor(root_fd) / member).mkdir()
            return promote(cache_fd, name, root_fd, member)

        def output(*args, **kwargs):
            if case == "closed-output" and args and str(args[0]).startswith("RESOURCE_STAGE staging"):
                raise BrokenPipeError("synthetic closed output")
            return printer(*args, **kwargs)

        if case == "partial-hardlink":
            # A writable cache entry must not truncate an unrelated hardlinked file.
            (cache / (rec["sha256"] + ".download")).unlink()
            os.link(outside / "keep", cache / (rec["sha256"] + ".partial"))
        handler = signal.signal(signal.SIGTERM, mod.interrupted)
        try:
            with patch.object(mod, "copy_file", injection), patch.object(mod, "promote", publish), \
                    patch.object(builtins, "print", output), patch.object(mod.tempfile, "mkdtemp", early_signal):
                mod.install(root, new, archive)
        except (SystemExit, ValueError, OSError) as exc:
            assert str(exc), (case, "missing diagnostic")
        else:
            raise AssertionError((case, "injected failure accepted"))
        finally:
            signal.signal(signal.SIGTERM, handler)
        assert (outside / "keep").read_bytes() == b"outside sentinel", case
        for sentinel in outside.rglob("keep"):
            assert sentinel.read_bytes().startswith(b"outside"), (case, sentinel)
        # Restore only synthetic namespace changes; never ask the helper to erase old data.
        for path, saved in reversed(restore):
            if path.is_symlink():
                path.unlink()
            else:
                assert (path / "keep").read_bytes() == b"replacement stage"
                (path / "keep").unlink()
                path.rmdir()
            saved.rename(path)
        if case == "destination-race":
            assert (root / "new-v1").is_dir() and not list((root / "new-v1").iterdir())
            (root / "new-v1").rmdir()
        if case == "partial-hardlink":
            (cache / (rec["sha256"] + ".partial")).unlink()
        assert old == snapshot(root), case
        assert (retained / "keep").read_bytes() == b"previous recovery data", case
        if case not in ("stage-symlink", "stage-directory"):
            assert sorted(p.name for p in cache.glob(".stage-*")) == [".stage-previous"], case
        else:
            # An identity mismatch is retained with failure, not blindly removed.
            assert all((cache / name).is_dir() for name in staged), case
        retained_snapshot = snapshot(cache)
        mod.install(root, new, archive)
        mod.install(root, new, archive)
        mod.verify_root(root)
        assert old == {"old-v1/" + name: digest
                       for name, digest in snapshot(root / "old-v1").items()}, case
        for name, digest in retained_snapshot.items():
            assert mod.digest(cache / name) == digest, (case, name)
        print("RESOURCE_SAFETY_CASE_PASS", case)
print("RESOURCE_NAMESPACE_SAFETY_PASS 11")

for case in ("success", "existing-empty", "claim-signal", "before-ready", "after-ready", "foreign-child"):
    with tempfile.TemporaryDirectory(prefix="goatools-ready-last-") as tmp:
        base = Path(tmp)
        archive = base / "archive"
        archive.mkdir()
        data = b"synthetic publication\n"
        (archive / "tiny.txt").write_bytes(data)
        rec = dict(id="old-v1", version="v1", filename="tiny.txt", size=len(data),
                   sha256=hashlib.sha256(data).hexdigest(), url="https://example.invalid/tiny",
                   license="CC0-1.0", attribution="TAFFISH synthetic fixture")
        root = base / "root"
        mod.install(root, rec, archive)
        before = snapshot(root / "old-v1")
        new = dict(rec, id="new-v1")
        mkdir = mod.os.mkdir
        link = mod.os.link

        def fallback(cache_fd, stage_name, root_fd, member_name):
            if case == "existing-empty":
                mkdir(member_name, dir_fd=root_fd)
            return False

        def claim(path, *args, **kwargs):
            result = mkdir(path, *args, **kwargs)
            if case == "claim-signal" and path == "new-v1":
                os.kill(os.getpid(), signal.SIGTERM)
            return result

        def publish_link(source, target, **kwargs):
            if target == "READY" and case in ("before-ready", "foreign-child"):
                if case == "foreign-child":
                    (mod.anchor(kwargs["dst_dir_fd"]) / "foreign.txt").write_bytes(b"do not remove")
                raise SystemExit(143)
            result = link(source, target, **kwargs)
            if target == "READY" and case == "after-ready":
                os.kill(os.getpid(), signal.SIGTERM)
            return result

        handler = signal.signal(signal.SIGTERM, mod.interrupted)
        try:
            with patch.object(mod, "promote", fallback), patch.object(mod.os, "mkdir", claim), \
                    patch.object(mod.os, "link", publish_link):
                mod.install(root, new, archive)
        except (SystemExit, ValueError, OSError) as exc:
            assert case != "success" and str(exc), (case, exc)
        else:
            assert case == "success", case
        finally:
            signal.signal(signal.SIGTERM, handler)
        assert snapshot(root / "old-v1") == before, case
        target = root / "new-v1"
        if case in ("success", "after-ready"):
            mod.verify_member(target, new)
        elif case == "foreign-child":
            assert sorted(p.name for p in target.iterdir()) == ["foreign.txt"]
            assert (target / "foreign.txt").read_bytes() == b"do not remove"
            # Explicit test-fixture restoration, not installer cleanup of foreign data.
            (target / "foreign.txt").unlink()
            target.rmdir()
        elif case == "existing-empty":
            assert target.is_dir() and not list(target.iterdir())
            target.rmdir()
        else:
            assert not target.exists(), case
        assert not list((base / ".root.goatools-cache").glob(".stage-*")), case
        with patch.object(mod, "promote", return_value=False):
            mod.install(root, new, archive)
            mod.install(root, new, archive)
        mod.verify_root(root)
        assert snapshot(root / "old-v1") == before, case
        print("RESOURCE_READY_LAST_CASE_PASS", case)
print("RESOURCE_READY_LAST_SAFETY_PASS 6")
