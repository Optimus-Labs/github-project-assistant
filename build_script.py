import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def build_package():
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # Create dist directory
    os.makedirs("dist", exist_ok=True)

    # Install build dependencies
    subprocess.check_call([sys.executable, "-m", "pip", "install", "build", "wheel"])

    # Build wheel
    subprocess.check_call([sys.executable, "-m", "build", "--wheel", "--no-isolation"])

    # Create platform-specific packages
    platforms = [
        ("linux", "x86_64"),
        ("darwin", "x86_64"),
        ("darwin", "arm64"),
    ]

    for os_name, arch in platforms:
        # Create directory structure
        dist_dir = Path(f"dist/gpa-{os.getenv('VERSION')}-{os_name}-{arch}")
        bin_dir = dist_dir / "bin"
        bin_dir.mkdir(parents=True)

        # Copy wheel to lib directory
        wheel_file = next(Path("dist").glob("*.whl"))
        lib_dir = dist_dir / "lib"
        lib_dir.mkdir()
        shutil.copy(wheel_file, lib_dir)

        # Create executable script
        executable = bin_dir / "gpa"
        with executable.open("w") as f:
            f.write(f"""#!/bin/sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
INSTALL_DIR=$(dirname "$SCRIPT_DIR")
export PYTHONPATH="$INSTALL_DIR/lib/{wheel_file.name}"
exec python3 -m gpa "$@"
""")

        # Make executable
        executable.chmod(0o755)

        # Create tarball
        shutil.make_archive(
            f"dist/gpa-{os.getenv('VERSION')}-{os_name}-{arch}",
            "gztar",
            "dist",
            f"gpa-{os.getenv('VERSION')}-{os_name}-{arch}",
        )


if __name__ == "__main__":
    build_package()
