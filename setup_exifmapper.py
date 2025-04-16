#!/usr/bin/env python3
import os
import sys
import platform
import subprocess
import shutil
import stat

def run_command(command, shell=False, silent=False):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(command, shell=shell, check=True, text=True, capture_output=True)
        if not silent:
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        if not silent:
            print(f"Error running command {' '.join(command) if not shell else command}: {e.stderr}")
        return False, e.stderr
    except Exception as e:
        if not silent:
            print(f"Unexpected error: {str(e)}")
        return False, str(e)

def get_linux_distro():
    """Detect Linux distribution by reading /etc/os-release."""
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("ID="):
                    distro_id = line.strip().split("=")[1].strip('"')
                    return distro_id.lower()
    except Exception:
        return None
    return None

def check_system_dependency(package, distro):
    """Check if a system package is installed based on the distro."""
    if distro in ["debian", "ubuntu", "linuxmint"]:
        success, _ = run_command(["dpkg", "-l", package], silent=True)
    elif distro == "fedora":
        success, _ = run_command(["rpm", "-q", package], silent=True)
    elif distro == "arch":
        success, _ = run_command(["pacman", "-Qs", package], silent=True)
    else:
        return False
    return success

def check_python_dependency(package):
    """Check if a Python package is installed using pip show."""
    success, _ = run_command([sys.executable, "-m", "pip", "show", package], silent=True)
    return success

def check_executable():
    """Check if the exifmapper executable is already installed."""
    system = platform.system()
    if system == "Linux":
        dest_path = "/usr/local/bin/exifmapper"
    elif system == "Windows":
        python_scripts = os.path.join(os.path.dirname(sys.executable), "Scripts")
        dest_path = os.path.join(python_scripts, "exifmapper.py")
    else:
        return False
    return os.path.exists(dest_path)

def check_desktop_entry():
    """Check if the desktop entry exists (Linux only)."""
    if platform.system() != "Linux":
        return True
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    desktop_file = os.path.join(desktop_dir, "exifmapper.desktop")
    return os.path.exists(desktop_file)

