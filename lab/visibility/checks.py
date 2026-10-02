"""Bounded in-container checks and controlled witnesses for isolation proof 1.4."""

import errno
import http.client
import json
import os
import secrets
import socket
import struct
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def dns_packet(name):
    identity = secrets.randbelow(65536)
    question = b"".join(bytes([len(p)]) + p.encode("ascii") for p in name.split("."))
    return identity, struct.pack("!HHHHHH", identity, 0x100, 1, 0, 0, 0) + question + b"\0\0\1\0\1"


def dns_query(address, name):
    identity, query = dns_packet(name)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1)
            sock.sendto(query, (address, 53))
            reply, peer = sock.recvfrom(512)
        if peer[0] != address or len(reply) < 12 or struct.unpack_from("!H", reply)[0] != identity:
            raise ValueError("Invalid DNS witness reply")
        _, flags, _, answers, _, _ = struct.unpack_from("!HHHHHH", reply)
        return {"replied": True, "rcode": flags & 15, "answers": answers}
    except OSError as exc:
        return {"replied": False, "errno": exc.errno, "timeout": isinstance(exc, TimeoutError)}


def http_probe(address, port, token):
    try:
        client = http.client.HTTPConnection(address, port, timeout=1)
        client.request("GET", "/canary-" + token)
        response = client.getresponse()
        body = response.read(256)
        client.close()
        return {"connected": True, "matched": response.status == 200 and body == token.encode()}
    except OSError as exc:
        return {"connected": False, "errno": exc.errno, "timeout": isinstance(exc, TimeoutError)}


def process_status(pid):
    wanted = {"Uid", "Gid", "CapInh", "CapPrm", "CapEff", "CapAmb", "NoNewPrivs"}
    return {key: value.strip() for line in Path(f"/proc/{pid}/status").read_text().splitlines()
            for key, _, value in [line.partition(":")] if key in wanted}


def permissions():
    result = {"process": process_status(1)}
    try:
        with socket.socket(socket.AF_PACKET, socket.SOCK_RAW):
            result["raw_socket_blocked"] = False
    except PermissionError:
        result["raw_socket_blocked"] = True
    try:
        os.setuid(0)
        result["setuid_root_blocked"] = False
    except PermissionError:
        result["setuid_root_blocked"] = True
    path = Path("/tmp/netguard-isolation-check")
    try:
        path.write_text("test")
        result["rootfs_read_only"] = False
        path.unlink()
    except OSError as exc:
        result["rootfs_read_only"] = exc.errno == errno.EROFS
    route = subprocess.run(["ip", "route", "add", "blackhole", "198.51.100.0/24"],
                           capture_output=True, text=True, timeout=2)
    result["route_change_blocked"] = route.returncode != 0 and "Operation not permitted" in route.stderr
    if route.returncode == 0:
        subprocess.run(["ip", "route", "del", "blackhole", "198.51.100.0/24"], capture_output=True)
    result["ipv4_routes"] = json.loads(subprocess.check_output(["ip", "-j", "-4", "route"]))
    result["ipv6_disabled"] = Path("/proc/sys/net/ipv6/conf/all/disable_ipv6").read_text().strip() == "1"
    result["docker_socket_absent"] = not Path("/var/run/docker.sock").exists()
    if Path("/capture").exists():
        stat = os.statvfs("/capture")
        result["capture_tmpfs_bytes"] = stat.f_blocks * stat.f_frsize
    return result


def fixture(token):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = token.encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *_args):
            pass
    def serve_dns():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("0.0.0.0", 53))
            while True:
                data, peer = sock.recvfrom(512)
                if len(data) >= 17 and data[4:6] == b"\0\1":
                    # A synthetic answer, served only by this disposable fixture.
                    reply = data[:2] + struct.pack("!HHHHH", 0x8180, 1, 1, 0, 0) + data[12:]
                    reply += b"\xc0\x0c\0\1\0\1\0\0\0\0\0\4" + socket.inet_aton("192.0.2.123")
                    sock.sendto(reply, peer)
    threading.Thread(target=serve_dns, daemon=True).start()
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "fixture":
        fixture(sys.argv[2])
    elif action == "http":
        print(json.dumps(http_probe(sys.argv[2], int(sys.argv[3]), sys.argv[4])))
    elif action == "dns":
        print(json.dumps(dns_query(sys.argv[2], sys.argv[3])))
    elif action == "permissions":
        print(json.dumps(permissions()))
    elif action == "resolve":
        print(json.dumps(socket.gethostbyname(sys.argv[2])))
    elif action == "health":
        client = http.client.HTTPConnection(sys.argv[2], 8080, timeout=1)
        client.request("GET", "/health")
        response = client.getresponse()
        print(json.dumps({"healthy": response.status == 200 and response.read() == b"ready\n"}))
    else:
        raise SystemExit("Unknown isolation check")
