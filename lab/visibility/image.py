"""Build a versioned image and reject stale images before starting the lab."""

import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = "netguard-lab:1.5"
SOURCE_LABEL = "org.netguard.lab.sources-sha256"
IMAGE_FILES = ("Dockerfile", ".dockerignore", "packages.lock", "roles.py", "checks.py")


def source_fingerprint():
    entries = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in IMAGE_FILES}
    return hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()


def configure_image():
    # Freeze these values so Compose's .env cannot silently select another image.
    os.environ["LAB_IMAGE_REF"] = IMAGE
    os.environ["LAB_SOURCE_SHA256"] = source_fingerprint()


def prepare_image(docker, compose, command, *, skip_build=False, rebuild=False):
    expected = source_fingerprint()
    if not skip_build:
        options = ["--no-cache", "--pull"] if rebuild else []
        print("Building the locked lab image...", flush=True)
        command(compose + ["build", *options, "target-web"], timeout=600)
    found = command(docker + ["image", "inspect", IMAGE], check=False)
    if found.returncode:
        raise RuntimeError("Lab image is missing; rerun without --skip-build")
    info = json.loads(found.stdout)[0]
    if (info["Config"].get("Labels") or {}).get(SOURCE_LABEL) != expected:
        raise RuntimeError("Lab image does not match current sources; rerun without --skip-build")
    if source_fingerprint() != expected:
        raise RuntimeError("Image sources changed during preparation; rerun the proof")
    # Compose services and the witness use this immutable local image ID.
    os.environ["LAB_IMAGE_REF"] = info["Id"]
    return {"image_id": info["Id"], "image_sources_sha256": expected,
            "image_platform": info["Os"] + "/" + info["Architecture"],
            "package_lock_sha256": hashlib.sha256((HERE / "packages.lock").read_bytes()).hexdigest()}
