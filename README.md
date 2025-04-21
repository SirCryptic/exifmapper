
<p align="center">
  <a href="https://github.com/sircryptic/exifmapper">
    <img src="https://github.com/user-attachments/assets/953ae98b-b3ff-4d16-b98e-9a2dbfca0fc0" alt="ExifMapper"
    onmouseover="this.style.transform='scale(1.05)'; this.style.opacity='0.8';" 
    onmouseout="this.style.transform='scale(1)'; this.style.opacity='1';">
  </a>

<div align="center">
    <a href="https://github.com/sircryptic/exifmapper/stargazers"><img src="https://img.shields.io/github/stars/sircryptic/exifmapper.svg" alt="GitHub stars"></a>
    <a href="https://github.com/sircryptic/exifmapper/network"><img src="https://img.shields.io/github/forks/sircryptic/exifmapper.svg" alt="GitHub forks"></a>
    <a href="https://github.com/sircryptic/exifmapper/watchers"><img src="https://img.shields.io/github/watchers/sircryptic/exifmapper.svg?style=social" alt="GitHub watchers"></a>
    <br>
    <a href="https://github.com/SirCryptic/exifmapper/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
</div>

# ExifMapper

A simple, user-friendly desktop application that lets you extract GPS coordinates from images and display them on an interactive map. Whether your photos are stored locally or hosted online, this tool makes it easy to visualize their locations.
Developed by [SirCryptic](https://github.com/SirCryptic)

## Features
- Load GPS Data: Extract coordinates from local images (e.g., .jpg, .png) or web URLs with EXIF GPS metadata.
- Interactive Map: View locations on a map with customizable styles (OpenStreetMap, Stamen Terrain, CartoDB Positron).
- Add Custom Locations: Manually input latitude and longitude for places without GPS data.
- Edit & Manage: Rename or remove locations from your list.
- Save & Load: Save your locations to a JSON file and load them later.
- Beginner-Friendly: Clear tooltips, examples, and a help section guide new users.
- Supports linux & windows!

## Screenshots
<h1 align="left">Preview</h1>

<center>

<details>
  <summary>Click to expand!</summary>

### Main Interface
![interface](https://github.com/user-attachments/assets/d78bf766-9c08-4deb-847b-a89f32a3e34e)



### Map View
Interactive map displayed in the browser.
![distance](https://github.com/user-attachments/assets/bc7a6d1e-6047-47e2-a4d1-2fea50f31df5)
![heat](https://github.com/user-attachments/assets/5bf115a0-0eba-499a-b6a7-2233a302b11b)
![i-main](https://github.com/user-attachments/assets/2f5a7435-5d24-4f11-908f-1fbe844fb377)

</center>


# Installation
### Prerequisites
- Python 3.11+
- Windows: Just use the compiled .exe unless you want to run from source (note: other OS support possible with source also the exe version isnt up to date as of 16/04/2025).

### Option 1: Run from Source

Clone the Repository:
```
git clone https://github.com/SirCryptic/exifmapper.git 
cd exifmapper 
```

1. Install Dependencies:
```
pip install -r requirements.txt
```
2. Run the Installer:
This is so you can launch from any cli , windows & linux!
```
python setup_exifmapper.py
```

3. Launch The app.

if installed you can launch it using any cli & the cmd below
```
exifmapper
```

### Option 2: Use the Compiled Executable

1. Download the Latest Release:
* Go to [Releases](https://github.com/SirCryptic/exifmapper/releases).
* Download gpsviewer.exe.
* Run the exe (no Python installation needed - outdated gui)

### Usage
1.Load an Image:
* Enter a URL (e.g., https://raw.githubusercontent.com/ianare/exif-samples/master/jpg/gps/DSCN0027.jpg) or local path (e.g., C:\Photos\image.jpg) in the input field or just Click "Browse" to select local files.
* Click "Load Location" to extract GPS data.
2. View the Map:
* Select a map style from the dropdown.
* Click "View Map" to open an interactive map in your browser.
3. Manage Locations:
* Double-click a location in the app istelf to rename it it will reflect on the map in the browser once reloaded.
* Click "Add Custom Location" to enter coordinates manually.
* Select a location and click "Remove Selected" to delete it.
3. Save or Load:
* Click "Save Locations" to save to a .json file.
* Click "Load Saved Locations" to restore from a file.
4. Need Help?:
* Click "Help" for a quick guide.
