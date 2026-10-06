"""Run or attach to downloading, then prepare the real Cloth -> Sports data."""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def windows_process_running(pid):
    # Windows os.kill(pid, 0) is not a portable liveness check.
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    try:
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value == 259  # STILL_ACTIVE
    finally:
        kernel.CloseHandle(handle)


def download_estimate(progress):
    """Account for the largest remaining file, rather than total bytes only."""
    elapsed = progress.get("elapsed_seconds", 0)
    estimates = []
    for item in progress.get("files", {}).values():
        remaining = max(0, item.get("expected_bytes", 0) - item.get("received_bytes", 0))
        speed = item.get("network_bytes", 0) / elapsed if elapsed else 0
        if remaining and speed:
            estimates.append(remaining / speed)
    return round(max(estimates)) if estimates else None


def save_status(report_dir, status):
    status["updated_at"] = now()
    destination = report_dir / "pipeline_status.json"
    temp = destination.with_suffix(".tmp")
    temp.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, destination)
    labels = {"downloading": "正在下载", "preparing": "正在处理数据", "complete": "已完成", "failed": "失败，请查看日志"}
    lines = ["# Cloth→Sports 本机任务状态", "",
             f"状态：{labels.get(status['state'], status['state'])}", "",
             f"更新时间（UTC）：{status['updated_at']}", ""]
    if "download" in status:
        data = status["download"]
        lines += [f"下载：{data.get('received_bytes', 0) / 1e6:.1f} / {data.get('expected_bytes', 0) / 1e6:.1f} MB。", ""]
        estimate = status.get("download_eta_seconds")
        if estimate and status["state"] == "downloading":
            lines += [f"下载预计剩余约 {estimate / 60:.0f} 分钟（依据最慢文件的平均速度，随网络波动）。", "",
                      "随后自动执行 CPU 预处理；暂预留 10～20 分钟，实际耗时写入 audit.json。", ""]
    if "preparation" in status:
        lines += [f"预处理：`{json.dumps(status['preparation'], ensure_ascii=False)}`", ""]
    if "error" in status:
        lines += [f"错误：{status['error']}", ""]
    lines += ["日志：download.stdout.log、download.stderr.log、preparation.stdout.log、preparation.stderr.log。", "",
              f"完成后产物清单见 {status.get('evidence_directory', str(ROOT / 'CDRec/data/agent_evidence/cloth_to_sports/v2'))}/manifest.json；审计见本目录 audit.md。", ""]
    (report_dir / "status.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=ROOT / "CDRec/data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "CDRec/data/agent_evidence/cloth_to_sports/v2")
    parser.add_argument("--report-dir", type=Path, default=ROOT / "doc/experiments/2026-10-06_cloth_sports_90_5_5")
    parser.add_argument("--prompt-dev-ratio", type=float, default=0.05)
    parser.add_argument("--prompt-val-ratio", type=float, default=0.05)
    parser.add_argument("--internal-seed", type=int, default=999)
    parser.add_argument("--download-pid", type=int, help="Attach to an existing Windows downloader instead of starting one.")
    parser.add_argument("--direct", action="store_true", help="Use direct connections for a newly started downloader.")
    parser.add_argument("--download-attempts", type=int, default=20)
    args = parser.parse_args()
    if args.download_attempts < 1:
        parser.error("--download-attempts must be positive")
    report = args.report_dir.resolve()
    report.mkdir(parents=True, exist_ok=True)
    status = {"state": "downloading", "pid": os.getpid(), "started_at": now(),
              "connection_mode": "direct" if args.direct else "environment",
              "evidence_directory": str(args.output_dir.resolve()),
              "internal_split": {"dev_ratio": args.prompt_dev_ratio, "val_ratio": args.prompt_val_ratio,
                                 "seed": args.internal_seed}}
    started = time.monotonic()
    log_handles = []
    download_child = None
    try:
        if args.download_pid is None:
            for stream in ("stdout", "stderr"):
                log_handles.append((report / f"download.{stream}.log").open("a", encoding="utf-8"))
            download_command = [sys.executable, "-u", str(ROOT / "scripts/download_cloth_sports_data.py"),
                                "--data-root", str(args.data_root.resolve()), "--status", str(report / "download_status.json"),
                                "--max-attempts", str(args.download_attempts)]
            if args.direct:
                download_command.append("--direct")
            # Prevent a completed/failed status from a prior run being mistaken
            # for the child that is about to start.
            download_status_path = report / "download_status.json"
            download_status_temp = download_status_path.with_suffix(".tmp")
            download_status_temp.write_text(json.dumps({"state": "starting", "files": {}, "started_at": now()}), encoding="utf-8")
            os.replace(download_status_temp, download_status_path)
            download_child = subprocess.Popen(
                download_command,
                cwd=ROOT, stdout=log_handles[0], stderr=log_handles[1])
            args.download_pid = download_child.pid
            (report / "download.pid").write_text(str(download_child.pid) + "\n", encoding="utf-8")
            # Wait for this invocation to initialize status, not stale prior status.
            time.sleep(3)
        status["download_pid"] = args.download_pid
        while True:
            progress_path = report / "download_status.json"
            if progress_path.exists():
                progress = read_json(progress_path)
                status["download"] = progress
                status["download_eta_seconds"] = download_estimate(progress)
                save_status(report, status)
                if progress["state"] == "complete":
                    break
                if progress["state"] == "failed":
                    raise RuntimeError(f"Download failed: {progress.get('errors')}")
            alive = download_child.poll() is None if download_child else windows_process_running(args.download_pid)
            if not alive:
                raise RuntimeError("Downloader exited before reporting completion; resume with this script without --download-pid.")
            if time.monotonic() - started > 12 * 3600:
                raise TimeoutError("Download wait exceeded 12 hours; inspect download logs.")
            time.sleep(10)
        status.update(state="preparing", preparation_started_at=now(), download_eta_seconds=0)
        save_status(report, status)
        command = [sys.executable, "-u", str(ROOT / "scripts/prepare_cloth_sports_data.py"),
                   "--data-root", str(args.data_root.resolve()), "--output-dir", str(args.output_dir.resolve()),
                   "--report-dir", str(report), "--prompt-dev-ratio", str(args.prompt_dev_ratio),
                   "--prompt-val-ratio", str(args.prompt_val_ratio), "--internal-seed", str(args.internal_seed)]
        with (report / "preparation.stdout.log").open("a", encoding="utf-8") as out, \
                (report / "preparation.stderr.log").open("a", encoding="utf-8") as err:
            child = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err)
            status["preparation_pid"] = child.pid
            while child.poll() is None:
                child_status = args.output_dir / "status.json"
                if child_status.exists():
                    status["preparation"] = read_json(child_status)
                save_status(report, status)
                time.sleep(5)
            if child.returncode:
                raise RuntimeError(f"Preparation exited with code {child.returncode}; inspect preparation.stderr.log.")
        manifest = read_json(args.output_dir / "manifest.json")
        if manifest.get("state") != "complete":
            raise RuntimeError("Preparation exited without a completed manifest.")
        status.update(state="complete", completed_at=now(), elapsed_seconds=round(time.monotonic() - started),
                      preparation=read_json(args.output_dir / "status.json"), manifest=str(args.output_dir / "manifest.json"))
        save_status(report, status)
        print("Local preparation complete.", flush=True)
        return 0
    except Exception as exc:
        status.update(state="failed", error=str(exc), failed_at=now())
        save_status(report, status)
        print(str(exc), file=sys.stderr, flush=True)
        return 1
    finally:
        for handle in log_handles:
            handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