def convert_line_endings(file_path):
    """Convert Windows line endings (\r\n) to Unix line endings (\n)."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        content = content.replace(b'\r\n', b'\n')
        with open(file_path, 'wb') as f:
            f.write(content)
        print(f"Converted line endings in {file_path} to Unix style.")
    except Exception as e:
        print(f"Failed to convert line endings in {file_path}: {str(e)}")

def install_python_dependencies():
    """Install Python dependencies if not already installed."""
    dependencies = ["PyQt6", "requests", "folium", "Pillow", "geopy", "simplekml"]
    print("Checking Python dependencies...")
    all_installed = True
    for dep in dependencies:
        if check_python_dependency(dep):
            print(f"{dep} is already installed.")
        else:
            print(f"Installing {dep}...")
            if not run_command([sys.executable, "-m", "pip", "install", dep])[0]:
                print(f"Failed to install {dep}. Please install it manually.")
                all_installed = False
    return all_installed

def install_linux_dependencies():
    """Install system dependencies on Linux if not already installed."""
    distro = get_linux_distro()
    print(f"Detected Linux distribution: {distro or 'unknown'}")
    
    # Map package names for different distros
    package_map = {
        "debian": {
            "qt6": ["libqt6core6", "libqt6gui6", "libqt6widgets6", "qt6-base-dev"],
            "xcb": ["libxcb-cursor0", "libxcb1", "libxcb-xfixes0", "libxcb-shape0", 
                    "libxcb-shm0", "libxcb-render0", "libxcb-randr0", "libxcb-keysyms1"]
        },
        "ubuntu": {
            "qt6": ["libqt6core6", "libqt6gui6", "libqt6widgets6", "qt6-base-dev"],
            "xcb": ["libxcb-cursor0", "libxcb1", "libxcb-xfixes0", "libxcb-shape0", 
                    "libxcb-shm0", "libxcb-render0", "libxcb-randr0", "libxcb-keysyms1"]
        },
        "linuxmint": {
            "qt6": ["libqt6core6", "libqt6gui6", "libqt6widgets6", "qt6-base-dev"],
            "xcb": ["libxcb-cursor0", "libxcb1", "libxcb-xfixes0", "libxcb-shape0", 
                    "libxcb-shm0", "libxcb-render0", "libxcb-randr0", "libxcb-keysyms1"]
        },
        "fedora": {
            "qt6": ["qt6-qtbase", "qt6-qtbase-devel"],
            "xcb": ["libxcb", "xcb-util-cursor"]
        },
        "arch": {
            "qt6": ["qt6-base"],
            "xcb": ["libxcb", "xcb-util-cursor"]
        }
    }

    if distro not in package_map:
        print(f"Unsupported distribution: {distro}. Please install Qt6 and libxcb dependencies manually.")
        return False

    packages = package_map[distro]["qt6"] + package_map[distro]["xcb"]
    print("Checking system dependencies...")
    missing_packages = []
    for pkg in packages:
        if check_system_dependency(pkg, distro):
            print(f"{pkg} is already installed.")
        else:
            missing_packages.append(pkg)
    
    if not missing_packages:
        print("All system dependencies are already installed.")
        return True

    print(f"Installing missing packages: {', '.join(missing_packages)}...")
    if distro in ["debian", "ubuntu", "linuxmint"]:
        commands = [
            ["sudo", "apt", "update"],
            ["sudo", "apt", "install", "-y"] + missing_packages
        ]
    elif distro == "fedora":
        commands = [
            ["sudo", "dnf", "install", "-y"] + missing_packages
        ]
    elif distro == "arch":
        commands = [
            ["sudo", "pacman", "-Syu", "--noconfirm"],
            ["sudo", "pacman", "-S", "--noconfirm"] + missing_packages
        ]
    else:
        return False

    for cmd in commands:
        if not run_command(cmd)[0]:
            print(f"Failed to run {' '.join(cmd)}. Please install dependencies manually.")
            return False
    return True

def install_windows_dependencies():
    """Placeholder for Windows system dependencies (usually none needed)."""
    print("Detected Windows. No additional system dependencies required.")
    return True

def setup_executable():
    """Copy exifmapper.py to a system-wide location if not already installed."""
    if check_executable():
        print("Exifmapper executable is already installed.")
        return True

    script_name = "exifmapper.py"
    if not os.path.exists(script_name):
        print(f"Error: {script_name} not found in the current directory.")
        return False

    system = platform.system()
    if system == "Linux":
        dest_path = "/usr/local/bin/exifmapper"
        print(f"Copying {script_name} to {dest_path}...")
        try:
            # Convert line endings before copying
            convert_line_endings(script_name)
            shutil.copy(script_name, dest_path)
            # Ensure Unix line endings in destination
            convert_line_endings(dest_path)
            # Set executable permissions
            os.chmod(dest_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            print(f"Successfully installed {dest_path}. You can run 'exifmapper' from any CLI.")
            return True
        except Exception as e:
            print(f"Failed to copy {script_name} to {dest_path}: {str(e)}")
            return False
    elif system == "Windows":
        python_scripts = os.path.join(os.path.dirname(sys.executable), "Scripts")
        dest_path = os.path.join(python_scripts, "exifmapper.py")
        print(f"Copying {script_name} to {dest_path}...")
        try:
            shutil.copy(script_name, dest_path)
            bat_path = os.path.join(python_scripts, "exifmapper.bat")
            with open(bat_path, "w") as bat_file:
                bat_file.write(f'@echo off\n"{sys.executable}" "{dest_path}" %*\n')
            print(f"Successfully installed {dest_path}. Ensure {python_scripts} is in your PATH.")
            print("You can run 'exifmapper' from any CLI after adding Python's Scripts to PATH.")
            return True
        except Exception as e:
            print(f"Failed to copy {script_name} to {dest_path}: {str(e)}")
            return False
    else:
        print(f"Unsupported operating system: {system}")
        return False

def create_desktop_entry():
    """Create a desktop entry for GUI launching if not already present (Linux only)."""
    if platform.system() != "Linux":
        print("Desktop entry creation is only supported on Linux.")
        return True

    if check_desktop_entry():
        print("Desktop entry is already created.")
        return True

    desktop_entry = """[Desktop Entry]
Name=ExifMapper
Exec=exifmapper
Type=Application
Terminal=false
Categories=Utility;
Comment=Map GPS data from images
"""
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    desktop_file = os.path.join(desktop_dir, "exifmapper.desktop")
    print(f"Creating desktop entry at {desktop_file}...")
    try:
        os.makedirs(desktop_dir, exist_ok=True)
        with open(desktop_file, "w") as f:
            f.write(desktop_entry)
        os.chmod(desktop_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        print("Desktop entry created. You can launch ExifMapper from your application menu.")
        return True
    except Exception as e:
        print(f"Failed to create desktop entry: {str(e)}")
        return False

def main():
    print("Setting up ExifMapper...")
    system = platform.system()
    print(f"Operating System: {system}")

    # Install system dependencies
    if system == "Linux":
        if not install_linux_dependencies():
            print("System dependency installation failed. Exiting.")
            return
    elif system == "Windows":
        if not install_windows_dependencies():
            print("System dependency installation failed. Exiting.")
            return
    else:
        print(f"Unsupported operating system: {system}")
        return

    # Install Python dependencies
    if not install_python_dependencies():
        print("Python dependency installation failed. Exiting.")
        return

    # Setup executable
    if not setup_executable():
        print("Failed to set up executable. Exiting.")
        return

    # Create desktop entry (Linux only)
    if not create_desktop_entry():
        print("Failed to create desktop entry, but setup is complete.")

    print("\nSetup complete! You can now run 'exifmapper' from any CLI.")
    if system == "Windows":
        print("Ensure Python's Scripts directory is in your PATH.")
        print("To add it, run: setx PATH \"%PATH%;%APPDATA%\\Python\\PythonXX\\Scripts\"")
        print("Replace 'PythonXX' with your Python version (e.g., Python39).")

if __name__ == "__main__":
    main()