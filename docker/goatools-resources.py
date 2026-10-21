#!/usr/bin/env python3
"""Install explicit, immutable GO resource members without replacing old data."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")
                if (Path(__file__).resolve().parents[1] / "src/resource_validation.py").is_file()
                else "/opt/goatools/share")
from resource_validation import SCHEMA, digest, recipe_check, valid_data, verify_member, verify_root

CATALOG = Path("/opt/goatools/share/resource-catalog.json")


def ensure_dir(path, mode):
    if path.is_symlink():
        raise ValueError("unexpected directory symlink: " + str(path))
    if path.exists():
        if not path.is_dir():
            raise ValueError("not a directory: " + str(path))
        return
    # Only chmod directories created by this invocation, never an existing parent.
    missing = []
    p = path
    while not p.exists():
        missing.append(p)
        p = p.parent
    for p in reversed(missing):
        p.mkdir(mode=mode)
        p.chmod(mode)


def install(root, rec, archive_dir=None, force=False, allow_network=False):
    member = root / rec["id"]
    # Immutable installs never overwrite even a corrupt or dangling old member.
    if member.exists() or member.is_symlink():
        verify_member(member, rec)
        print("RESOURCE_ALREADY_READY " + rec["id"], flush=True)
        return
    cache = root.parent / ("." + root.name + ".goatools-cache")
    ensure_dir(cache, 0o700)
    if cache.stat().st_uid != os.geteuid() or cache.stat().st_mode & 0o077:
        raise ValueError("download cache must be caller-owned and private (0700)")
    lockpath = cache / "install.lock"
    fd = os.open(lockpath, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    stage = None
    with os.fdopen(fd, "r+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("installation lock is held; retry after the owner exits")
        print("RESOURCE_STAGE locked " + rec["id"], flush=True)
        if member.exists() or member.is_symlink():
            verify_member(member, rec)
            print("RESOURCE_ALREADY_READY " + rec["id"], flush=True)
            return
        if root.exists():
            # Empty new roots are allowed for setup; all existing members must validate.
            for p in root.iterdir():
                verify_member(p)
        blob = cache / (rec["sha256"] + ".download")
        partial = cache / (rec["sha256"] + ".partial")
        for p in (blob, partial):
            if p.is_symlink() or (p.exists() and not p.is_file()):
                raise ValueError("unsafe cache entry: " + str(p))
        if force and partial.exists():
            partial.unlink()
        if blob.exists() and not valid_data(blob, rec):
            if not force:
                raise ValueError("corrupt download cache; use --force to discard only that cache")
            blob.unlink()
        if partial.exists() and partial.stat().st_size >= rec["size"]:
            if valid_data(partial, rec):
                partial.replace(blob)
            elif force:
                partial.unlink()
            else:
                raise ValueError("invalid completed partial; use --force for cache-only reset")
        # Cache and stage share the root parent's filesystem. Reserve peak bytes + 64 MiB.
        need = rec["size"] + (0 if blob.exists() else rec["size"]) + 64 * 1024 * 1024
        if shutil.disk_usage(root.parent).free < need:
            raise ValueError("insufficient disk space: need at least " + str(need) + " free bytes")
        if not blob.exists():
            print("RESOURCE_STAGE download " + rec["id"], flush=True)
            if archive_dir is not None:
                source = archive_dir / rec["filename"]
                if not valid_data(source, rec):
                    raise ValueError("offline archive checksum/size mismatch")
                shutil.copyfile(source, partial)
            else:
                if not allow_network:
                    raise ValueError("network disabled: supply --archive-dir or explicitly add "
                                     "--allow-network for this fixed resource and persistent root")
                # URLs + digests bind content, not indefinite upstream availability.
                # Resume is bounded and always followed by full size/SHA verification.
                cmd = ["curl", "--fail", "--location", "--proto", "=https",
                       "--proto-redir", "=https", "--retry", "2", "--retry-delay", "1",
                       "--connect-timeout", "20", "--max-time", "7200",
                       "--continue-at", "-", "--output", str(partial), rec["url"]]
                child = subprocess.Popen(cmd)
                try:
                    code = child.wait()
                finally:
                    if child.poll() is None:
                        child.terminate()
                        try:
                            child.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            child.kill()
                            child.wait()
                if code:
                    raise ValueError("download failed (curl " + str(code) +
                                     "); partial retained; retry or use --force after inspection")
            if not valid_data(partial, rec):
                raise ValueError("download checksum/size mismatch; partial retained, not installed")
            partial.replace(blob)
        try:
            old_mask = signal.pthread_sigmask(signal.SIG_BLOCK,
                                              {signal.SIGINT, signal.SIGTERM, signal.SIGHUP})
            try:
                stage = Path(tempfile.mkdtemp(prefix=".stage-", dir=cache))
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
            print("RESOURCE_STAGE staging " + rec["id"], flush=True)
            shutil.copyfile(blob, stage / rec["filename"])
            (stage / "FORMAT").write_text(SCHEMA + "\n")
            (stage / "recipe.json").write_text(json.dumps(rec, sort_keys=True, indent=2) + "\n")
            (stage / "RESOURCE_LICENSE.txt").write_text(
                rec["license"] + "\n" + rec["attribution"] + "\n" + rec["url"] + "\n")
            (stage / "SHA256SUMS").write_text("".join(
                digest(p) + "  " + p.name + "\n" for p in sorted(stage.iterdir())))
            (stage / "READY").write_text(digest(stage / "SHA256SUMS") + "\n")
            for p in stage.iterdir():
                p.chmod(0o644)
            stage.chmod(0o755)
            ensure_dir(root, 0o755)
            # Lock serializes this helper; no replacement/deletion of an existing member.
            if member.exists() or member.is_symlink():
                raise ValueError("destination appeared during install; refusing replacement")
            stage.rename(member)
            stage = None
            verify_member(member, rec)
            print("RESOURCE_READY " + str(member), flush=True)
        finally:
            if stage is not None and stage.exists():
                shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource", action="append", help="catalog ID; repeat to select members")
    parser.add_argument("--recipe", type=Path, help="explicit JSON recipe for another fixed member")
    parser.add_argument("--db-root", type=Path, required=True, help="explicit persistent shared root")
    parser.add_argument("--archive-dir", type=Path, help="offline directory of original named files")
    parser.add_argument("--allow-network", action="store_true",
                        help="explicitly allow HTTPS download of selected fixed resources")
    parser.add_argument("--dry-run", action="store_true", help="print exact plan; no writes/network")
    parser.add_argument("--verify", action="store_true", help="verify every installed member offline")
    parser.add_argument("--force", action="store_true",
                        help="discard invalid cache only; NEVER replace/delete an installed member")
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify_root(args.db_root.resolve(strict=True)), indent=2))
        print("RESOURCE_VERIFY_PASS")
        return
    if bool(args.recipe) == bool(args.resource):
        parser.error("choose --resource ID(s) or --recipe FILE explicitly")
    if args.recipe:
        resources = [recipe_check(json.loads(args.recipe.read_text()))]
    else:
        catalog = json.loads(CATALOG.read_text())
        try:
            resources = [recipe_check(catalog[x]) for x in dict.fromkeys(args.resource)]
        except KeyError as exc:
            parser.error("unknown resource " + str(exc) + "; choices: " + ", ".join(catalog))
    plan = {"schema": SCHEMA, "resources": resources, "db_root": str(args.db_root),
            "space_policy": "per-member cache + stage + 64 MiB free on root parent filesystem",
            "network": ("none (--archive-dir)" if args.archive_dir else
                        "explicit HTTPS setup" if args.allow_network else "disabled (cache only)"),
            "concurrency": 1, "force": "cache only; installed members immutable"}
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        return
    # A valid root symlink is resolved physically; a dangling one must never be recreated.
    if args.db_root.is_symlink() and not args.db_root.is_dir():
        raise ValueError("dangling/invalid root symlink")
    root = args.db_root.absolute().resolve()
    if root == Path("/") or root == Path.home() or root == root.parent:
        raise ValueError("choose a dedicated resource subdirectory")
    ensure_dir(root.parent, 0o755)
    for rec in resources:
        install(root, rec, args.archive_dir, args.force, args.allow_network)


def interrupted(signum, _frame):
    raise SystemExit(128 + signum)


if __name__ == "__main__":
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("GOATOOLS_RESOURCE_ERROR " + str(exc), file=sys.stderr, flush=True)
        sys.exit(2)
