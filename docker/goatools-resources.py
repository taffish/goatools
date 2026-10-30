#!/usr/bin/env python3
"""Install explicit, immutable GO resource members without replacing old data."""
import argparse
from contextlib import ExitStack, contextmanager
import ctypes
import errno
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import stat
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


@contextmanager
def directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        yield fd
    finally:
        os.close(fd)


def anchor(fd):
    # The installer runs inside Linux containers; host discovery remains portable.
    path = Path("/proc/self/fd") / str(fd)
    if not path.is_dir():
        raise ValueError("resource installation requires Linux /proc/self/fd")
    return path


def same_directory(path, fd):
    entry = path.lstat()
    opened = os.fstat(fd)
    if not stat.S_ISDIR(entry.st_mode) or (entry.st_dev, entry.st_ino) != (opened.st_dev, opened.st_ino):
        raise ValueError("resource directory changed during installation: " + str(path))


def copy_file(source, target, exclusive=False):
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    flags |= os.O_EXCL if exclusive else 0
    fd = os.open(target, flags, 0o600)
    with os.fdopen(fd, "wb") as dst, open(source, "rb") as src:
        info = os.fstat(dst.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("unexpected download file type")
        os.ftruncate(dst.fileno(), 0)
        shutil.copyfileobj(src, dst, 1024 * 1024)


def write_new(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(text)


def promote(cache_fd, stage_name, root_fd, member_name):
    # Unlike rename(), RENAME_NOREPLACE cannot replace even an empty old directory.
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        return False
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(cache_fd, os.fsencode(stage_name), root_fd, os.fsencode(member_name), 1):
        code = ctypes.get_errno()
        if code == errno.EEXIST:
            raise ValueError("destination appeared during install; refusing replacement")
        if code in (errno.EINVAL, errno.ENOSYS, errno.EOPNOTSUPP):
            return False
        raise OSError(code, os.strerror(code))
    return True


def publish_ready(stage_fd, root_fd, member_name, unchanged):
    # Some host shares (including gRPC FUSE) lack RENAME_NOREPLACE. Claim a new
    # directory exclusively, then hardlink immutable files and commit READY last.
    # Readers always require the complete READY/inventory contract. Old names
    # are never replaced; rollback unlinks only files created by this invocation.
    # Reopen the pinned directory stream: some rootless runtimes return an empty
    # list for a descriptor opened before its files were created. Do not weaken
    # READY validation or fall back to an unpinned logical pathname.
    names = sorted(os.listdir(anchor(stage_fd)), key=lambda n: (n == "READY", n))
    if "READY" not in names:
        raise ValueError("staged READY missing; publication not started")
    created = []
    dest_fd = None
    committed = False
    blocked = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP}
    try:
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, blocked)
        try:
            os.mkdir(member_name, 0o700, dir_fd=root_fd)
            dest_fd = os.open(member_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=root_fd)
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        dest = anchor(dest_fd)
        same_directory(anchor(root_fd) / member_name, dest_fd)
        if list(dest.iterdir()):
            raise ValueError("publication directory unexpectedly nonempty; retained")
        for name in names:
            unchanged()
            same_directory(anchor(root_fd) / member_name, dest_fd)
            source = os.stat(name, dir_fd=stage_fd, follow_symlinks=False)
            if not stat.S_ISREG(source.st_mode):
                raise ValueError("unexpected staged file type")
            if name == "READY":
                os.fchmod(dest_fd, 0o755)
            old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, blocked)
            try:
                os.link(name, name, src_dir_fd=stage_fd, dst_dir_fd=dest_fd, follow_symlinks=False)
                created.append((name, source.st_dev, source.st_ino))
                if name == "READY":
                    committed = True
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        if not committed:
            raise ValueError("staged READY missing; publication not committed")
    finally:
        if dest_fd is not None:
            try:
                if not committed:
                    for name, dev, ino in reversed(created):
                        entry = os.stat(name, dir_fd=dest_fd, follow_symlinks=False)
                        if (entry.st_dev, entry.st_ino) != (dev, ino):
                            raise ValueError("publication file changed; retained for inspection")
                        os.unlink(name, dir_fd=dest_fd)
                    same_directory(anchor(root_fd) / member_name, dest_fd)
                    # A foreign child makes rmdir fail instead of being removed.
                    os.rmdir(member_name, dir_fd=root_fd)
            finally:
                os.close(dest_fd)


