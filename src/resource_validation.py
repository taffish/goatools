#!/usr/bin/env python3
"""One offline resource identity contract for the host wrapper and installer."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

SCHEMA = "taffish.goatools.resource.v1"
SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,150}\Z")
RESERVED = {"FORMAT", "recipe.json", "RESOURCE_LICENSE.txt", "SHA256SUMS", "READY"}


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def recipe_check(rec):
    if not isinstance(rec, dict):
        raise ValueError("recipe must be an object")
    for key in ("id", "version", "filename", "url", "sha256", "license", "attribution"):
        if not isinstance(rec.get(key), str) or not rec[key].strip():
            raise ValueError("missing recipe field: " + key)
    if not SAFE.fullmatch(rec["id"]) or not SAFE.fullmatch(rec["filename"]):
        raise ValueError("unsafe resource ID/filename")
    if rec["filename"] in RESERVED:
        raise ValueError("reserved filename")
    if not re.fullmatch("[a-f0-9]{64}", rec["sha256"]):
        raise ValueError("recipe SHA256 must be lowercase hexadecimal")
    if type(rec.get("size")) is not int or rec["size"] <= 0:
        raise ValueError("recipe size must be a positive byte count")
    u = urlsplit(rec["url"])
    if u.scheme != "https" or not u.netloc or u.username or u.password or u.fragment:
        raise ValueError("resource URL must be HTTPS without credentials/fragment")
    return rec


def regular(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("not a regular file: " + str(path))


def valid_data(path, rec):
    regular(path)
    return path.stat().st_size == rec["size"] and digest(path) == rec["sha256"]


def verify_member(member, expected=None):
    if member.is_symlink() or not member.is_dir():
        raise ValueError("invalid member directory: " + str(member))
    for name in RESERVED:
        regular(member / name)
    rec = recipe_check(json.loads((member / "recipe.json").read_text(encoding="utf-8")))
    if expected is not None and rec != expected:
        raise ValueError("existing resource recipe differs; choose a new root/ID")
    if member.name != rec["id"] or (member / "FORMAT").read_text() != SCHEMA + "\n":
        raise ValueError("resource schema/ID mismatch")
    if set(p.name for p in member.iterdir()) != RESERVED | {rec["filename"]}:
        raise ValueError("unexpected/missing files in resource")
    if (member / "READY").read_text() != digest(member / "SHA256SUMS") + "\n":
        raise ValueError("invalid READY receipt")
    lines = (member / "SHA256SUMS").read_text().splitlines()
    expected_names = {"FORMAT", "recipe.json", "RESOURCE_LICENSE.txt", rec["filename"]}
    seen = set()
    for line in lines:
        match = re.fullmatch(r"([a-f0-9]{64})  ([A-Za-z0-9][A-Za-z0-9._-]{0,150})", line)
        if not match or match[2] not in expected_names or match[2] in seen:
            raise ValueError("invalid inventory")
        path = member / match[2]
        regular(path)
        if digest(path) != match[1]:
            raise ValueError("inventory checksum mismatch: " + match[2])
        seen.add(match[2])
    if seen != expected_names or not valid_data(member / rec["filename"], rec):
        raise ValueError("resource content mismatch")
    if (member / "RESOURCE_LICENSE.txt").read_text(encoding="utf-8") != (
            rec["license"] + "\n" + rec["attribution"] + "\n" + rec["url"] + "\n"):
        raise ValueError("resource license/source mismatch")
    return rec


def verify_root(root):
    if not root.is_dir():
        raise ValueError("missing resource root")
    members = list(root.iterdir())
    if not members:
        raise ValueError("empty resource root")
    return [verify_member(p) for p in sorted(members)]


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("usage: resource_validation.py ROOT")
        verify_root(Path(sys.argv[1]).resolve(strict=True))
    except (ValueError, OSError) as exc:
        print("GOATOOLS_RESOURCE_ERROR " + str(exc), file=sys.stderr)
        sys.exit(2)
