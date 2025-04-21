from setuptools import setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="exifmapper",
    version="1.0.0",
    packages=["exifmapper"],
    package_dir={"exifmapper": "src"},
    include_package_data=True,
    package_data={
        "exifmapper": [
            "resources/icon.png",
            "gui.py",
        ],
    },
    install_requires=[
        "PyQt6>=6.7.0",
        "requests>=2.31.0",
        "Pillow>=10.2.0",
        "folium>=0.15.0",
        "geopy>=2.4.0",
        "simplekml>=1.3.6",
    ],
    entry_points={
        "console_scripts": [
            "exifmapper=exifmapper.gui:main",
        ],
    },
    author="SirCryptic",
    author_email="sircryptic@protonmail.com",
    description="A desktop application to extract GPS coordinates from images and display them on an interactive map",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SirCryptic/exifmapper",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.11",
)