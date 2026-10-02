"""Single entry point for the existing, bounded Docker lab proofs."""

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("verify", "isolation", "visibility"),
                        help="verify runs isolation then both visibility rounds")
    parser.add_argument("--context", help="Local Docker context; defaults to the current context")
    build_options = parser.add_mutually_exclusive_group()
    build_options.add_argument("--skip-build", action="store_true", help="Reuse a matching local image")
    build_options.add_argument("--rebuild", action="store_true", help="Rebuild without layer cache and check the base image")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 or newer is required")
    try:
        context = args.context or subprocess.check_output(
            ["docker", "context", "show"], text=True).strip()
        actions = ("isolation", "visibility") if args.action == "verify" else (args.action,)
        for index, action in enumerate(actions):
            script = "check_isolation.py" if action == "isolation" else "run.py"
            command = [sys.executable, "-B", str(ROOT / "lab" / "visibility" / script),
                       "--context", context]
            if args.skip_build or index > 0:
                command.append("--skip-build")
            elif args.rebuild:
                command.append("--rebuild")
            print(f"Running lab {action} proof...", flush=True)
            result = subprocess.run(command, cwd=ROOT)
            if result.returncode:
                return result.returncode if result.returncode > 0 else 1
        print("PASS: requested lab proofs completed.", flush=True)
        return 0
    except FileNotFoundError:
        print("Docker CLI is required; start Docker Desktop and check your PATH.", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    except KeyboardInterrupt:
        # The foreground child receives the same terminal interrupt and performs
        # its own cleanup; do not kill it or claim successful verification.
        print("Interrupted; check the proof report for cleanup status.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
