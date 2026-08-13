#!/usr/bin/env python3
import argparse
import array
import fcntl
import os
import pty
import select
import signal
import struct
import subprocess
import termios
import time


DEFAULT_ELPIS_BIN = os.environ.get("ELPIS_BIN", "elpis")


def terminate_child(master: int, pid: int) -> None:
    try:
        os.write(master, b"\x03")
    except OSError:
        pass
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass


def run_direct_exec(args, command, env) -> int:
    os.makedirs(os.path.dirname(args.transcript), exist_ok=True)
    with open(args.transcript, "wb") as output:
        output.write(("Exec command: " + " ".join(command[:-1]) + " <prompt>\n").encode())
        process = subprocess.Popen(
            command,
            cwd=args.cwd,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
        )
        start = time.monotonic()
        while process.poll() is None:
            if args.stop_file and os.path.exists(args.stop_file):
                process.terminate()
                process.wait()
                output.write(b"\n[COMPLETION STOP]\n")
                return 0
            if time.monotonic() - start >= args.timeout:
                process.terminate()
                process.wait()
                output.write(b"\n[EXEC TIMEOUT]\n")
                return 124
            time.sleep(0.25)
        return process.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cwd")
    parser.add_argument("transcript")
    parser.add_argument("prompt")
    parser.add_argument("sandbox")
    parser.add_argument("--timeout", type=float, default=35.0)
    parser.add_argument("--stop-file")
    parser.add_argument("--response")
    args = parser.parse_args()
    prompt = open(args.prompt, encoding="utf-8").read()
    model = os.environ.get("ELPIS_MODEL", "inclusionai/ling-3.0-flash")
    if os.environ.get("BENCHMARK_ARM") == "direct":
        command = [
            os.environ.get("DIRECT_AGENT_BIN", "codex"),
            "--model", model,
            "--sandbox", args.sandbox,
            "--ask-for-approval", "never",
            "--no-alt-screen",
            prompt,
        ]
    else:
        command = [
            os.environ.get("ELPIS_BIN", DEFAULT_ELPIS_BIN),
            "--provider", os.environ.get("ELPIS_PROVIDER", "openrouter"),
            "--model", model,
            "-c", 'model_reasoning_effort="minimal"',
            "-c", 'model_verbosity="low"',
            "--sandbox", args.sandbox,
            "--ask-for-approval", "never",
            "--no-alt-screen",
            prompt,
        ]
    env = os.environ.copy()
    if os.environ.get("BENCHMARK_ARM") == "direct" and args.response:
        direct_command = [
            command[0],
            "exec",
            "--ephemeral",
            "--json",
            "--skip-git-repo-check",
            "-C", args.cwd,
            "--model", model,
            "--sandbox", args.sandbox,
            "--output-last-message", args.response,
            prompt,
        ]
        return run_direct_exec(args, direct_command, env)
    os.makedirs(os.path.dirname(args.transcript), exist_ok=True)
    with open(args.transcript, "wb") as output:
        output.write(("PTY command: " + " ".join(command[:-1]) + " <prompt>\n").encode())
        pid, master = pty.fork()
        if pid == 0:
            os.chdir(args.cwd)
            os.execvpe(command[0], command, env)
        fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
        start = time.monotonic()
        sent_enter = False
        status = None
        while True:
            waited, wait_status = os.waitpid(pid, os.WNOHANG)
            if waited == pid:
                status = wait_status
                break
            if args.stop_file and os.path.exists(args.stop_file):
                terminate_child(master, pid)
                os.waitpid(pid, 0)
                output.write(b"\n[COMPLETION STOP]\n")
                return 0
            elapsed = time.monotonic() - start
            if not sent_enter and elapsed >= 1.5:
                os.write(master, b"\r")
                sent_enter = True
            if elapsed >= args.timeout:
                terminate_child(master, pid)
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
