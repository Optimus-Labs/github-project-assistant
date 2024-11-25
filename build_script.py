#!/usr/bin/env python3
import os
import shutil
import subprocess
import platform
import sys
from pathlib import Path

PLATFORMS = [
    ("linux", "x86_64"),
    ("linux", "aarch64"),
    ("darwin", "x86_64"),
    ("darwin", "arm64"),
]

VERSION = "0.1.0"


def clean_dist():
    """Clean existing distribution files"""
    print("Cleaning previous builds...")
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("build_venv", ignore_errors=True)
    for path in Path(".").glob("*.egg-info"):
        shutil.rmtree(path)


def create_virtualenv(venv_path):
    """Create a virtual environment"""
    print(f"Creating virtual environment in {venv_path}...")
    subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

    # Upgrade pip in the virtual environment
    pip = str(Path(venv_path) / "bin" / "pip")
    subprocess.run([pip, "install", "--upgrade", "pip"], check=True)


def install_build_dependencies(venv_path):
    """Install build dependencies in virtual environment"""
    print("Installing build dependencies...")
    pip = str(Path(venv_path) / "bin" / "pip")
    subprocess.run([pip, "install", "build", "wheel"], check=True)


def build_wheel(venv_path):
    """Build wheel package"""
    print("Building wheel package...")
    python = str(Path(venv_path) / "bin" / "python")
    subprocess.run([python, "-m", "build", "--wheel"], check=True)


def build_package(platform_tuple):
    """Build package for specific platform"""
    os_name, arch = platform_tuple
    print(f"\nBuilding package for {os_name}-{arch}...")

    dist_name = f"gpa-{VERSION}-{os_name}-{arch}"
    dist_path = Path("dist") / dist_name

    # Create distribution directory structure
    os.makedirs(dist_path / "bin", exist_ok=True)
    os.makedirs(dist_path / "lib", exist_ok=True)

    # Copy wheel and dependencies
    wheels_dir = Path("dist")
    wheel_file = next(wheels_dir.glob("*.whl"))
    lib_path = dist_path / "lib"
    shutil.copy(wheel_file, lib_path)

    # Copy documentation files
    shutil.copy("README.md", dist_path)
    if Path("LICENSE").exists():
        shutil.copy("LICENSE", dist_path)

    # Create launcher script
    create_launcher_script(dist_path / "bin" / "gpa", os_name)

    # Package everything
    archive_path = Path("dist") / dist_name
    shutil.make_archive(str(archive_path), "gztar", str(dist_path.parent), dist_name)

    # Clean up intermediate files
    shutil.rmtree(dist_path)


def create_launcher_script(path, os_name):
    """Create platform-specific launcher script"""
    if os_name == "windows":
        content = "@echo off\r\npython -m gpa %*"
        ext = ".bat"
    else:
        content = f"""#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"
PACKAGE_DIR="$SCRIPT_DIR/../lib"
WHEEL_FILE="$(ls $PACKAGE_DIR/*.whl)"

# Ensure virtual environment exists
VENV_DIR="$HOME/.gpa/venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install "$WHEEL_FILE"
fi

# Run GPA
"$VENV_DIR/bin/python" -m gpa "$@"
"""
        ext = ""

    script_path = str(path) + ext
    with open(script_path, "w") as f:
        f.write(content)

    if os_name != "windows":
        os.chmod(script_path, 0o755)


def main():
    try:
        clean_dist()

        # Create and set up virtual environment
        venv_path = "build_venv"
        create_virtualenv(venv_path)
        install_build_dependencies(venv_path)

        # Build wheel package
        build_wheel(venv_path)

        # Build platform-specific packages
        for platform_tuple in PLATFORMS:
            build_package(platform_tuple)

        print("\nBuild complete! Distribution packages are in the 'dist' directory.")

        # List created packages
        print("\nCreated packages:")
        for file in os.listdir("dist"):
            if file.endswith(".tar.gz"):
                print(f"- {file}")

    except subprocess.CalledProcessError as e:
        print(f"\nError during build process:")
        print(f"Command '{' '.join(e.cmd)}' failed with exit status {e.returncode}")
        print("\nOutput:")
        if e.output:
            print(e.output.decode())
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
