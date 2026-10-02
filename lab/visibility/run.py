"""Run the real capture proof twice, then remove only its own Docker resources."""

import argparse
import hashlib
import ipaddress
import json
import os
import platform
import secrets
import subprocess
import sys
import time
from pathlib import Path

from verify_capture import verify_capture
from artifacts import proof_lock, reserve
from image import configure_image, prepare_image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def command(args, *, timeout=60, check=True):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f"Command failed: {args[0]} {args[1]}\n{result.stderr[-2000:]}")
    return result


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def check_routes(network):
    if platform.system() == "Darwin":
        result = command(["netstat", "-rn", "-f", "inet"])
        routes = []
        for line in result.stdout.splitlines():
            fields = line.split()
            if not fields or not fields[0][0].isdigit():
                continue
            address, _, prefix = fields[0].partition("/")
            parts = address.split(".")
            prefix = prefix or str(len(parts) * 8)
            routes.append(".".join(parts + ["0"] * (4 - len(parts))) + "/" + prefix)
    elif platform.system() == "Linux":
        data = json.loads(command(["ip", "-j", "-4", "route", "show", "table", "all"]).stdout)
        routes = [r["dst"] for r in data if r.get("dst") not in (None, "default")]
    else:
        raise RuntimeError("Route preflight supports macOS and Linux only")
    for route in routes:
        other = ipaddress.ip_network(route, strict=False)
        if other.prefixlen and network.overlaps(other):
            raise RuntimeError("Lab subnet overlaps a host route; change LAB_SUBNET and addresses")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", help="Explicit local Docker context")
    build_options = parser.add_mutually_exclusive_group()
    build_options.add_argument("--skip-build", action="store_true", help="Reuse a matching local image")
    build_options.add_argument("--rebuild", action="store_true", help="Rebuild without layer cache and check the base image")
    args = parser.parse_args()
    configure_image()
    context = args.context or command(["docker", "context", "show"]).stdout.strip()
    docker = ["docker", "--context", context]
    project = "netguard-visibility-" + secrets.token_hex(4)
    compose = docker + ["compose", "-p", project, "-f", str(HERE / "compose.yaml")]
    network = ipaddress.ip_network(os.environ.get("LAB_SUBNET", "172.30.50.0/24"))
    source = os.environ.get("LAB_SOURCE_IP", "172.30.50.10")
    target = os.environ.get("LAB_TARGET_IP", "172.30.50.20")
    gateway = os.environ.get("LAB_GATEWAY", "172.30.50.1")
    addresses = [ipaddress.ip_address(a) for a in (source, target, gateway)]
    if (network.version != 4 or not network.is_private or len(set(addresses)) != 3
            or any(a not in network or a in (network.network_address, network.broadcast_address)
                   for a in addresses)):
        raise ValueError("Expected private IPv4 subnet and three distinct usable lab addresses")
    # Freeze the values inspected here so a local .env cannot override preflight.
    os.environ.update(LAB_SUBNET=str(network), LAB_SOURCE_IP=source,
                      LAB_TARGET_IP=target, LAB_GATEWAY=gateway)
    endpoint = json.loads(command(["docker", "context", "inspect", context]).stdout)[0]
    if not endpoint["Endpoints"]["docker"]["Host"].startswith("unix://"):
        raise RuntimeError("This proof requires a local Docker engine via a Unix socket")
    server = json.loads(command(docker + ["version", "--format", "{{json .Server}}"]).stdout)
    if server["Os"] != "linux":
        raise RuntimeError("Linux containers are required")
    check_routes(network)
    ids = command(docker + ["network", "ls", "-q"]).stdout.split()
    if ids:
        for item in json.loads(command(docker + ["network", "inspect"] + ids).stdout):
            for config in item["IPAM"].get("Config") or []:
                subnet = config.get("Subnet")
                if subnet and ":" not in subnet and network.overlaps(ipaddress.ip_network(subnet)):
                    raise RuntimeError("Lab subnet overlaps an existing Docker network")
    command(compose + ["config", "--quiet"])
    output = reserve(ROOT, project)
    report = {"status": "running", "rounds": [], "target_recreated": False,
              "scope": "TCP between the generator and the single target on eth0"}
    dump(output / "report.json", report)
    active = False
    try:
        report.update(prepare_image(docker, compose, command,
                                    skip_build=args.skip_build, rebuild=args.rebuild))
        previous = None
        for number in (1, 2):
            folder = output / f"round-{number}"
            folder.mkdir()
            active = True
            print(f"Round {number}: starting target, generator and capture...", flush=True)
            command(compose + ["up", "--no-build", "--pull", "never", "-d", "--wait", "--wait-timeout", "30",
                               "target-web", "traffic-generator"])
            command(compose + ["up", "--no-build", "--pull", "never", "-d", "capture-probe"])
            target_id = command(compose + ["ps", "-q", "target-web"]).stdout.strip()
            probe_id = command(compose + ["ps", "-q", "capture-probe"]).stdout.strip()
            if previous is not None:
                if previous == target_id:
                    raise RuntimeError("Target was not recreated")
                report["target_recreated"] = True
            previous = target_id
            inspected = json.loads(command(docker + ["inspect", probe_id]).stdout)[0]
            if inspected["HostConfig"]["NetworkMode"] != "container:" + target_id:
                raise RuntimeError("Probe does not share the current target network namespace")
            for container in json.loads(command(docker + ["inspect", target_id, probe_id]).stdout):
                if container["HostConfig"].get("PortBindings"):
                    raise RuntimeError("Unexpected published ports")
            deadline = time.monotonic() + 15
            while True:
                result = command(docker + ["exec", probe_id, "cat", "/capture/status.json"], check=False)
                if result.returncode == 0:
                    status = json.loads(result.stdout)
                    if status["state"] == "ready":
                        break
                if time.monotonic() > deadline:
                    logs = command(compose + ["logs", "--no-color", "capture-probe"]).stdout
                    raise RuntimeError("Capture readiness timeout\n" + logs[-2000:])
                time.sleep(0.1)
            if (int(status["effective_capabilities"], 16) != 0 or status["capture_uid"] != 65534
                    or status["supervisor_uid"] != 65534
                    or int(status["supervisor_capabilities"], 16) != 0):
                raise RuntimeError("tcpdump must drop to nobody with no effective capabilities")
            dump(folder / "capture-status.json", status)
            if number == 1:
                report["packages"] = command(docker + ["exec", probe_id, "apk", "info", "-v"] ).stdout.splitlines()
                report["tcpdump_version"] = command(docker + ["exec", probe_id, "tcpdump", "--version"]).stdout.strip()
            token = secrets.token_hex(8)
            generated = command(compose + ["exec", "-T", "traffic-generator", "python3",
                                          "/opt/lab/roles.py", "generate", token])
            scenario = json.loads(generated.stdout)
            dump(folder / "scenario.json", scenario)
            # Ask the supervisor to flush tcpdump; keep tmpfs mounted for extraction.
            command(docker + ["kill", "--signal", "SIGTERM", probe_id])
            deadline = time.monotonic() + 5
            while True:
                status = json.loads(command(docker + ["exec", probe_id, "cat", "/capture/status.json"]).stdout)
                if status["state"] == "closed":
                    break
                if time.monotonic() > deadline:
                    raise RuntimeError("Capture did not close within its shutdown deadline")
                time.sleep(0.1)
            if status["exit_code"] != 0 or status["timed_out"]:
                raise RuntimeError("Capture ended outside the requested lifecycle")
            dump(folder / "capture-status.json", status)
            for name in ("capture.pcap", "tcpdump.log"):
                # docker cp does not reliably archive tmpfs; stream the file before teardown.
                with (folder / name).open("wb") as destination:
                    extracted = subprocess.run(
                        docker + ["exec", "--user", "65534:65534", probe_id, "cat", f"/capture/{name}"],
                        stdout=destination, stderr=subprocess.PIPE, timeout=10)
                if extracted.returncode:
                    raise RuntimeError("Cannot extract capture artifact: " + extracted.stderr.decode())
            result = verify_capture(folder / "capture.pcap", scenario, folder / "tcpdump.log")
            dump(folder / "verification.json", result)
            report["rounds"].append(result)
            dump(output / "report.json", report)
            print(f"Round {number}: capture verified.", flush=True)
            command(compose + ["down", "--timeout", "5"])
            active = False
        report["status"] = "passed"
    except (Exception, KeyboardInterrupt) as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        raise
    finally:
        report["cleanup_verified"] = False
        try:
            if active:
                cleanup = command(compose + ["down", "--timeout", "5"], check=False)
                if cleanup.returncode:
                    report["status"] = "failed"
                    report["cleanup_error"] = cleanup.stderr[-2000:]
            remaining = command(docker + ["ps", "-aq", "--filter", f"label=com.docker.compose.project={project}"])
            networks = command(docker + ["network", "ls", "-q", "--filter", f"label=com.docker.compose.project={project}"])
            report["cleanup_verified"] = not remaining.stdout.strip() and not networks.stdout.strip()
        except (Exception, KeyboardInterrupt) as exc:
            report["cleanup_error"] = str(exc)
        if not report["cleanup_verified"]:
            report["status"] = "failed"
        report["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in HERE.iterdir() if p.is_file()}
        dump(output / "report.json", report)
        print(f"Evidence: {output.relative_to(ROOT)}", flush=True)
    if report["status"] != "passed":
        raise RuntimeError("Proof or cleanup failed; see local report")
    print("PASS: both captures and target recreation verified; lab resources removed.")


if __name__ == "__main__":
    with proof_lock(ROOT):
        main()
