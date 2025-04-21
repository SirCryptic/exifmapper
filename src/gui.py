#!/usr/bin/env python3
import sys
import webbrowser
import requests
import io
import base64
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QFileDialog, 
                             QListWidget, QMessageBox, QInputDialog, QComboBox,
                             QProgressDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QColor
from io import BytesIO
import folium
from folium.plugins import FastMarkerCluster, HeatMap, AntPath
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import json
from math import radians, sin, cos, sqrt, atan2
from geopy.geocoders import Nominatim
import simplekml
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import re
from requests.exceptions import RequestException
from PIL import UnidentifiedImageError

class MapUI(QWidget):
    def __init__(self):
        super().__init__()
        self.markers = []  # (location, name, timestamp, altitude, exif_data) tuples
        self.undo_stack = []
        self.redo_stack = []
        self.show_distance_lines = False
        self.show_heatmap = False
        self.last_file = self.load_last_file()
        self.initUI()
        if self.last_file and Path(self.last_file).exists():
            try:
                self.loadSavedData(self.last_file)
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Could not load last file: {str(e)}")

    def initUI(self):
        self.setWindowTitle('ExifMapper')
        main_layout = QGridLayout()

        # Enable drag-and-drop
        self.setAcceptDrops(True)

        # Set Fusion style with dark theme
        app = QApplication.instance()
        app.setStyle('Fusion')
        palette = self.palette()
        palette.setColor(palette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(palette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(palette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(palette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(palette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(palette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(palette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(palette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(palette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(palette)

        # Set window icon
        try:
            icon_path = Path(__file__).parent / 'resources' / 'icon.png'
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass

        # Input Section
        input_layout = QHBoxLayout()
        self.fileInput = QLineEdit(self)
        self.fileInput.setPlaceholderText("Enter image paths or URLs (e.g., https://example.com/image.jpg) or drag-and-drop images")
        self.fileInput.setToolTip("Enter comma-separated image paths/URLs with GPS data or drag-and-drop images.")
        self.fileInput.setText("https://raw.githubusercontent.com/ianare/exif-samples/master/jpg/gps/DSCN0027.jpg")
        input_layout.addWidget(self.fileInput)
        browseButton = QPushButton('Browse Files', self)
        browseButton.clicked.connect(self.browseFiles)
        browseButton.setToolTip("Browse for local image files with GPS data.")
        input_layout.addWidget(browseButton)
        folderButton = QPushButton('Process Folder', self)
        folderButton.clicked.connect(self.processFolder)
        folderButton.setToolTip("Recursively load all images from a folder.")
        input_layout.addWidget(folderButton)
        main_layout.addLayout(input_layout, 0, 0, 1, 2)

        # Action Buttons
        action_layout = QHBoxLayout()
        loadButton = QPushButton('Load Location', self)
        loadButton.clicked.connect(self.loadGPSData)
        loadButton.setToolTip("Add GPS data from the images above to the list.")
        action_layout.addWidget(loadButton)
        displayMapButton = QPushButton('View Map', self)
        displayMapButton.clicked.connect(self.displayMap)
        displayMapButton.setToolTip("Display all loaded locations on a map.")
        action_layout.addWidget(displayMapButton)
        self.mapTiles = QComboBox(self)
        self.mapTiles.addItems(['OpenStreetMap', 'Stamen Terrain', 'CartoDB Positron'])
        self.mapTiles.setCurrentText('OpenStreetMap')
        self.mapTiles.setToolTip("Select the map style for viewing.")
        action_layout.addWidget(QLabel('Map Style:'))
        action_layout.addWidget(self.mapTiles)
        main_layout.addLayout(action_layout, 1, 0, 1, 2)

        # Status Label
        self.statusLabel = QLabel(f"Loaded Locations: {len(self.markers)}", self)
        main_layout.addWidget(self.statusLabel, 2, 0, 1, 2)

        # Marker List
        main_layout.addWidget(QLabel('Locations:'), 3, 0, 1, 2)
        self.fileList = QListWidget(self)
        self.fileList.itemDoubleClicked.connect(self.editMarker)
        self.fileList.setToolTip("Double-click to rename a location; all loaded locations appear here.")
        self.fileList.setMinimumHeight(150)
        main_layout.addWidget(self.fileList, 4, 0, 1, 2)

        # Marker Management Buttons
        marker_buttons = QHBoxLayout()
        addMarkerButton = QPushButton('Add Custom Location', self)
        addMarkerButton.clicked.connect(self.addMarker)
        addMarkerButton.setToolTip("Manually add a location with custom coordinates.")
        marker_buttons.addWidget(addMarkerButton)
        geocodeButton = QPushButton('Add by Address', self)
        geocodeButton.clicked.connect(self.addGeocodedLocation)
        geocodeButton.setToolTip("Add a location by entering an address.")
        marker_buttons.addWidget(geocodeButton)
        removeMarkerButton = QPushButton('Remove Selected', self)
        removeMarkerButton.clicked.connect(self.removeMarker)
        removeMarkerButton.setToolTip("Remove the currently selected location.")
        marker_buttons.addWidget(removeMarkerButton)
        clearButton = QPushButton('Clear All', self)
        clearButton.clicked.connect(self.clearAll)
        clearButton.setToolTip("Remove all locations from the list.")
        marker_buttons.addWidget(clearButton)
        undoButton = QPushButton('Undo', self)
        undoButton.clicked.connect(self.undo)
        undoButton.setToolTip("Undo the last action (add/remove/edit).")
        marker_buttons.addWidget(undoButton)
        redoButton = QPushButton('Redo', self)
        redoButton.clicked.connect(self.redo)
        redoButton.setToolTip("Redo the last undone action.")
        marker_buttons.addWidget(redoButton)
        distanceButton = QPushButton('Calculate Distance', self)
        distanceButton.clicked.connect(self.calculateDistance)
        distanceButton.setToolTip("Calculate total distance between all locations in miles.")
        marker_buttons.addWidget(distanceButton)
        toggleDistanceButton = QPushButton('Toggle Distance Lines', self)
        toggleDistanceButton.clicked.connect(self.toggleDistanceLines)
        toggleDistanceButton.setToolTip("Show/hide distance lines on the map.")
        marker_buttons.addWidget(toggleDistanceButton)
        toggleHeatmapButton = QPushButton('Toggle Heatmap', self)
        toggleHeatmapButton.clicked.connect(self.toggleHeatmap)
        toggleHeatmapButton.setToolTip("Show/hide heatmap overlay on the map.")
        marker_buttons.addWidget(toggleHeatmapButton)
        main_layout.addLayout(marker_buttons, 5, 0, 1, 2)

        # Save/Load Buttons
        save_load_layout = QHBoxLayout()
        saveButton = QPushButton('Save Locations', self)
        saveButton.clicked.connect(self.saveData)
        saveButton.setToolTip("Save all locations to a JSON file.")
        save_load_layout.addWidget(saveButton)
        exportKMLButton = QPushButton('Export to KML', self)
        exportKMLButton.clicked.connect(self.exportKML)
        exportKMLButton.setToolTip("Export locations to KML for Google Earth.")
        save_load_layout.addWidget(exportKMLButton)
        loadSavedButton = QPushButton('Load Saved Locations', self)
        loadSavedButton.clicked.connect(lambda: self.loadSavedData())
        loadSavedButton.setToolTip("Add locations from a saved JSON file.")
        save_load_layout.addWidget(loadSavedButton)
        helpButton = QPushButton('Help', self)
        helpButton.clicked.connect(self.showHelp)
        helpButton.setToolTip("View instructions for using the app.")
        save_load_layout.addWidget(helpButton)
        main_layout.addLayout(save_load_layout, 6, 0, 1, 2)

        self.setLayout(main_layout)
        self.setGeometry(100, 100, 1000, 600)
        self.setMinimumSize(1000, 600)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile().lower()
                if file_path.endswith(('.png', '.jpg', '.jpeg')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        files = [urllib.parse.unquote(url.toLocalFile()) for url in event.mimeData().urls() 
                 if url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg'))]
        if files:
            self.fileInput.setText(", ".join(files))
            QMessageBox.information(self, "Success", f"Dropped {len(files)} image(s). Click 'Load Location' to process.")
        else:
            QMessageBox.warning(self, "Invalid Drop", "No valid image files dropped.")
        event.acceptProposedAction()

    def browseFiles(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg)")
        if files:
            self.fileInput.setText(", ".join(files))
            QMessageBox.information(self, "Success", f"Selected {len(files)} image(s). Click 'Load Location' to process.")
        else:
            QMessageBox.information(self, "No Selection", "No files selected.")

    def processFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            try:
                image_files = []
                extensions = ('*.png', '*.jpg', '*.jpeg')
                # Initialize progress dialog
                progress = QProgressDialog("Scanning folder for images...", "Cancel", 0, 0, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                progress.show()
                QApplication.processEvents()

                for ext in extensions:
                    for file in Path(folder).rglob(ext):
                        image_files.append(str(file))
                        progress.setValue(progress.value() + 1)
                        QApplication.processEvents()
                        if progress.wasCanceled():
                            progress.close()
                            QMessageBox.information(self, "Cancelled", "Folder processing cancelled.")
                            return

                progress.close()
                if image_files:
                    self.fileInput.setText(", ".join(image_files))
                    QMessageBox.information(self, "Success", f"Found {len(image_files)} image(s). Click 'Load Location' to process.")
                else:
                    QMessageBox.warning(self, "No Images", "No images found in the selected folder!")
            except Exception as e:
                QMessageBox.critical(self, "Folder Error", f"Failed to process folder: {str(e)}")
        else:
            QMessageBox.information(self, "No Selection", "No folder selected.")

    def is_valid_url(self, url):
        """Check if the input is a valid URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.scheme in ('http', 'https') and bool(re.match(r'^[\w\-\.\:\/]+$', parsed.netloc))
        except Exception:
            return False

    def loadGPSData(self):
        self.undo_stack.append(self.markers.copy())
        self.redo_stack.clear()
        inputs = [x.strip() for x in self.fileInput.text().split(',')]
        if not inputs or all(not x for x in inputs):
            QMessageBox.warning(self, "Oops", "Please enter an image URL or path first!")
            return
        
        validated_inputs = []
        from_file_flags = []
        for item in inputs:
            if self.is_valid_url(item):
                validated_inputs.append(item)
                from_file_flags.append(False)
            elif Path(item).is_file():
                validated_inputs.append(item)
                from_file_flags.append(True)
            else:
                self.fileList.addItem(f"{item} - Invalid URL or file path")

        if not validated_inputs:
            QMessageBox.warning(self, "No Valid Inputs", "No valid URLs or file paths found!")
            return

        new_locations = 0
        try:
            with ThreadPoolExecutor() as executor:
                results = executor.map(self.get_loc, validated_inputs, from_file_flags)
            for item, result in zip(validated_inputs, results):
                try:
                    if result is None:
                        self.fileList.addItem(f"{item} - No GPS Data Found")
                        continue
                    loc, timestamp, altitude, exif_data = result
                    if loc:
                        if not self.is_duplicate(loc, item):
                            self.markers.append((loc, item, timestamp, altitude, exif_data))
                            self.fileList.addItem(item)
                            new_locations += 1
                        else:
                            reply = QMessageBox.question(self, "Duplicate Found", 
                                                        f"'{item}' already exists. Overwrite?", 
                                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                                        QMessageBox.StandardButton.No)
                            if reply == QMessageBox.StandardButton.Yes:
                                self.removeMarkerByName(item)
                                self.markers.append((loc, item, timestamp, altitude, exif_data))
                                self.fileList.addItem(item)
                                new_locations += 1
                    else:
                        self.fileList.addItem(f"{item} - No GPS Data Found")
                except RequestException as e:
                    self.fileList.addItem(f"{item} - Network Error: {str(e)}")
                except FileNotFoundError:
                    self.fileList.addItem(f"{item} - File not found")
                except UnidentifiedImageError:
                    self.fileList.addItem(f"{item} - Invalid image format")
                except Exception as e:
                    self.fileList.addItem(f"{item} - Error: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Processing Error", f"Failed to process images: {str(e)}")
            return

        self.updateStatus()
        if new_locations > 0:
            QMessageBox.information(self, "Success", f"Added {new_locations} new location(s).")
            self.fileInput.clear()
        elif self.markers:
            QMessageBox.information(self, "No New Locations", "No new GPS data added.")
        else:
            QMessageBox.warning(self, "No Locations", "No GPS data found. Try another image.")

    def get_loc(self, file_or_url, from_file=True):
        try:
            exif_data = None
            if from_file:
                with Image.open(file_or_url) as img:
                    img.verify()  # Validate image
                    img = Image.open(file_or_url)  # Reopen after verification
                    exif_data = img._getexif()
            else:
                response = requests.get(file_or_url, timeout=5)
                response.raise_for_status()
                img_data = BytesIO(response.content)
                with Image.open(img_data) as img:
                    img.verify()  # Validate image
                    img = Image.open(BytesIO(response.content))  # Reopen after verification
                    exif_data = img._getexif()
            
            if not exif_data:
                return None, None, None, None

            exif_data = {TAGS.get(tag, tag): value for tag, value in exif_data.items()}
            loc, altitude = self.get_gps_data(exif_data)
            timestamp = exif_data.get('DateTime', None)
            additional_exif = {
                'CameraModel': exif_data.get('Model', 'N/A'),
                'Exposure': exif_data.get('ExposureTime', 'N/A')
            }
            return loc, timestamp, altitude, additional_exif
        except FileNotFoundError:
            raise
        except UnidentifiedImageError:
            raise
        except RequestException as e:
            raise
        except Exception as e:
            raise Exception(f"Processing failed: {str(e)}")

    def get_gps_data(self, tags):
        if 'GPSInfo' not in tags or not tags['GPSInfo']:
            return None, None
        gps_info = {GPSTAGS.get(key, key): value for key, value in tags['GPSInfo'].items()}
        lat = gps_info.get('GPSLatitude')
        lat_ref = gps_info.get('GPSLatitudeRef')
        lon = gps_info.get('GPSLongitude')
        lon_ref = gps_info.get('GPSLongitudeRef')
        alt = gps_info.get('GPSAltitude')
        if lat and lat_ref and lon and lon_ref:
            try:
                lat = self.convert_to_degrees(lat, lat_ref)
                lon = self.convert_to_degrees(lon, lon_ref)
                alt_value = float(alt) if alt else None
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    return None, None
                return [lat, lon], alt_value
            except (ValueError, TypeError):
                return None, None
        return None, None

    def convert_to_degrees(self, value, ref):
        try:
            d, m, s = value
            degrees = float(d)
            minutes = float(m) / 60.0
            seconds = float(s) / 3600.0
            result = degrees + minutes + seconds
            if ref in ['S', 'W']:
                result = -result
            return result
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid GPS coordinate format: {str(e)}")

    def compress_image(self, file_path, max_width=100):
        try:
            with Image.open(file_path) as img:
                img.verify()  # Validate image
                img = Image.open(file_path)  # Reopen after verification
                img.thumbnail((max_width, max_width))
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=75)
                return buffer.getvalue()
        except FileNotFoundError:
            return None
        except UnidentifiedImageError:
            return None
        except Exception:
            return None

    def displayMap(self):
        if not self.markers:
            QMessageBox.warning(self, "Oops", "No locations loaded yet!")
            return
        try:
            avg_lat = sum(m[0][0] for m in self.markers) / len(self.markers)
            avg_lon = sum(m[0][1] for m in self.markers) / len(self.markers)
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
            tile_choice = self.mapTiles.currentText()
            if tile_choice == 'OpenStreetMap':
                folium.TileLayer(tiles='openstreetmap', attr='© OpenStreetMap contributors').add_to(m)
            elif tile_choice == 'Stamen Terrain':
                folium.TileLayer(tiles='stamen terrain', attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.').add_to(m)
            elif tile_choice == 'CartoDB Positron':
                folium.TileLayer(tiles='cartodb positron', attr='© CartoDB, © OpenStreetMap contributors').add_to(m)
            
            marker_cluster = FastMarkerCluster([]).add_to(m)
            for loc, name, timestamp, altitude, exif_data in self.markers:
                popup_text = f"<b>{name}</b>"
                if timestamp:
                    try:
                        date, time = timestamp.split(" ")
                        popup_text += f"<br>Time: {time}<br>Date: {date.replace(':', '-')}"
                    except ValueError:
                        popup_text += f"<br>Timestamp: {timestamp}"
                if altitude is not None:
                    popup_text += f"<br>Altitude: {altitude:.1f} m"
                if exif_data:
                    popup_text += f"<br>Camera: {exif_data['CameraModel']}<br>Exposure: {exif_data['Exposure']}"
                if name.startswith(('http://', 'https://')):
                    popup_text += f"<br><img src='{name}' width='100'>"
                else:
                    try:
                        img_data = self.compress_image(name)
                        if img_data:
                            img_b64 = base64.b64encode(img_data).decode('utf-8')
                            popup_text += f"<br><img src='data:image/jpeg;base64,{img_b64}' width='100'>"
                    except Exception:
                        pass
                folium.Marker(loc, popup=folium.Popup(popup_text, max_width=300)).add_to(marker_cluster)
            
            if self.show_distance_lines and len(self.markers) >= 2:
                total_distance = 0
                coords = [marker[0] for marker in self.markers]
                for i in range(len(coords) - 1):
                    lat1, lon1 = map(radians, coords[i])
                    lat2, lon2 = map(radians, coords[i + 1])
                    dlat, dlon = lat2 - lat1, lon2 - lon1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * atan2(sqrt(a), sqrt(1-a))
                    distance_km = 6371 * c
                    distance_miles = distance_km * 0.621371
                    total_distance += distance_miles
                AntPath(coords, tooltip=f"Total Distance: {total_distance:.2f} miles", color='red').add_to(m)
            
            if self.show_heatmap:
                heat_data = [[loc[0], loc[1]] for loc, _, _, _, _ in self.markers]
                HeatMap(heat_data).add_to(m)

            temp_html = Path('temp_map.html')
            m.save(str(temp_html))
            webbrowser.open(temp_html.absolute().as_uri())
            QMessageBox.information(self, "Map Ready", "Map opened in your browser!")
        except Exception as e:
            QMessageBox.critical(self, "Map Error", f"Failed to display map: {str(e)}")
        finally:
            if temp_html.exists():
                try:
                    temp_html.unlink()
                except Exception:
                    pass

    def saveData(self):
        if not self.markers:
            QMessageBox.warning(self, "Oops", "No locations to save!")
            return
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Your Locations", "", "JSON Files (*.json)")
        if fileName:
            try:
                with open(fileName, 'w') as f:
                    json.dump(self.markers, f)
                self.last_file = fileName
                self.save_last_file(fileName)
                QMessageBox.information(self, "Saved", f"Locations saved to {fileName}!")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Couldn’t save: {str(e)}")

    def exportKML(self):
        if not self.markers:
            QMessageBox.warning(self, "Oops", "No locations to export!")
            return
        fileName, _ = QFileDialog.getSaveFileName(self, "Export to KML", "", "KML Files (*.kml)")
        if fileName:
            try:
                kml = simplekml.Kml()
                for loc, name, timestamp, altitude, exif_data in self.markers:
                    pnt = kml.newpoint(name=name, coords=[(loc[1], loc[0], altitude or 0)])
                    description = []
                    if timestamp:
                        try:
                            date, time = timestamp.split(" ")
                            description.append(f"Time: {time}\nDate: {date.replace(':', '-')}")
                        except ValueError:
                            description.append(f"Timestamp: {timestamp}")
                    if altitude is not None:
                        description.append(f"Altitude: {altitude:.1f} m")
                    if exif_data:
                        description.append(f"Camera: {exif_data['CameraModel']}\nExposure: {exif_data['Exposure']}")
                    pnt.description = "\n".join(description)
                kml.save(fileName)
                QMessageBox.information(self, "Exported", f"Locations exported to {fileName}!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Couldn’t export: {str(e)}")

    def loadSavedData(self, fileName=None):
        self.undo_stack.append(self.markers.copy())
        self.redo_stack.clear()
        if not fileName:
            fileName, _ = QFileDialog.getOpenFileName(self, "Load Saved Locations", "", "JSON Files (*.json)")
        if fileName:
            try:
                with open(fileName, 'r') as f:
                    new_markers = json.load(f)
                new_locations = 0
                for marker in new_markers:
                    if not isinstance(marker, list) or len(marker) < 2:
                        continue
                    loc, name = marker[0], marker[1]
                    timestamp = marker[2] if len(marker) > 2 else None
                    altitude = marker[3] if len(marker) > 3 else None
                    exif_data = marker[4] if len(marker) > 4 else None
                    if not isinstance(loc, list) or len(loc) != 2:
                        continue
                    if not self.is_duplicate(loc, name):
                        self.markers.append((loc, name, timestamp, altitude, exif_data))
                        self.fileList.addItem(name)
                        new_locations += 1
                    else:
                        reply = QMessageBox.question(self, "Duplicate Found", 
                                                    f"'{name}' already exists. Overwrite?", 
                                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                                    QMessageBox.StandardButton.No)
                        if reply == QMessageBox.StandardButton.Yes:
                            self.removeMarkerByName(name)
                            self.markers.append((loc, name, timestamp, altitude, exif_data))
                            self.fileList.addItem(name)
                            new_locations += 1
                self.updateStatus()
                self.last_file = fileName
                self.save_last_file(fileName)
                QMessageBox.information(self, "Loaded", f"Added {new_locations} location(s) from {fileName}!")
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Load Error", f"Invalid JSON format in {fileName}")
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Couldn’t load: {str(e)}")

    def editMarker(self, item):
        self.undo_stack.append(self.markers.copy())
        self.redo_stack.clear()
        current_name = item.text()
        new_name, ok = QInputDialog.getText(self, 'Rename Location', 'New name:', text=current_name)
        if ok and new_name:
            try:
                for i, (loc, name, timestamp, altitude, exif_data) in enumerate(self.markers):
                    if name == current_name:
                        self.markers[i] = (loc, new_name, timestamp, altitude, exif_data)
                        break
                self.fileList.item(self.fileList.row(item)).setText(new_name)
                self.updateStatus()
                QMessageBox.information(self, "Renamed", f"Changed to '{new_name}'!")
            except Exception as e:
                QMessageBox.critical(self, "Rename Error", f"Failed to rename: {str(e)}")

    def addMarker(self):
        self.undo_stack.append(self.markers.copy())
        self.redo_stack.clear()
        dialog = QInputDialog(self)
        dialog.setLabelText("Location name:")
        dialog.setTextValue("New Place")
        if dialog.exec():
            name = dialog.textValue()
            if not name:
                QMessageBox.warning(self, "Oops", "Please enter a name!")
                return
            dialog = QInputDialog(self)
            dialog.setLabelText("Latitude (e.g., 40.7128, -90 to 90):")
            dialog.setTextValue("40.7128")
            if dialog.exec():
                try:
                    lat = float(dialog.textValue())
                    if not -90 <= lat <= 90:
                        raise ValueError("Latitude must be between -90 and 90.")
                except ValueError as e:
                    QMessageBox.warning(self, "Invalid Input", f"Bad latitude: {str(e)}")
                    return
                dialog = QInputDialog(self)
                dialog.setLabelText("Longitude (e.g., -74.0060, -180 to 180):")
                dialog.setTextValue("-74.0060")
                if dialog.exec():
                    try:
                        lon = float(dialog.textValue())
                        if not -180 <= lon <= 180:
                            raise ValueError("Longitude must be between -180 and 180.")
                        loc = [lat, lon]
                        if not self.is_duplicate(loc, name):
                            self.markers.append((loc, name, None, None, None))
                            self.fileList.addItem(name)
                            self.updateStatus()
                            QMessageBox.information(self, "Added", f"Added '{name}' at {lat}, {lon}!")
                        else:
                            QMessageBox.warning(self, "Duplicate", f"'{name}' with those coordinates already exists!")
                    except ValueError as e:
                        QMessageBox.warning(self, "Invalid Input", f"Bad longitude: {str(e)}")

    def addGeocodedLocation(self):
        self.undo_stack.append(self.markers.copy())
        self.redo_stack.clear()
        geolocator = Nominatim(user_agent="MapUI")
        address, ok = QInputDialog.getText(self, "Geocode", "Enter an address:")
        if ok and address:
            try:
                location = geolocator.geocode(address, timeout=5)
                if location:
                    loc = [location.latitude, location.longitude]
                    if not self.is_duplicate(loc, address):
                        self.markers.append((loc, address, None, None, None))
                        self.fileList.addItem(address)
                        self.updateStatus()
                        QMessageBox.information(self, "Added", f"Added '{address}' at {loc[0]}, {loc[1]}!")
                    else:
                        QMessageBox.warning(self, "Duplicate", f"'{address}' already exists!")
                else:
                    QMessageBox.warning(self, "Error", "Address not found!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Geocoding failed: {str(e)}")

    def removeMarker(self):
        self.undo_stack.append(self.markers.copy())
        self.redo_stack.clear()
        item = self.fileList.currentItem()
        if not item:
            QMessageBox.warning(self, "Oops", "Select a location to remove!")
            return
        name = item.text()
        self.removeMarkerByName(name)
        self.fileList.takeItem(self.fileList.row(item))
        self.updateStatus()
        QMessageBox.information(self, "Removed", f"Removed '{name}'!")

    def removeMarkerByName(self, name):
        for i, (_, marker_name, _, _, _) in enumerate(self.markers):
            if marker_name == name:
                del self.markers[i]
                break

    def clearAll(self):
        if not self.markers:
            QMessageBox.information(self, "Nothing to Clear", "No locations loaded!")
            return
        reply = QMessageBox.question(self, "Confirm Clear", "Remove all locations?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.undo_stack.append(self.markers.copy())
            self.redo_stack.clear()
            self.markers = []
            self.fileList.clear()
            self.updateStatus()
            QMessageBox.information(self, "Cleared", "All locations removed!")

    def undo(self):
        if not self.undo_stack:
            QMessageBox.information(self, "Nothing to Undo", "No actions to undo!")
            return
        self.redo_stack.append(self.markers.copy())
        self.markers = self.undo_stack.pop()
        self.fileList.clear()
        for _, name, _, _, _ in self.markers:
            self.fileList.addItem(name)
        self.updateStatus()
        QMessageBox.information(self, "Undo", "Last action undone!")

    def redo(self):
        if not self.redo_stack:
            QMessageBox.information(self, "Nothing to Redo", "No actions to redo!")
            return
        self.undo_stack.append(self.markers.copy())
        self.markers = self.redo_stack.pop()
        self.fileList.clear()
        for _, name, _, _, _ in self.markers:
            self.fileList.addItem(name)
        self.updateStatus()
        QMessageBox.information(self, "Redo", "Last undone action redone!")

    def calculateDistance(self):
        if len(self.markers) < 2:
            QMessageBox.warning(self, "Oops", "Need at least 2 locations to calculate distance!")
            return
        try:
            total_distance = 0
            for i in range(len(self.markers) - 1):
                lat1, lon1 = map(radians, self.markers[i][0])
                lat2, lon2 = map(radians, self.markers[i + 1][0])
                dlat, dlon = lat2 - lat1, lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                distance_km = 6371 * c
                distance_miles = distance_km * 0.621371
                total_distance += distance_miles
            QMessageBox.information(self, "Distance", f"Total distance: {total_distance:.2f} miles")
        except Exception as e:
            QMessageBox.critical(self, "Distance Error", f"Failed to calculate distance: {str(e)}")

    def toggleDistanceLines(self):
        self.show_distance_lines = not self.show_distance_lines
        self.displayMap()
        state = "on" if self.show_distance_lines else "off"
        QMessageBox.information(self, "Distance Lines", f"Distance lines turned {state}")

    def toggleHeatmap(self):
        self.show_heatmap = not self.show_heatmap
        self.displayMap()
        state = "on" if self.show_heatmap else "off"
        QMessageBox.information(self, "Heatmap", f"Heatmap turned {state}")

    def is_duplicate(self, loc, name):
        for existing_loc, existing_name, _, _, _ in self.markers:
            if (abs(existing_loc[0] - loc[0]) < 0.0001 and 
                abs(existing_loc[1] - loc[1]) < 0.0001 and 
                existing_name == name):
                return True
        return False

    def updateStatus(self):
        self.statusLabel.setText(f"Loaded Locations: {len(self.markers)}")

    def showHelp(self):
        help_text = (
            "Welcome to ExifMapper!\n\n"
            "1. **Load Locations**: Enter image URLs/paths, drag-and-drop images, process a folder, or click 'Load Location'.\n"
            "2. **View Map**: See locations with time/date, altitude, camera info, and previews.\n"
            "3. **Add Custom**: Add via coordinates or address (geocoding).\n"
            "4. **Edit**: Double-click to rename.\n"
            "5. **Save/Load/Export**: Save to JSON, load, or export to KML.\n"
            "6. **Remove/Clear**: Remove one or all locations.\n"
            "7. **Undo/Redo**: Undo or redo actions.\n"
            "8. **Distance**: Calculate distance in miles or toggle lines.\n"
            "9. **Heatmap**: Toggle heatmap overlay.\n"
            "Tip: Images need GPS EXIF data."
        )
        QMessageBox.information(self, "How to Use", help_text)

    def load_last_file(self):
        last_file = Path('last_file.txt')
        if last_file.exists():
            try:
                return last_file.read_text().strip()
            except Exception:
                return None
        return None

    def save_last_file(self, path):
        try:
            Path('last_file.txt').write_text(path)
        except Exception:
            pass

def main():
    try:
        app = QApplication(sys.argv)
        ex = MapUI()
        ex.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", f"Application failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
