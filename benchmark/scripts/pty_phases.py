#!/usr/bin/env python3
"""Run a two-phase interactive agent session without changing the agent."""

from __future__ import annotations

import argparse
import fcntl
import os
import pty
import select
import signal
import struct
import termios
import time
from pathlib import Path


DEFAULT_AGENT = os.environ.get("ELPIS_BIN", "elpis")


def stop_child(master: int, pid: int) -> None:
    try:
        os.write(master, b"\x03")
    except OSError:
        pass
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cwd", type=Path)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("phase1", type=Path)
    parser.add_argument("phase2", type=Path)
    parser.add_argument("sandbox")
    parser.add_argument("--marker", default="PHASE_ONE_DONE")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--stop-file")
    args = parser.parse_args()
    phase1 = args.phase1.read_text(encoding="utf-8")
    phase2 = args.phase2.read_text(encoding="utf-8")
    model = os.environ.get("ELPIS_MODEL", "inclusionai/ling-3.0-flash")
    if os.environ.get("BENCHMARK_ARM") == "direct":
        command = [
            os.environ.get("DIRECT_AGENT_BIN", "codex"),
            "--model", model,
            "--sandbox", args.sandbox,
            "--ask-for-approval", "never",
            "--no-alt-screen",
            phase1,
        ]
    else:
        command = [
            os.environ.get("ELPIS_BIN", DEFAULT_AGENT),
            "--provider", os.environ.get("ELPIS_PROVIDER", "openrouter"),
            "--model", model,
            "-c", 'model_reasoning_effort="minimal"',
            "-c", 'model_verbosity="low"',
            "--sandbox", args.sandbox,
            "--ask-for-approval", "never",
            "--no-alt-screen",
            phase1,
        ]
    args.transcript.parent.mkdir(parents=True, exist_ok=True)
    with args.transcript.open("wb") as output:
        output.write(("PTY phase command: " + " ".join(command[:-1]) + " <phase1>\n").encode())
        pid, master = pty.fork()
        if pid == 0:
            os.chdir(args.cwd)
            os.execvpe(command[0], command, os.environ.copy())
        fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
        start = time.monotonic()
        submitted = False
        phase2_sent = False
        text = ""
        status = None
        while True:
            waited, wait_status = os.waitpid(pid, os.WNOHANG)
            if waited == pid:
                status = wait_status
                break
            if args.stop_file and os.path.exists(args.stop_file):
                stop_child(master, pid)
                os.waitpid(pid, 0)
                output.write(b"\n[COMPLETION STOP]\n")
                return 0
            elapsed = time.monotonic() - start
            if not submitted and elapsed >= 1.5:
                os.write(master, b"\r")
                submitted = True
            if submitted and not phase2_sent and text.count(args.marker) >= 2:
                os.write(master, phase2.encode("utf-8") + b"\r")
                output.write(b"\n[PHASE TWO SENT]\n")
                output.flush()
                phase2_sent = True
            if elapsed >= args.timeout:
                stop_child(master, pid)
                os.waitpid(pid, 0)
                output.write(b"\n[PTY TIMEOUT]\n")
                return 124
            ready, _, _ = select.select([master], [], [], 0.25)
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    chunk = b""
                if chunk:
                    output.write(chunk)
                    output.flush()
                    text += chunk.decode("utf-8", errors="replace")
        while True:
            ready, _, _ = select.select([master], [], [], 0)
            if not ready:
                break
            try:
                chunk = os.read(master, 65536)
            except OSError:
                break
            if not chunk:
                break
            output.write(chunk)
        if os.WIFEXITED(status):
            return os.WEXITSTATUS(status)
        if os.WIFSIGNALED(status):
            return 128 + os.WTERMSIG(status)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
