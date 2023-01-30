import subprocess
import sys
# Developer: SirCryptic (NullSecurityTeam)
# Info: exifmapper requirements installer 1.0 (BETA)

def install(package):
try:
subprocess.check_call([sys.executable, "-m", "pip", "install", package])
print(f"Successfully installed {package}")
except subprocess.CalledProcessError:
print(f"{package} is already installed.")

def main():
# Check if folium is installed
try:
import folium
except ImportError:
install("folium")
# Check if exifread is installed
try:
    import exifread
except ImportError:
    install("exifread")

# Check if requests is installed
try:
    import requests
except ImportError:
    install("requests")

# Check if termcolor is installed
try:
    import termcolor
except ImportError:
    install("termcolor")
if name == "main":
    main()
