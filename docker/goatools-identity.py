"""Check exact runtime identity and the command's exit status without a pipe."""
import importlib.metadata
import subprocess
import sys

EXPECTED = "1.6.8"


def check(result):
    if result.returncode != 0 or result.stdout.splitlines() != [EXPECTED]:
        raise ValueError(f"GOATOOLS_IDENTITY_FAIL exit={result.returncode} "
                         f"stdout={result.stdout!r} stderr={result.stderr!r}")


if __name__ == "__main__":
    import goatools
    try:
        check(subprocess.run(["goatools", "--version"], capture_output=True,
                             text=True, timeout=60))
        if goatools.__version__ != EXPECTED or importlib.metadata.version("goatools") != EXPECTED:
            raise ValueError("GOATOOLS_IDENTITY_FAIL module/metadata mismatch")
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print("GOATOOLS_IDENTITY_PASS " + EXPECTED)