def cleanup_stage(cache_fd, stage_name, stage_fd):
    entry = os.stat(stage_name, dir_fd=cache_fd, follow_symlinks=False)
    owned = os.fstat(stage_fd)
    if not stat.S_ISDIR(entry.st_mode) or (entry.st_dev, entry.st_ino) != (owned.st_dev, owned.st_ino):
        raise ValueError("staging identity changed; retained for inspection")
    # dir_fd pins the original cache, even if its pathname/parent becomes a symlink.
    if not shutil.rmtree.avoids_symlink_attacks:
        raise ValueError("safe descriptor-relative staging cleanup unavailable")
    shutil.rmtree(stage_name, dir_fd=cache_fd)


def install(root, rec, archive_dir=None, force=False, allow_network=False):
    logical_root = root.absolute()
    with ExitStack() as handles:
        parent_fd = handles.enter_context(directory(logical_root.parent))
        root = anchor(parent_fd) / logical_root.name
        root_fd = handles.enter_context(directory(root)) if root.exists() or root.is_symlink() else None
        cache_name = "." + logical_root.name + ".goatools-cache"
        cache_fd = None

        def unchanged():
            same_directory(logical_root.parent, parent_fd)
            if root_fd is not None:
                same_directory(root, root_fd)
            if cache_fd is not None:
                same_directory(anchor(parent_fd) / cache_name, cache_fd)

        def resource_root():
            nonlocal root_fd
            if root_fd is None:
                ensure_dir(root, 0o755)
                root_fd = handles.enter_context(directory(root))
            unchanged()
            return root_fd

        # Never follow a replaced resource-root directory during reads or publication.
        current_root = anchor(root_fd) if root_fd is not None else root
        member = current_root / rec["id"]
        if root_fd is not None:
            for existing in current_root.iterdir():
                verify_member(existing)
        unchanged()
        if member.exists() or member.is_symlink():
            verify_member(member, rec)
            unchanged()
            print("RESOURCE_ALREADY_READY " + rec["id"], flush=True)
            return
        cache_path = anchor(parent_fd) / cache_name
        ensure_dir(cache_path, 0o700)
        cache_fd = handles.enter_context(directory(cache_path))
        info = os.fstat(cache_fd)
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError("download cache must be caller-owned and private (0700)")
        unchanged()
        _install(current_root, rec, archive_dir, force, allow_network, cache_fd,
                 resource_root, unchanged, logical_root)


