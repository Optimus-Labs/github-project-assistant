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
    if os.path.exists("src/gpa.egg-info"):
        shutil.rmtree("src/gpa.egg-info")

    # Create dist directory
    os.makedirs("dist", exist_ok=True)

    # Install build dependencies
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "build",
            "wheel",
            "setuptools>=42",
            "twine",
            # Install package dependencies
            "typer>=0.9.0",
            "rich>=13.0.0",
            "groq>=0.4.0",
            "GitPython>=3.1.0",
            "PyGithub>=2.1.1",
        ]
    )

    # Build wheel with isolation to ensure clean environment
    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "build",
                "--wheel",
                "--outdir",
                "dist/",
                "--no-isolation",  # This ensures our local src directory is used
            ]
        )
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        subprocess.run([sys.executable, "-m", "pip", "list"])
        raise

    # Create platform-specific packages
    platforms = [
        ("linux", "x86_64"),
        ("darwin", "x86_64"),
        ("darwin", "arm64"),
    ]

    wheel_file = next(Path("dist").glob("*.whl"))

    for os_name, arch in platforms:
        # Create directory structure
        pkg_version = os.getenv("VERSION", "0.1.0")
        dist_dir = Path(f"dist/gpa-{pkg_version}-{os_name}-{arch}")
        bin_dir = dist_dir / "bin"
        lib_dir = dist_dir / "lib"

        # Create directories
        bin_dir.mkdir(parents=True, exist_ok=True)
        lib_dir.mkdir(parents=True, exist_ok=True)

        # Copy wheel to lib directory
        shutil.copy(wheel_file, lib_dir)

        # Create executable script
        executable = bin_dir / "gpa"
        with executable.open("w") as f:
            f.write(f"""#!/bin/sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0" || echo "$0")")
INSTALL_DIR=$(dirname "$SCRIPT_DIR")
export PYTHONPATH="$INSTALL_DIR/lib/{wheel_file.name}"
# Ensure dependencies are installed
python3 -m pip install --user typer rich groq GitPython PyGithub
python3 -m gpa "$@"
""")

        # Make executable
        executable.chmod(0o755)

        # Create tarball
        archive_name = f"gpa-{pkg_version}-{os_name}-{arch}"
        shutil.make_archive(f"dist/{archive_name}", "gztar", "dist", archive_name)


if __name__ == "__main__":
    build_package()
