"""Small, bounded traffic/capture helpers for the lab; no NetGuard domain code."""

import http.client
import ipaddress
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = b"ready\n"
        elif re.fullmatch(r"/proof-[a-f0-9]{16}", self.path):
            body = ("netguard-proof:" + self.path.removeprefix("/proof-")).encode()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def endpoints():
    source = ipaddress.IPv4Address(os.environ["LAB_SOURCE_IP"])
    target = ipaddress.IPv4Address(os.environ["LAB_TARGET_IP"])
    if not (source.is_private and target.is_private) or source == target:
        raise ValueError("Expected distinct private lab endpoints")
    return str(source), str(target)


def generate(token):
    if not re.fullmatch(r"[a-f0-9]{16}", token):
        raise ValueError("Invalid proof token")
    source, target = endpoints()
    result = {"token": token, "source_ip": source, "target_ip": target,
              "http_port": 8080, "closed_ports": [8000, 8001, 8002],
              "started_at": time.time()}
    client = http.client.HTTPConnection(target, 8080, timeout=2,
                                        source_address=(source, 0))
    client.request("GET", "/proof-" + token)
    response = client.getresponse()
    body = response.read()
    if response.status != 200 or body != ("netguard-proof:" + token).encode():
        raise RuntimeError("Unexpected HTTP proof response")
    client.close()
    for port in result["closed_ports"]:
        with socket.socket() as sock:
            sock.settimeout(1)
            sock.bind((source, 0))
            try:
                sock.connect((target, port))
            except ConnectionRefusedError:
                continue
            raise RuntimeError(f"Port {port} must refuse the connection")
    result["finished_at"] = time.time()
    print(json.dumps(result), flush=True)


def write_status(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value))
    temporary.replace(path)


def capture():
    source, target = endpoints()
    interface = os.environ["LAB_INTERFACE"]
    info = json.loads(subprocess.check_output(
        ["ip", "-j", "-4", "addr", "show", "dev", interface]))
    if not any(a["local"] == target for i in info for a in i["addr_info"]):
        raise RuntimeError("Capture interface does not carry the target address")
    folder = Path("/capture")
    log_path = folder / "tcpdump.log"
    status_path = folder / "status.json"
    capture_filter = f"tcp and host {source} and host {target}"
    command = ["tcpdump", "--immediate-mode", "-i", interface, "-p", "-nn", "-U", "-s", "0",
               "-c", "512", "-Z", "nobody", "-w", str(folder / "capture.pcap"),
               capture_filter]
    done = threading.Event()
    def stop(_signum, _frame):
        done.set()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with log_path.open("w") as log:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=log)
        deadline = time.monotonic() + 10
        while f"listening on {interface}," not in log_path.read_text():
            if process.poll() is not None or time.monotonic() > deadline or done.is_set():
                process.terminate()
                process.wait(timeout=3)
                raise RuntimeError("Capture failed before readiness: " + log_path.read_text())
            time.sleep(0.05)
        proc_status = Path(f"/proc/{process.pid}/status").read_text()
        capabilities = next(line.split()[1] for line in proc_status.splitlines()
                            if line.startswith("CapEff:"))
        # Same unprivileged UID as tcpdump permits graceful signalling without KILL.
        os.setgroups([65534])
        os.setgid(65534)
        os.setuid(65534)
        own_status = Path("/proc/self/status").read_text()
        own_capabilities = next(line.split()[1] for line in own_status.splitlines()
                                if line.startswith("CapEff:"))
        status = {"state": "ready", "interface": interface, "target_ip": target,
                  "supervisor_uid": os.getuid(),
                  "supervisor_capabilities": own_capabilities,
                  "capture_uid": int(next(line.split()[1] for line in proc_status.splitlines()
                                          if line.startswith("Uid:"))),
                  "effective_capabilities": capabilities,
                  "promiscuous": False, "filter": capture_filter,
                  "max_packets": 512, "max_seconds": 30}
        write_status(status_path, status)
        print("capture ready", flush=True)
        deadline = time.monotonic() + 30
        while process.poll() is None and not done.is_set() and time.monotonic() < deadline:
            time.sleep(0.05)
        timed_out = not done.is_set()
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        process.wait(timeout=3)
    status.update(state="closed", exit_code=process.returncode, timed_out=timed_out)
    write_status(status_path, status)
    if process.returncode != 0 or timed_out:
        raise RuntimeError("Capture ended unexpectedly or exceeded its time/packet budget")
    # Keep tmpfs mounted until the runner has copied the proof, then stop the container.
    while True:
        time.sleep(1)


if __name__ == "__main__":
    role = sys.argv[1]
    if role == "target":
        HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
    elif role == "health":
        client = http.client.HTTPConnection("127.0.0.1", 8080, timeout=1)
        client.request("GET", "/health")
        if client.getresponse().status != 200:
            raise SystemExit(1)
    elif role == "generate":
        generate(sys.argv[2])
    elif role == "capture":
        capture()
    elif role == "idle":
        while True:
            time.sleep(60)
    else:
        raise SystemExit("Unknown lab role")
