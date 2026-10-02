#!/usr/bin/env python3
"""Verify the bounded visibility experiment without external dependencies.

This deliberately supports classic Ethernet/IPv4/TCP PCAPs only. It is a
laboratory acceptance check, not the NetGuard packet parser or detection Core.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
from pathlib import Path
import re
import struct


_MAGIC = {
    b"\xd4\xc3\xb2\xa1": ("<", 1_000_000),
    b"\xa1\xb2\xc3\xd4": (">", 1_000_000),
    b"\x4d\x3c\xb2\xa1": ("<", 1_000_000_000),
    b"\xa1\xb2\x3c\x4d": (">", 1_000_000_000),
}
_MAX_PACKETS = 512
_MAX_FILE_BYTES = 8 * 1024 * 1024
_MAX_STREAM_BYTES = 128 * 1024


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _read_bounded(path: str | Path, limit: int) -> bytes:
    try:
        with Path(path).open("rb") as handle:
            contents = handle.read(limit + 1)
    except OSError as exc:
        raise ValueError(f"Cannot read proof artifact: {exc.strerror}") from exc
    _require(len(contents) <= limit, "Proof artifact exceeds its verification limit")
    return contents


def _parse_pcap(data: bytes) -> tuple[list[dict], list[float], int]:
    _require(len(data) >= 24, "Truncated PCAP global header")
    _require(data[:4] in _MAGIC, "Unsupported format: classic PCAP required")
    endian, resolution = _MAGIC[data[:4]]
    major, minor, _, _, snaplen, linktype = struct.unpack(endian + "HHiIII", data[4:24])
    _require((major, minor) == (2, 4), "Unsupported PCAP version")
    _require(linktype == 1, "Ethernet PCAP linktype 1 required")
    _require(snaplen > 0, "Invalid PCAP snapshot length")
    offset = 24
    tcp_packets: list[dict] = []
    timestamps: list[float] = []
    housekeeping = 0
    while offset < len(data):
        _require(len(timestamps) < _MAX_PACKETS, "Capture exceeds 512 packets")
        _require(len(data) - offset >= 16, "Truncated PCAP record header")
        seconds, fraction, captured, original = struct.unpack_from(endian + "IIII", data, offset)
        offset += 16
        _require(fraction < resolution, "Invalid PCAP timestamp fraction")
        _require(0 < captured <= snaplen, "Invalid captured packet length")
        _require(captured == original, "A packet was truncated by the capture snapshot")
        _require(captured <= len(data) - offset, "Truncated PCAP packet record")
        frame = data[offset : offset + captured]
        offset += captured
        timestamp = seconds + fraction / resolution
        _require(timestamp > 0, "Invalid PCAP timestamp")
        timestamps.append(timestamp)
        _require(len(frame) >= 14, "Truncated Ethernet header")
        ether_type = struct.unpack_from("!H", frame, 12)[0]
        layer3 = 14
        while ether_type in (0x8100, 0x88A8):
            _require(layer3 <= 22, "Excessive Ethernet VLAN nesting")
            _require(len(frame) >= layer3 + 4, "Truncated VLAN header")
            ether_type = struct.unpack_from("!H", frame, layer3 + 2)[0]
            layer3 += 4
        if ether_type != 0x0800:
            housekeeping += 1
            continue
        ip = frame[layer3:]
        _require(len(ip) >= 20, "Truncated IPv4 header")
        _require(ip[0] >> 4 == 4, "Invalid IPv4 version")
        header_length = (ip[0] & 15) * 4
        total_length = struct.unpack_from("!H", ip, 2)[0]
        _require(20 <= header_length <= total_length <= len(ip), "Truncated or invalid IPv4 packet")
        if ip[9] != 6:
            housekeeping += 1
            continue
        fragment = struct.unpack_from("!H", ip, 6)[0]
        _require(fragment & 0x3FFF == 0, "Fragmented TCP is outside this proof's scope")
        tcp = ip[header_length:total_length]
        _require(len(tcp) >= 20, "Truncated TCP header")
        tcp_header_length = (tcp[12] >> 4) * 4
        _require(20 <= tcp_header_length <= len(tcp), "Truncated or invalid TCP options")
        source_port, target_port, sequence, acknowledgement = struct.unpack_from("!HHII", tcp)
        tcp_packets.append({
            "timestamp": timestamp,
            "source_ip": str(ipaddress.IPv4Address(ip[12:16])),
            "target_ip": str(ipaddress.IPv4Address(ip[16:20])),
            "source_port": source_port,
            "target_port": target_port,
            "sequence": sequence,
            "acknowledgement": acknowledgement,
            "flags": tcp[13],
            "payload": tcp[tcp_header_length:],
        })
    _require(bool(timestamps), "PCAP contains no packets")
    return tcp_packets, timestamps, housekeeping


def _next(sequence: int) -> int:
    return (sequence + 1) & 0xFFFFFFFF


def _stream(packets: list[dict], initial_sequence: int) -> bytes:
    """Reassemble a small directional stream; accept consistent retransmissions."""
    pieces: dict[int, int] = {}
    for packet in packets:
        payload = packet["payload"]
        if not payload:
            continue
        relative = (packet["sequence"] - initial_sequence) & 0xFFFFFFFF
        _require(relative < _MAX_STREAM_BYTES, "TCP payload sequence lies outside bounded stream")
        _require(relative + len(payload) <= _MAX_STREAM_BYTES, "TCP stream exceeds proof limit")
        for position, byte in enumerate(payload, relative):
            _require(position not in pieces or pieces[position] == byte, "Conflicting TCP retransmission")
            pieces[position] = byte
    if not pieces:
        return b""
    _require(len(pieces) == max(pieces) + 1, "TCP payload has a capture gap")
    return bytes(pieces[position] for position in range(len(pieces)))


def _verify_http(packets: list[dict], source: str, target: str, port: int, token: str) -> dict:
    failures: list[str] = []
    candidates = [p for p in packets if p["source_ip"] == source and p["target_ip"] == target
                  and p["target_port"] == port and p["flags"] & 0x17 == 0x02]
    for syn in candidates:
        try:
            source_port = syn["source_port"]
            outbound = [p for p in packets if p["source_ip"] == source and p["target_ip"] == target
                        and p["source_port"] == source_port and p["target_port"] == port
                        and p["timestamp"] >= syn["timestamp"]]
            inbound = [p for p in packets if p["source_ip"] == target and p["target_ip"] == source
                       and p["source_port"] == port and p["target_port"] == source_port
                       and p["timestamp"] >= syn["timestamp"]]
            synacks = [p for p in inbound if p["flags"] & 0x17 == 0x12
                       and p["acknowledgement"] == _next(syn["sequence"])]
            _require(bool(synacks), "HTTP SYN has no matching SYN/ACK")
            synack = synacks[0]
            acks = [p for p in outbound if p["flags"] & 0x16 == 0x10
                    and p["sequence"] == _next(syn["sequence"])
                    and p["acknowledgement"] == _next(synack["sequence"])
                    and p["timestamp"] >= synack["timestamp"]]
            _require(bool(acks), "HTTP handshake has no matching final ACK")
            request = _stream(outbound, _next(syn["sequence"]))
            response = _stream(inbound, _next(synack["sequence"]))
            expected_requests = [f"GET /proof-{token} HTTP/1.{version}\r\n".encode("ascii")
                                 for version in (0, 1)]
            _require(any(request.startswith(line) for line in expected_requests) and b"\r\n\r\n" in request,
                     "HTTP connection does not contain the expected proof request")
            _require(response.startswith(b"HTTP/1.0 200 "), "HTTP connection has no HTTP/1.0 200 response")
            headers, separator, body = response.partition(b"\r\n\r\n")
            _require(bool(separator), "HTTP response headers are incomplete")
            _require(f"netguard-proof:{token}".encode("ascii") in body, "HTTP response proof marker missing")
            length_headers = re.findall(rb"(?im)^Content-Length:\s*(\d+)\s*$", headers)
            if length_headers:
                _require(len(length_headers) == 1 and len(body) == int(length_headers[0]),
                         "HTTP response body is incomplete or Content-Length is ambiguous")
            return {"client_port": source_port, "handshake_verified": True,
                    "request_verified": True, "response_verified": True,
                    "request_bytes": len(request), "response_bytes": len(response)}
        except ValueError as exc:
            failures.append(str(exc))
    detail = failures[-1] if failures else "No HTTP SYN from the expected source to target"
    raise ValueError(f"No verified HTTP proof connection: {detail}")


def verify_capture(pcap_path: str | Path, scenario_dict: dict, capture_log_path: str | Path) -> dict:
    """Return a compact verified proof summary, or raise ValueError on failure.

    Required scenario fields: token, source_ip, target_ip, started_at, finished_at.
    Optional fields: http_port (8080), closed_ports ([8000, 8001, 8002]).
    Times are Unix seconds; a two-second tolerance applies to the full capture.
    """
    try:
        source = str(ipaddress.IPv4Address(scenario_dict["source_ip"]))
        target = str(ipaddress.IPv4Address(scenario_dict["target_ip"]))
        token = scenario_dict["token"]
        start = scenario_dict["started_at"]
        finish = scenario_dict["finished_at"]
        http_port = scenario_dict.get("http_port", 8080)
        closed_ports = scenario_dict.get("closed_ports", [8000, 8001, 8002])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Missing or invalid scenario metadata") from exc
    _require(source != target, "Scenario source and target must differ")
    _require(isinstance(token, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", token) is not None,
             "Invalid scenario token")
    _require(type(start) in (int, float) and type(finish) in (int, float)
             and math.isfinite(start) and math.isfinite(finish) and 0 < start <= finish,
             "Invalid scenario time window")
    _require(type(http_port) is int and 1 <= http_port <= 65535, "Invalid HTTP port")
    _require(isinstance(closed_ports, list) and len(closed_ports) >= 3
             and all(type(port) is int and 1 <= port <= 65535 and port != http_port for port in closed_ports),
             "At least three valid closed ports distinct from the HTTP port are required")
    _require(len(closed_ports) == len(set(closed_ports)), "Duplicate closed ports")
    data = _read_bounded(pcap_path, _MAX_FILE_BYTES)
    packets, timestamps, housekeeping = _parse_pcap(data)
    _require(all(start - 2 <= timestamp <= finish + 2 for timestamp in timestamps),
             "PCAP timestamps lie outside the scenario window (two-second tolerance)")
    _require(all({p["source_ip"], p["target_ip"]} == {source, target} for p in packets),
             "Capture includes TCP outside the configured source/target pair")
    log = _read_bounded(capture_log_path, 1024 * 1024).decode("utf-8", errors="replace")
    captured_counts = re.findall(r"(?m)^\s*(\d+) packets? captured\s*$", log)
    drop_counts = re.findall(r"(?m)^\s*(\d+) packets? dropped by kernel\s*$", log)
    _require(bool(captured_counts) and int(captured_counts[-1]) > 0, "tcpdump captured-packet statistics missing or empty")
    _require(int(captured_counts[-1]) == len(timestamps), "tcpdump count differs from PCAP record count")
    _require(bool(drop_counts) and all(int(count) == 0 for count in drop_counts),
             "tcpdump kernel-drop statistics missing or nonzero")
    http = _verify_http(packets, source, target, http_port, token)
    verified_closed_ports = []
    for port in closed_ports:
        syns = [p for p in packets if p["source_ip"] == source and p["target_ip"] == target
                and p["target_port"] == port and p["flags"] & 0x17 == 0x02]
        matching = any(
            response["source_ip"] == target and response["target_ip"] == source
            and response["source_port"] == port and response["target_port"] == syn["source_port"]
            and response["flags"] & 0x16 == 0x14
            and response["acknowledgement"] == _next(syn["sequence"])
            and response["timestamp"] >= syn["timestamp"]
            for syn in syns for response in packets
        )
        _require(matching, f"Closed TCP port {port} has no matching SYN and reverse RST/ACK")
        verified_closed_ports.append(port)
    return {
        "passed": True,
        "sha256": hashlib.sha256(data).hexdigest(),
        "packet_count": len(timestamps),
        "tcp_packet_count": len(packets),
        "housekeeping_packet_count": housekeeping,
        "source_ip": source,
        "target_ip": target,
        "http_port": http_port,
        "http": http,
        "closed_ports_verified": verified_closed_ports,
        "timestamps_verified": True,
        "first_packet_at": min(timestamps),
        "last_packet_at": max(timestamps),
        "kernel_drops": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pcap", type=Path)
    parser.add_argument("scenario", type=Path, help="Scenario metadata JSON")
    parser.add_argument("--capture-log", required=True, type=Path)
    args = parser.parse_args()
    try:
        scenario = json.loads(_read_bounded(args.scenario, 64 * 1024))
        _require(isinstance(scenario, dict), "Scenario JSON must be an object")
        result = verify_capture(args.pcap, scenario, args.capture_log)
    except (ValueError, UnicodeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
