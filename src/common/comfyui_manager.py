"""
Manages the lifecycle of the ComfyUI server process.

This module provides a ComfyUIManager class to start, stop, and clean up
the ComfyUI server process.
"""
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional

import psutil
import requests

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.logger import setup_logger

logger = setup_logger(__name__)


class ComfyUIManager:
    """Manages the ComfyUI server lifecycle."""

    def __init__(self):
        """Initializes the ComfyUIManager, setting up paths."""
        self.project_dir = PROJECT_ROOT
        self.pid_file = self.project_dir / "output" / "logs" / ".comfyui_server.pid"
        self.out_log_file = self.project_dir / "output" / "logs" / "comfyui_server.out.log"
        self.err_log_file = self.project_dir / "output" / "logs" / "comfyui_server.err.log"

        # ComfyUI paths
        self.comfyui_dir = self.project_dir / "engine" / "comfyui"
        self.comfyui_main = self.comfyui_dir / "main.py"
        self.comfyui_venv_python = self.comfyui_dir / "venv" / "Scripts" / "python.exe"

        # Server config
        self.server_host = "127.0.0.1"
        self.server_port = 8188
        self.health_url = f"http://{self.server_host}:{self.server_port}/system_stats"

        # Create log directory if it doesn't exist
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)

    def get_server_pid(self) -> Optional[int]:
        """
        Reads the PID from the PID file and checks if the process is running.

        Returns:
            The PID if the process is running, otherwise None.
        """
        if not self.pid_file.exists():
            return None

        try:
            pid = int(self.pid_file.read_text().strip())
            if psutil.pid_exists(pid):
                # Extra check to ensure it's a Python process
                proc = psutil.Process(pid)
                if "python" in proc.name().lower():
                    return pid
        except (ValueError, psutil.NoSuchProcess):
            pass

        # If we reach here, the PID is stale
        self.pid_file.unlink(missing_ok=True)
        return None

    def start_server(self):
        """Starts the ComfyUI server if it is not already running."""
        if self.get_server_pid():
            logger.warning(f"ComfyUI is already running (PID: {self.get_server_pid()}).")
            print("[OK] ComfyUI already running")
            return

        if not self.comfyui_main.exists():
            logger.error(f"ComfyUI main.py not found: {self.comfyui_main}")
            print(f"[ERROR] ComfyUI not found at {self.comfyui_dir}")
            print("Please ensure ComfyUI is installed in engine/comfyui/")
            return

        # Determine which Python to use: venv if available, otherwise current interpreter
        if self.comfyui_venv_python.exists():
            python_exe = str(self.comfyui_venv_python)
            logger.info(f"Using ComfyUI venv Python: {python_exe}")
        else:
            python_exe = sys.executable
            logger.warning(f"ComfyUI venv not found, using system Python: {python_exe}")

        # ComfyUI startup parameters
        params = [
            python_exe,
            str(self.comfyui_main),
            "--listen", self.server_host,
            "--port", str(self.server_port),
        ]

        logger.info("Starting ComfyUI server...")
        print("==========================================")
        print(" ComfyUI 시작 (SDXL Image Generation)")
        print("==========================================")
        print(f"포트: {self.server_port}")
        print("==========================================")

        try:
            with open(self.out_log_file, "wb") as out_log, open(self.err_log_file, "wb") as err_log:
                process = subprocess.Popen(
                    params,
                    stdout=out_log,
                    stderr=err_log,
                    cwd=str(self.comfyui_dir),  # Run in ComfyUI directory
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )

            self.pid_file.write_text(str(process.pid))
            logger.info(f"ComfyUI started with PID {process.pid}.")
            print(f"[시작] PID {process.pid}")
            print(f"[stdout 로그] {self.out_log_file}")
            print(f"[stderr 로그] {self.err_log_file}")

            # Health check loop
            print("\n[대기] ComfyUI가 시작되는 중입니다. 모델 로딩에 1-2분 소요될 수 있습니다...")
            print("       (자세한 내용은 stdout 로그 파일을 확인하세요: " + str(self.out_log_file) + ")")

            max_wait_time = 180  # 3 minutes max
            elapsed = 0
            dot_count = 0

            while elapsed < max_wait_time:
                # Check if the server is healthy
                try:
                    response = requests.get(self.health_url, timeout=2)
                    if response.status_code == 200:
                        print("\n[완료] ComfyUI 준비됨!")
                        print(f"[URL] http://{self.server_host}:{self.server_port}")
                        return
                except requests.exceptions.RequestException:
                    # Server not ready yet, continue waiting
                    pass

                # Check if the process has died unexpectedly
                if not psutil.pid_exists(process.pid):
                    print("\n[오류] ComfyUI 프로세스가 시작 중 예기치 않게 종료되었습니다.")
                    print(f"       자세한 내용은 에러 로그 파일을 확인하세요: {self.err_log_file}")
                    return

                # Print a dot to show progress
                print(".", end="", flush=True)
                dot_count += 1
                if dot_count % 60 == 0:  # Newline every 60 dots
                    print()

                time.sleep(2)  # Check every 2 seconds
                elapsed += 2

            # If we reach here, health check timed out
            print("\n[경고] ComfyUI 헬스 체크 타임아웃 (서버는 백그라운드에서 계속 시작 중)")
            print(f"       URL: http://{self.server_host}:{self.server_port}")

        except Exception as e:
            logger.error(f"Failed to start ComfyUI: {e}")
            print(f"[오류] ComfyUI 시작 실패: {e}")

    def stop_server(self):
        """Stops the running ComfyUI server."""
        pid = self.get_server_pid()
        if not pid:
            logger.info("No running ComfyUI process found.")
            print("[정보] 실행 중인 ComfyUI 없음")
            return

        print(f"[중지] ComfyUI 종료 중 (PID: {pid})")
        try:
            proc = psutil.Process(pid)
            # Terminate all child processes first
            children = proc.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass

            # Try graceful termination
            proc.terminate()
            try:
                proc.wait(timeout=10)
                print("[완료] 정상 종료")
            except psutil.TimeoutExpired:
                print("[강제 종료]")
                proc.kill()
                # Kill remaining children
                for child in children:
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                proc.wait()
                print("[완료] 강제 종료됨")
        except psutil.NoSuchProcess:
            print("[정보] 프로세스가 이미 종료되었습니다.")
        except Exception as e:
            logger.error(f"Failed to stop process {pid}: {e}")

        self.pid_file.unlink(missing_ok=True)

    def cleanup_orphan_processes(self):
        """Finds and terminates any orphan ComfyUI processes."""
        print("[정리] 고아 ComfyUI 프로세스 검색")

        running_pid = self.get_server_pid()
        found_orphans = False

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'comfyui' in ' '.join(cmdline).lower() and proc.info['pid'] != running_pid:
                    print(f"[종료] 고아 PID: {proc.info['pid']}")
                    p = psutil.Process(proc.info['pid'])
                    p.kill()
                    p.wait()
                    found_orphans = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            except Exception as e:
                logger.warning(f"Failed to check process {proc.info['pid']}: {e}")

        if not found_orphans:
            print("[완료] 고아 프로세스 없음")
        else:
            print("[완료]")
