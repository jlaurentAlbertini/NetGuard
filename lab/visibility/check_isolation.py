"""Verify lab boundaries against disposable live witnesses, then clean up."""

import argparse
import hashlib
import ipaddress
import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from artifacts import proof_lock, reserve
from image import configure_image, prepare_image
from run import HERE, ROOT, check_routes, command, dump


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context")
    build_options = parser.add_mutually_exclusive_group()
    build_options.add_argument("--skip-build", action="store_true", help="Reuse a matching local image")
    build_options.add_argument("--rebuild", action="store_true", help="Rebuild without layer cache and check the base image")
    args = parser.parse_args()
    configure_image()
    context = args.context or command(["docker", "context", "show"]).stdout.strip()
    docker = ["docker", "--context", context]
    endpoint = json.loads(command(docker + ["context", "inspect", context]).stdout)[0]
    if not endpoint["Endpoints"]["docker"]["Host"].startswith("unix://"):
        raise ValueError("A local Docker engine is required")
    if command(docker + ["info", "--format", "{{.OSType}}"] ).stdout.strip() != "linux":
        raise ValueError("A Linux Docker engine is required")
    project = "netguard-isolation-" + secrets.token_hex(4)
    compose = docker + ["compose", "-p", project, "-f", str(HERE / "compose.yaml")]
    network = ipaddress.ip_network(os.environ.get("LAB_SUBNET", "172.30.50.0/24"))
    source = os.environ.get("LAB_SOURCE_IP", "172.30.50.10")
    target = os.environ.get("LAB_TARGET_IP", "172.30.50.20")
    gateway = os.environ.get("LAB_GATEWAY", "172.30.50.1")
    addresses = [ipaddress.ip_address(value) for value in (source, target, gateway)]
    if (network.version != 4 or not network.is_private or len(set(addresses)) != 3
            or any(a not in network or a in (network.network_address, network.broadcast_address) for a in addresses)):
        raise ValueError("Invalid private IPv4 lab addressing")
    os.environ.update(LAB_SUBNET=str(network), LAB_SOURCE_IP=source, LAB_TARGET_IP=target, LAB_GATEWAY=gateway)
    check_routes(network)
    ids = command(docker + ["network", "ls", "-q"]).stdout.split()
    existing = json.loads(command(docker + ["network", "inspect"] + ids).stdout)
    for item in existing:
        for ipam in item["IPAM"].get("Config") or []:
            if ipam.get("Subnet") and ":" not in ipam["Subnet"] and network.overlaps(ipaddress.ip_network(ipam["Subnet"])):
                raise ValueError("Lab subnet overlaps an existing Docker network")
    command(compose + ["config", "--quiet"])
    output = reserve(ROOT, project)
    report = {"status": "running", "checks": [], "cleanup_verified": False}
    fixture_network = project + "-witness"
    fixture_name = project + "-witness"
    fixture_id = None
    host_server = None
    token = secrets.token_hex(8)

    def expect(condition, name, details=None):
        record = {"name": name, "passed": bool(condition)}
        if details is not None:
            record["details"] = details
        report["checks"].append(record)
        dump(output / "report.json", report)
        if not condition:
            raise RuntimeError("Isolation check failed: " + name)

    def helper(container, user, *arguments):
        value = command(docker + ["exec", "--user", user, container, "python3", "/opt/lab/checks.py", *arguments])
        return json.loads(value.stdout)

    def blocked(result):
        return not result["connected"] and (result.get("timeout") or result.get("errno") in (101, 113, 111))

    try:
        report.update(prepare_image(docker, compose, command,
                                    skip_build=args.skip_build, rebuild=args.rebuild))
        command(compose + ["up", "--no-build", "--pull", "never", "-d", "--wait", "--wait-timeout", "30", "target-web", "traffic-generator"])
        target_id = command(compose + ["ps", "-q", "target-web"]).stdout.strip()
        source_id = command(compose + ["ps", "-q", "traffic-generator"]).stdout.strip()
        lab_network = json.loads(command(docker + ["network", "inspect", project + "_monitored"]).stdout)[0]
        expect(lab_network["Internal"] and not lab_network["EnableIPv6"]
               and lab_network["Options"].get("com.docker.network.bridge.gateway_mode_ipv4") == "isolated",
               "internal_isolated_ipv4_network")
        # Separate controlled network; only this fixture has ordinary Docker routing.
        command(docker + ["network", "create", "--label", "netguard.proof=" + project, fixture_network])
        created = command(docker + ["run", "-d", "--name", fixture_name,
                          "--label", "netguard.proof=" + project,
                          "--network", fixture_network, "--add-host", "host.docker.internal:host-gateway",
                          "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                          "--user", "65532:65532", "--memory", "128m", "--cpus", "0.5", "--pids-limit", "32",
                          "--log-opt", "max-size=1m", "--log-opt", "max-file=1",
                          "--entrypoint", "python3", report["image_id"],
                          "/opt/lab/checks.py", "fixture", token])
        fixture_id = created.stdout.strip()
        fixture_info = json.loads(command(docker + ["inspect", fixture_id]).stdout)[0]
        fixture_ip = fixture_info["NetworkSettings"]["Networks"][fixture_network]["IPAddress"]
        deadline = time.monotonic() + 10
        while True:
            result = helper(fixture_id, "65532:65532", "http", fixture_ip, "8080", token)
            if result.get("matched"):
                break
            if time.monotonic() > deadline:
                raise RuntimeError("HTTP witness failed to start")
            time.sleep(0.1)
        expect(result["matched"], "http_witness_positive_control")
        dns_control = helper(fixture_id, "65532:65532", "dns", fixture_ip, "canary.test")
        expect(dns_control.get("answers") == 1, "dns_witness_positive_control")
        expect(helper(source_id, "65532:65532", "health", target)["healthy"], "generator_to_target_http_allowed")
        expect(helper(source_id, "65532:65532", "resolve", "target-web") == target,
               "internal_service_dns_allowed")

        class HostHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(token.encode())
            def log_message(self, *_args):
                pass
        host_server = HTTPServer(("127.0.0.1", 0), HostHandler)
        threading.Thread(target=host_server.serve_forever, daemon=True).start()
        host_port = host_server.server_address[1]
        # Only a locally created listener is used; no existing host service is scanned.
        import http.client
        client = http.client.HTTPConnection("127.0.0.1", host_port, timeout=1)
        client.request("GET", "/canary-" + token)
        response = client.getresponse()
        expect(response.read() == token.encode(), "host_loopback_witness_positive_control")
        client.close()
        host_address = helper(fixture_id, "65532:65532", "resolve", "host.docker.internal")

        for label, container in (("generator", source_id), ("target", target_id)):
            print(f"Checking {label}: permissions, routes, external TCP and DNS...", flush=True)
            info = json.loads(command(docker + ["inspect", container]).stdout)[0]
            config = info["HostConfig"]
            expect(config["ReadonlyRootfs"] and not config["Privileged"] and not config.get("PortBindings")
                   and not info["Mounts"] and config["CapDrop"] == ["ALL"] and not config.get("CapAdd")
                   and config["Dns"] == ["127.0.0.1"] and config["DnsSearch"] == ["."]
                   and "no-new-privileges:true" in config["SecurityOpt"]
                   and set(info["NetworkSettings"]["Networks"]) == {project + "_monitored"},
                   label + "_docker_restrictions")
            expect(config["Memory"] == 128 * 1024 * 1024 and config["NanoCpus"] == 500_000_000
                   and config["PidsLimit"] == 32 and config["LogConfig"]["Config"].get("max-size") == "1m"
                   and config["LogConfig"]["Config"].get("max-file") == "1",
                   label + "_resource_limits")
            permissions = helper(container, "65532:65532", "permissions")
            proc = permissions.pop("process")
            routes = permissions.pop("ipv4_routes")
            expect(all(int(x) == 65532 for x in proc["Uid"].split()) and proc["NoNewPrivs"] == "1"
                   and all(int(proc[key], 16) == 0 for key in ("CapEff", "CapPrm", "CapInh", "CapAmb")),
                   label + "_unprivileged_process")
            expect(all(permissions.values()), label + "_forbidden_operations_blocked", permissions)
            expect(bool(routes) and all(r.get("dst") == str(network) and "gateway" not in r for r in routes),
                   label + "_no_external_route")
            expect(blocked(helper(container, "65532:65532", "http", fixture_ip, "8080", token)),
                   label + "_separate_network_tcp_blocked")
            dns = helper(container, "65532:65532", "dns", fixture_ip, "canary.test")
            expect(not dns["replied"], label + "_separate_network_dns_blocked")
            embedded = helper(container, "65532:65532", "dns", "127.0.0.11", "proof-" + token + ".invalid")
            expect(not embedded.get("answers", 0), label + "_external_name_not_resolved")
            host_result = helper(container, "65532:65532", "http", host_address, str(host_port), token)
            expect(not host_result["connected"] and host_result.get("errno") == 101,
                   label + "_host_route_unreachable")
            gateway_result = helper(container, "65532:65532", "http", gateway, str(host_port), token)
            expect(blocked(gateway_result), label + "_reserved_gateway_unreachable")

        expect(blocked(helper(fixture_id, "65532:65532", "http", target, "8080", token)),
               "other_network_to_target_blocked")
        expect(helper(fixture_id, "65532:65532", "http", fixture_ip, "8080", token)["matched"],
               "http_witness_still_alive")
        expect(helper(fixture_id, "65532:65532", "dns", fixture_ip, "canary.test").get("answers") == 1,
               "dns_witness_still_alive")
        expect(helper(source_id, "65532:65532", "health", target)["healthy"], "target_still_healthy")

        print("Checking capture permissions after privilege drop...", flush=True)
        command(compose + ["up", "--no-build", "--pull", "never", "-d", "capture-probe"])
        probe_id = command(compose + ["ps", "-q", "capture-probe"]).stdout.strip()
        deadline = time.monotonic() + 15
        while True:
            current = command(docker + ["exec", probe_id, "cat", "/capture/status.json"], check=False)
            if current.returncode == 0:
                status = json.loads(current.stdout)
                if status["state"] == "ready":
                    break
            if time.monotonic() > deadline:
                raise RuntimeError("Capture did not become ready")
            time.sleep(0.1)
        probe = json.loads(command(docker + ["inspect", probe_id]).stdout)[0]
        config = probe["HostConfig"]
        expect(config["NetworkMode"] == "container:" + target_id and not config["Privileged"]
               and not config.get("PortBindings") and config["ReadonlyRootfs"]
               and config["CapDrop"] == ["ALL"]
               and {cap.removeprefix("CAP_") for cap in config["CapAdd"]} == {"NET_RAW", "SETUID", "SETGID"}
               and "no-new-privileges:true" in config["SecurityOpt"] and not probe["Mounts"],
               "probe_namespace_and_startup_permissions")
        expect(status["capture_uid"] == status["supervisor_uid"] == 65534
               and int(status["effective_capabilities"], 16) == int(status["supervisor_capabilities"], 16) == 0,
               "probe_privileges_dropped")
        permissions = helper(probe_id, "65534:65534", "permissions")
        proc = permissions.pop("process")
        permissions.pop("ipv4_routes")
        tmpfs_bytes = permissions.pop("capture_tmpfs_bytes")
        expect(all(permissions.values()) and proc["NoNewPrivs"] == "1" and tmpfs_bytes == 8 * 1024 * 1024,
               "probe_permissions_and_tmpfs", permissions)
        expect(config["Memory"] == 128 * 1024 * 1024 and config["NanoCpus"] == 500_000_000
               and config["PidsLimit"] == 32, "probe_resource_limits")
        command(docker + ["kill", "--signal", "SIGTERM", probe_id])
        deadline = time.monotonic() + 5
        while True:
            status = json.loads(command(docker + ["exec", probe_id, "cat", "/capture/status.json"]).stdout)
            if status["state"] == "closed":
                break
            if time.monotonic() > deadline:
                raise RuntimeError("Capture did not close")
            time.sleep(0.1)
        expect(status["exit_code"] == 0 and not status["timed_out"], "probe_graceful_shutdown")
        report["status"] = "passed"
    except (Exception, KeyboardInterrupt) as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        raise
    finally:
        if host_server:
            host_server.shutdown()
            host_server.server_close()
        cleanup_errors = []
        # Attempt every cleanup even if one operation fails. Labels also find a
        # fixture created by Docker before a failed `run` returned its ID.
        try:
            command(compose + ["down", "--timeout", "5"])
        except (Exception, KeyboardInterrupt) as exc:
            cleanup_errors.append(str(exc))
        for resource, removal in (("container", ["rm", "-f"]), ("network", ["network", "rm"])):
            try:
                listing = ["ps", "-aq"] if resource == "container" else ["network", "ls", "-q"]
                owned = command(docker + listing + ["--filter", "label=netguard.proof=" + project]).stdout.split()
                for resource_id in owned:
                    try:
                        command(docker + removal + [resource_id])
                    except (Exception, KeyboardInterrupt) as exc:
                        cleanup_errors.append(str(exc))
            except (Exception, KeyboardInterrupt) as exc:
                cleanup_errors.append(str(exc))
        try:
            remaining = command(docker + ["ps", "-aq", "--filter", "label=com.docker.compose.project=" + project]).stdout.strip()
            witnesses = command(docker + ["ps", "-aq", "--filter", "label=netguard.proof=" + project]).stdout.strip()
            left_networks = command(docker + ["network", "ls", "-q", "--filter", "label=com.docker.compose.project=" + project]).stdout.strip()
            left_witness_networks = command(docker + ["network", "ls", "-q", "--filter", "label=netguard.proof=" + project]).stdout.strip()
            report["cleanup_verified"] = not any((remaining, witnesses, left_networks, left_witness_networks))
        except (Exception, KeyboardInterrupt) as exc:
            cleanup_errors.append(str(exc))
        if cleanup_errors:
            report["cleanup_errors"] = cleanup_errors
        if not report["cleanup_verified"] or cleanup_errors:
            report["status"] = "failed"
        report["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in HERE.iterdir() if p.is_file()}
        dump(output / "report.json", report)
        print("Evidence:", output.relative_to(ROOT), flush=True)
    if report["status"] != "passed":
        raise RuntimeError("Isolation or cleanup failed")
    print(f'PASS: {len(report["checks"])} isolation/permission checks; temporary resources removed.')


if __name__ == "__main__":
    with proof_lock(ROOT):
        main()
