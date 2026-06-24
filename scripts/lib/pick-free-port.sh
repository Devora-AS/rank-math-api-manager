#!/usr/bin/env bash
# Pick the first TCP port in [BASE, END] that can bind on 127.0.0.1 (for dev servers).
# Prints the port number to stdout, or exits 1 if none found.
# shellcheck shell=bash

pick_free_port() {
  local base="${1:?base port required}"
  local end="${2:-$((base + 100))}"
  python3 - "$base" "$end" <<'PY'
import socket
import sys

base = int(sys.argv[1])
end = int(sys.argv[2])


def port_is_available(port: int) -> bool:
    probes = [
        (socket.AF_INET, ("127.0.0.1", port)),
        (socket.AF_INET6, ("::1", port)),
    ]
    sockets = []
    try:
        for family, address in probes:
            try:
                sock = socket.socket(family, socket.SOCK_STREAM)
            except OSError:
                continue
            try:
                sock.bind(address)
            except OSError:
                sock.close()
                return False
            sockets.append(sock)
        return True
    finally:
        for sock in sockets:
            sock.close()


for port in range(base, end + 1):
    if port_is_available(port):
        print(port)
        sys.exit(0)

print("no free port in range", base, "..", end, file=sys.stderr)
sys.exit(1)
PY
}
