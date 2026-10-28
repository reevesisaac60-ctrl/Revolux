#!/usr/bin/env python3

import argparse
import json
import platform
import shutil
import subprocess
import os
import sys

MIN_PYTHON = (3, 10)
REQUIRED_TOOLS = ["gcc", "g++", "make", "ld", "as", "ar", "bash", "perl", "python3", "m4", "bison", "gawk", "sed", "grep", "find", "diff", "patch", "tar", "gzip", "xz", "bzip2", "file", "readelf"]
OPTIONAL_TOOLS = ["git", "cmake", "ninja", "qemu-system-x86_64", "qemu-img", "xorriso", "pkg-config"]

def get_version(command):
    path = shutil.which(command)

    if path is None:
        return None
    
    try:
        result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return "Available; version could not be determined!"

    output = result.stdout or result.stderr

    for line in output.splitlines():
        line = line.strip()
        if line:
            return line[:200]
        
    return "Available; version could not be determined!"

def inspect_tools(names):
    results = {}

    for name in names:
        path = shutil.which(name)
        results[name] = {"available": path is not None, "path": path, "version": get_version(name) if path else None}

    return results


def run_check():
    python_version = platform.python_version_tuple()
    python_version = tuple(int(part) for part in python_version[:2])

    required = inspect_tools(REQUIRED_TOOLS)
    optional = inspect_tools(OPTIONAL_TOOLS)

    missing_required = [
        name
        for name, info in required.items()
        if not info["available"]
    ]

    return {
        "assessment": "preliminary",
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "python_supported": python_version >= MIN_PYTHON,
            "logical_cpus": os.cpu_count(),
        },
        "tools": {
            "required": required,
            "optional": optional,
        },
        "missing_required": missing_required,
        "ready_for_next_stage": (
            not missing_required
            and python_version >= MIN_PYTHON
        ),
    }

def main():
    parser = argparse.ArgumentParser(description="Inspect prerequisites for the Veyra bootstrap!")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON!")
    args = parser.parse_args()
    report = run_check()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        host = report["host"]

        print("Revolux Bootstrap - Preliminary Host Assessment")
        print("="*48)
        print(f"Operating System: {host['system']}")
        print(f"Kernel Release:   {host['release']}")
        print(f"Architecture:     {host['architecture']}")
        print(f"Python:           {host['python_version']}")
        print(f"Logical CPUs:     {host['logical_cpus']}")
        print("Python supported: "f"{'yes' if host['python_supported'] else 'no'}")

        print("\n Required tools:")
        for name, info in report["tools"]["required"].items():
            status = "FOUND" if info ["available"] else "MISSING"
            print(f"   [{status}] {name}")
        
        print("\n Optional tools:")
        for name, info in report["tools"]["optional"].items():
            status = "FOUND" if info ["available"] else "MISSING"
            print(f"   [{status}] {name}")
        
        print("\nAssessment:")
        if report["ready_for_next_stage"]:
            print("Inital prerequisites appear available.")
        else:
            print("Some prerequisites need attention!")
        
        print("This check does not establish that the host is ready for a complete or production bootstrap.")

        return 0 if report["ready_for_next_stage"] else 1

if __name__ == "__main__":
    sys.exit(main())