def _install(root, rec, archive_dir, force, allow_network, cache_fd, resource_root,
             unchanged, logical_root):
    member = root / rec["id"]
    # Reuse and new installs apply the same complete-root identity check as discovery.
    # Do not let a valid selected member hide a corrupt or symlinked sibling.
    if root.exists():
        for existing in root.iterdir():
            verify_member(existing)
    # Immutable installs never overwrite even a corrupt or dangling old member.
    if member.exists() or member.is_symlink():
        verify_member(member, rec)
        print("RESOURCE_ALREADY_READY " + rec["id"], flush=True)
        return
    cache = anchor(cache_fd)
    lockpath = cache / "install.lock"
    fd = os.open(lockpath, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    stage = None
    stage_fd = None
    stage_name = None
    with os.fdopen(fd, "r+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("installation lock is held; retry after the owner exits")
        info = os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
            raise ValueError("unsafe installation lock")
        unchanged()
        print("RESOURCE_STAGE locked " + rec["id"], flush=True)
        if root.exists():
            # Empty new roots are allowed for setup; all existing members must validate.
            for p in root.iterdir():
                verify_member(p)
        if member.exists() or member.is_symlink():
            verify_member(member, rec)
            unchanged()
            print("RESOURCE_ALREADY_READY " + rec["id"], flush=True)
            return
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
        if shutil.disk_usage(cache).free < need:
            raise ValueError("insufficient disk space: need at least " + str(need) + " free bytes")
        if not blob.exists():
            print("RESOURCE_STAGE download " + rec["id"], flush=True)
            if archive_dir is not None:
                source = archive_dir / rec["filename"]
                if not valid_data(source, rec):
                    raise ValueError("offline archive checksum/size mismatch")
                copy_file(source, partial)
            else:
                if not allow_network:
                    raise ValueError("network disabled: supply --archive-dir or explicitly add "
                                     "--allow-network for this fixed resource and persistent root")
                # URLs + digests bind content, not indefinite upstream availability.
                # Resume is bounded and always followed by full size/SHA verification.
                download_fd = os.open(partial, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
                cmd = ["curl", "--fail", "--location", "--proto", "=https",
                       "--proto-redir", "=https", "--retry", "2", "--retry-delay", "1",
                       "--connect-timeout", "20", "--max-time", "7200",
                       "--continue-at", "-", "--output", "/proc/self/fd/" + str(download_fd), rec["url"]]
                child = None
                try:
                    info = os.fstat(download_fd)
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                        raise ValueError("unexpected partial file type")
                    child = subprocess.Popen(cmd, pass_fds=(download_fd,))
                    code = child.wait()
                finally:
                    if child is not None and child.poll() is None:
                        child.terminate()
                        try:
                            child.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            child.kill()
                            child.wait()
                    os.close(download_fd)
                if code:
                    raise ValueError("download failed (curl " + str(code) +
                                     "); partial retained; retry or use --force after inspection")
            if not valid_data(partial, rec):
                raise ValueError("download checksum/size mismatch; partial retained, not installed")
            partial.replace(blob)
        try:
            unchanged()
            old_mask = signal.pthread_sigmask(signal.SIG_BLOCK,
                                              {signal.SIGINT, signal.SIGTERM, signal.SIGHUP})
            try:
                stage_path = Path(tempfile.mkdtemp(prefix=".stage-", dir=cache))
                stage_name = stage_path.name
                stage_fd = os.open(stage_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                stage = anchor(stage_fd)
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
            print("RESOURCE_STAGE staging " + rec["id"], flush=True)
            copy_file(blob, stage / rec["filename"], exclusive=True)
            write_new(stage / "FORMAT", SCHEMA + "\n")
            write_new(stage / "recipe.json", json.dumps(rec, sort_keys=True, indent=2) + "\n")
            write_new(stage / "RESOURCE_LICENSE.txt",
                      rec["license"] + "\n" + rec["attribution"] + "\n" + rec["url"] + "\n")
            write_new(stage / "SHA256SUMS", "".join(
                digest(p) + "  " + p.name + "\n" for p in sorted(stage.iterdir())))
            write_new(stage / "READY", digest(stage / "SHA256SUMS") + "\n")
            for p in stage.iterdir():
                item_fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
                try:
                    if not stat.S_ISREG(os.fstat(item_fd).st_mode):
                        raise ValueError("unexpected staged file type")
                    os.fchmod(item_fd, 0o644)
                finally:
                    os.close(item_fd)
            os.fchmod(stage_fd, 0o755)
            root_fd = resource_root()
            root = anchor(root_fd)
            member = root / rec["id"]
            # Lock serializes this helper; no replacement/deletion of an existing member.
            if member.exists() or member.is_symlink():
                raise ValueError("destination appeared during install; refusing replacement")
            unchanged()
            old_mask = signal.pthread_sigmask(signal.SIG_BLOCK,
                                              {signal.SIGINT, signal.SIGTERM, signal.SIGHUP})
            try:
                renamed = promote(cache_fd, stage_name, root_fd, rec["id"])
                if renamed:
                    stage_name = None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
            if not renamed:
                print("RESOURCE_PUBLICATION ready-last " + rec["id"], flush=True)
                publish_ready(stage_fd, root_fd, rec["id"], unchanged)
            verify_member(member, rec)
            unchanged()
            print("RESOURCE_READY " + str(logical_root / rec["id"]), flush=True)
        finally:
            try:
                if stage_name is not None and stage_fd is not None:
                    cleanup_stage(cache_fd, stage_name, stage_fd)
                unchanged()
            finally:
                if stage_fd is not None:
                    os.close(stage_fd)


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
