import os
import shutil
import sys
from pathlib import Path

def find_node():
    # 1. Check system PATH first
    node_path = shutil.which("node")
    if node_path:
        print(f"Found in PATH: {node_path}")
        return node_path

    # 2. Check common Windows installation paths
    common_paths = [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        os.path.expanduser(r"~\AppData\Roaming\npm\node.exe"),
        os.path.expanduser(r"~\AppData\Local\nvs\default\node.exe"),
        os.path.expanduser(r"~\.nvm\versions\node\*\node.exe"),
    ]

    print("Scanning common paths...")
    for path_str in common_paths:
        if '*' in path_str:
            # Handle wildcards if any
            import glob
            matches = glob.glob(path_str)
            if matches:
                print(f"Found in common path: {matches[0]}")
                return matches[0]
        else:
            path = Path(path_str)
            if path.exists():
                print(f"Found in common path: {path}")
                return str(path)
    
    print("Node.js not found in standard locations.")
    return None

if __name__ == "__main__":
    found = find_node()
    if found:
        print(f"\nSUCCESS! Node.js path is: {found}")
    else:
        print("\nFAILED: Could not find Node.js automatically.")