"""Task SSH transport. Credentials live in an ignored local file, never logs."""
from pathlib import Path
import argparse
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".codex_tools/ssh"))
import paramiko


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("exec", "upload", "download"))
    parser.add_argument("--command")
    parser.add_argument("--command-file", type=Path)
    parser.add_argument("--local")
    parser.add_argument("--remote")
    parser.add_argument("--timeout", type=int, default=55)
    parser.add_argument('--trace',action='store_true')
    parser.add_argument('--pty',action='store_true')
    args = parser.parse_args()
    connection = json.loads((ROOT / ".codex_tools/featurize.json").read_text(encoding="utf-8"))
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    known = ROOT / ".codex_tools/featurize_known_hosts"
    if known.exists():
        client.load_host_keys(str(known))
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        connected_at=time.monotonic()
        client.connect(**connection, timeout=20, auth_timeout=20, banner_timeout=20, look_for_keys=False, allow_agent=False)
        if args.trace: print({'ssh_connected_seconds':round(time.monotonic()-connected_at,2)},flush=True)
        client.get_transport().set_keepalive(15)
        client.save_host_keys(str(known))
        if args.action == "exec":
            command = args.command_file.read_text(encoding="utf-8") if args.command_file else args.command
            stdin, stdout, stderr = client.exec_command(command, timeout=args.timeout,get_pty=args.pty)
            if args.trace: print({'command_channel_seconds':round(time.monotonic()-connected_at,2)},flush=True)
            # Keep the command channel open until completion. Some SSH gateways
            # close a forwarded session when they receive an early stdin EOF.
            channel = stdout.channel
            deadline = time.monotonic() + args.timeout
            while True:
                if channel.recv_ready():
                    sys.stdout.buffer.write(channel.recv(65536))
                    sys.stdout.flush()
                if channel.recv_stderr_ready():
                    sys.stderr.buffer.write(channel.recv_stderr(65536))
                    sys.stderr.flush()
                if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
                    break
                if time.monotonic() > deadline:
                    raise TimeoutError("Remote command timed out")
                time.sleep(.05)
            sys.exit(channel.recv_exit_status())
        else:
            started = time.monotonic()
            progress_at=[started]
            def progress(done,total):
                now=time.monotonic()
                if now-progress_at[0]>=10 or done==total:
                    print(json.dumps({'bytes':done,'total':total,'MiB_per_second':round(done/max(.001,now-started)/2**20,2)}),flush=True)
                    progress_at[0]=now
            with client.open_sftp() as sftp:
                sftp.get_channel().settimeout(args.timeout)
                if args.action == "upload":
                    sftp.put(args.local, args.remote,callback=progress)
                else:
                    Path(args.local).parent.mkdir(parents=True, exist_ok=True)
                    sftp.get(args.remote, args.local,callback=progress)
            print(json.dumps({"action": args.action, "elapsed_seconds": round(time.monotonic()-started, 2), "local": args.local}))
    finally:
        client.close()


if __name__ == "__main__":
    main()
