"""
Command-line interface for managing all AI Short Factory backend services.

This script manages:
- llama-server (LLM)
- ComfyUI (Image Generation)

Usage:
    python manage_server.py start [service]    - Start service(s)
    python manage_server.py stop [service]     - Stop service(s)
    python manage_server.py restart [service]  - Restart service(s)
    python manage_server.py status [service]   - Check status
    python manage_server.py cleanup            - Clean up orphan processes

Services: llama, comfyui, all (default)
"""
import sys
from pathlib import Path

# Add project root to path to allow importing project modules
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Import managers
from src.common.server_manager import ServerManager
from src.common.comfyui_manager import ComfyUIManager


class AllServicesManager:
    """Unified manager for all backend services."""

    def __init__(self):
        self.llama = ServerManager()
        self.comfyui = ComfyUIManager()

    def start_all(self):
        """Start all services."""
        print("=" * 50)
        print("  AI Short Factory - Starting All Services")
        print("=" * 50)
        print()

        # Start llama-server first (critical)
        print("▶ Starting llama-server...")
        self.llama.start_server()
        print()

        # Start ComfyUI
        print("▶ Starting ComfyUI...")
        self.comfyui.start_server()
        print()

        print("=" * 50)
        print("  All Services Started")
        print("=" * 50)

    def stop_all(self):
        """Stop all services."""
        print("=" * 50)
        print("  Stopping All Services")
        print("=" * 50)
        print()

        # Stop in reverse order
        print("▶ Stopping ComfyUI...")
        self.comfyui.stop_server()
        print()

        print("▶ Stopping llama-server...")
        self.llama.stop_server()
        print()

        print("=" * 50)
        print("  All Services Stopped")
        print("=" * 50)

    def restart_all(self):
        """Restart all services."""
        self.stop_all()
        print()
        self.start_all()

    def status_all(self):
        """Check status of all services."""
        print("=" * 50)
        print("  Service Status")
        print("=" * 50)

        all_running = True

        # llama-server
        llama_pid = self.llama.get_server_pid()
        if llama_pid:
            print(f"✓ llama-server: Running (PID: {llama_pid})")
        else:
            print("✗ llama-server: Not running")
            all_running = False

        # ComfyUI
        comfyui_pid = self.comfyui.get_server_pid()
        if comfyui_pid:
            print(f"✓ ComfyUI: Running (PID: {comfyui_pid})")
        else:
            print("✗ ComfyUI: Not running")
            all_running = False

        print("=" * 50)

        return all_running

    def cleanup_all(self):
        """Clean up orphan processes for all services."""
        print("=" * 50)
        print("  Cleaning Up Orphan Processes")
        print("=" * 50)
        print()

        self.llama.cleanup_orphan_processes()
        print()
        self.comfyui.cleanup_orphan_processes()

        print()
        print("=" * 50)
        print("  Cleanup Complete")
        print("=" * 50)


def main():
    """Parses command-line arguments and executes the corresponding action."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    action = sys.argv[1].lower()
    service = sys.argv[2].lower() if len(sys.argv) > 2 else "all"

    # Create managers
    all_manager = AllServicesManager()
    llama_manager = ServerManager()
    comfyui_manager = ComfyUIManager()

    # Route to appropriate manager
    if service == "all":
        manager = all_manager
    elif service == "llama":
        manager = llama_manager
    elif service == "comfyui":
        manager = comfyui_manager
    else:
        print(f"Error: Unknown service '{service}'")
        print_usage()
        sys.exit(1)

    # Execute action
    if action == 'start':
        if service == "all":
            manager.start_all()
        else:
            manager.start_server()

    elif action == 'stop':
        if service == "all":
            manager.stop_all()
        else:
            manager.stop_server()

    elif action == 'restart':
        if service == "all":
            manager.restart_all()
        else:
            manager.stop_server()
            print()
            manager.start_server()

    elif action == 'status':
        if service == "all":
            all_running = manager.status_all()
            sys.exit(0 if all_running else 1)
        else:
            pid = manager.get_server_pid()
            if pid:
                print(f"[상태] {service} 실행 중 (PID: {pid})")
            else:
                print(f"[상태] {service} 실행 중 아님")
                sys.exit(1)

    elif action == 'cleanup':
        if service == "all":
            manager.cleanup_all()
        else:
            manager.cleanup_orphan_processes()

    else:
        print(f"Error: Unknown action '{action}'")
        print_usage()
        sys.exit(1)


def print_usage():
    """Prints the usage instructions."""
    print(__doc__)
    print("\nExamples:")
    print("  python manage_server.py start           # Start all services")
    print("  python manage_server.py start llama     # Start only llama-server")
    print("  python manage_server.py stop comfyui    # Stop only ComfyUI")
    print("  python manage_server.py status          # Check all services")
    print("  python manage_server.py cleanup         # Clean up orphans")


if __name__ == "__main__":
    main()
