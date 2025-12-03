"""
Command-line interface for managing the llama-server.

This script replaces the need for the llama_server_manager.ps1 script,
providing a robust, Python-native way to control the server.
"""
import sys
from pathlib import Path

# Add project root to path to allow importing project modules
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Now that the path is set, we can import the ServerManager
from src.common.server_manager import ServerManager

def main():
    """Parses command-line arguments and executes the corresponding action."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    action = sys.argv[1].lower()
    manager = ServerManager()

    if action == 'start':
        manager.start_server()
    elif action == 'stop':
        manager.stop_server()
    elif action == 'cleanup':
        manager.cleanup_orphan_processes()
    elif action == 'status':
        pid = manager.get_server_pid()
        if pid:
            print(f"[상태] llama-server 실행 중 (PID: {pid})")
        else:
            print("[상태] 실행 중 아님")
            # Exit with an error code to match powershell script behavior for scripting
            sys.exit(1)
    else:
        print(f"Error: Unknown action '{action}'")
        print_usage()
        sys.exit(1)

def print_usage():
    """Prints the usage instructions."""
    print("Usage: python manage_server.py {start|stop|status|cleanup}")
    print("\nExamples:")
    print("  python manage_server.py start")
    print("  python manage_server.py status")
    print("  python manage_server.py stop")

if __name__ == "__main__":
    main()
