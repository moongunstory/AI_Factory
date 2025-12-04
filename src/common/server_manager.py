"""
Manages the lifecycle of the llama-server process.

This module provides a ServerManager class to start, stop, and clean up
the llama-server process in a way that is robust and avoids the
brittleness of shell scripts.
"""
import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from typing import Optional

import psutil
import requests

# Add project root to path to allow importing project modules
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.logger import setup_logger

logger = setup_logger(__name__)

class ServerManager:
    """Manages the llama-server lifecycle."""

    def __init__(self):
        """Initializes the ServerManager, setting up paths."""
        self.project_dir = PROJECT_ROOT
        self.pid_file = self.project_dir / "output" / "logs" / ".llama_server.pid"
        self.out_log_file = self.project_dir / "output" / "logs" / "llama_server.out.log"
        self.err_log_file = self.project_dir / "output" / "logs" / "llama_server.err.log"
        self.model_path = self.project_dir / "models" / "llm" / "Meta-Llama-3.1-8B-Instruct-Q5_K_M" / "Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf"
        self.llama_server_exe = self.project_dir / "engine" / "llama.cpp" / "build" / "bin" / "Release" / "llama-server.exe"

        # Server config
        self.server_host = "127.0.0.1"
        self.server_port = 8080
        self.health_url = f"http://{self.server_host}:{self.server_port}/health"

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
                # Extra check to ensure it's the correct process
                proc = psutil.Process(pid)
                if "llama-server" in proc.name():
                    return pid
        except (ValueError, psutil.NoSuchProcess):
            pass
        
        # If we reach here, the PID is stale
        self.pid_file.unlink(missing_ok=True)
        return None

    def start_server(self):
        """Starts the llama-server if it is not already running."""
        if self.get_server_pid():
            logger.warning(f"llama-server is already running (PID: {self.get_server_pid()}).")
            print("[OK] llama-server already running")
            return

        if not self.model_path.exists():
            logger.error(f"Model file not found: {self.model_path}")
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        if not self.llama_server_exe.exists():
            logger.error(f"llama-server executable not found: {self.llama_server_exe}")
            raise FileNotFoundError(f"llama-server executable not found: {self.llama_server_exe}")

        # Parameters optimized for single-user local environment
        params = [
            str(self.llama_server_exe),
            "--host", self.server_host,
            "--port", str(self.server_port),
            "--model", str(self.model_path),
            "--ctx-size", "8192",       # Full context for single request (increased for long prompts)
            "--batch-size", "512",      # Optimized for single request (reduced from 2048)
            "--threads", "4",
            "--n-gpu-layers", "-1",     # Load all layers to GPU
            "--parallel", "1",          # Single slot enforced
            "--ctx-checkpoints", "1",   # No slot division
            "--flash-attn", "on",       # Correctly set to on
            "--verbose"
        ]

        logger.info("Starting llama-server with GPU acceleration...")
        print("==========================================")
        print(" llama-server 시작 (GPU 가속)")
        print("==========================================")
        print(f"모델: {self.model_path.name}")
        print(f"포트: {self.server_port}")
        print("==========================================")

        try:
            with open(self.out_log_file, "wb") as out_log, open(self.err_log_file, "wb") as err_log:
                process = subprocess.Popen(
                    params,
                    stdout=out_log,
                    stderr=err_log,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
            
            self.pid_file.write_text(str(process.pid))
            logger.info(f"llama-server started with PID {process.pid}.")
            print(f"[시작] PID {process.pid}")
            print(f"[stdout 로그] {self.out_log_file}")
            print(f"[stderr 로그] {self.err_log_file}")

            # Health check loop (no timeout)
            print("\n[대기] 서버가 모델을 로드하는 중입니다. 모델 크기에 따라 몇 분 정도 소요될 수 있습니다...")
            print("       (자세한 내용은 stdout 로그 파일을 확인하세요: " + str(self.out_log_file) + ")")
            
            dot_count = 0
            while True:
                # Check if the server is healthy
                try:
                    response = requests.get(self.health_url, timeout=2)
                    if response.status_code == 200:
                        print("\n[완료] llama-server 준비됨!")
                        print(f"[URL] http://{self.server_host}:{self.server_port}")
                        return
                except requests.exceptions.RequestException:
                    # Server not ready yet, continue waiting
                    pass

                # Check if the process has died unexpectedly
                if not psutil.pid_exists(process.pid):
                    print("\n[오류] llama-server 프로세스가 시작 중 예기치 않게 종료되었습니다.")
                    print(f"       자세한 내용은 에러 로그 파일을 확인하세요: {self.err_log_file}")
                    sys.exit(1)
                
                # Print a dot to show progress
                print(".", end="", flush=True)
                dot_count += 1
                if dot_count % 60 == 0: # Newline every 60 dots
                    print()

                time.sleep(2) # Check every 2 seconds

        except Exception as e:
            logger.error(f"Failed to start llama-server: {e}")
            sys.exit(1)

    def stop_server(self):
        """Stops the running llama-server."""
        pid = self.get_server_pid()
        if not pid:
            logger.info("No running llama-server process found.")
            print("[정보] 실행 중인 llama-server 없음")
            return

        print(f"[중지] llama-server 종료 중 (PID: {pid})")
        try:
            proc = psutil.Process(pid)
            # Try graceful termination first
            proc.terminate()
            try:
                proc.wait(timeout=10)
                print("[완료] 정상 종료")
            except psutil.TimeoutExpired:
                print("[강제 종료]")
                proc.kill()
                proc.wait()
                print("[완료] 강제 종료됨")
        except psutil.NoSuchProcess:
            print("[정보] 프로세스가 이미 종료되었습니다.")
        except Exception as e:
            logger.error(f"Failed to stop process {pid}: {e}")

        self.pid_file.unlink(missing_ok=True)

    def cleanup_orphan_processes(self):
        """Finds and terminates any orphan llama-server processes."""
        print("[정리] 고아 llama-server 프로세스 검색")
        
        running_pid = self.get_server_pid()
        found_orphans = False

        for proc in psutil.process_iter(['pid', 'name']):
            if "llama-server" in proc.info['name'] and proc.info['pid'] != running_pid:
                print(f"[종료] 고아 PID: {proc.info['pid']}")
                try:
                    p = psutil.Process(proc.info['pid'])
                    p.kill()
                    p.wait()
                    found_orphans = True
                except psutil.NoSuchProcess:
                    pass # Process already died
                except Exception as e:
                    logger.warning(f"Failed to kill orphan process {proc.info['pid']}: {e}")

        if not found_orphans:
            print("[완료] 고아 프로세스 없음")
        else:
            print("[완료]")
