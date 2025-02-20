import sys
import webbrowser
import requests
import io
import os
import logging
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QFileDialog, 
                             QListWidget, QMessageBox, QInputDialog, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon, QPixmap
from io import BytesIO
import folium
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import json

# Setup basic logging
logging.basicConfig(filename='errors.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class MapUI(QWidget):
    def __init__(self):
        super().__init__()
        self.markers = []  # Now stores (location, name, timestamp) tuples
        self.last_file = self.load_last_file()
        self.initUI()
        if self.last_file and os.path.exists(self.last_file):
            self.loadSavedData(self.last_file)

    def initUI(self):
        self.setWindowTitle('Easy GPS Map Viewer')
        main_layout = QVBoxLayout()

        # Palette for consistent look
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(45, 45, 45))
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(0, 0, 0))
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.Active, QPalette.Text, Qt.black)
        palette.setColor(QPalette.Active, QPalette.Base, Qt.white)
        self.setPalette(palette)

        # Set window icon
        icon_url = "https://user-images.githubusercontent.com/48811414/219992613-de266069-beaa-4071-ac2c-8b563fb441ac.png"
        try:
            response = requests.get(icon_url, timeout=5)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data.getvalue())
            if not pixmap.isNull():
                self.setWindowIcon(QIcon(pixmap))
        except Exception as e:
            logging.error(f"Error setting window icon: {str(e)}")

        # Input Section
        input_layout = QHBoxLayout()
        self.fileInput = QLineEdit(self)
        self.fileInput.setPlaceholderText("Enter image paths or URLs (e.g., https://example.com/image.jpg)")
        self.fileInput.setToolTip("Enter comma-separated image paths/URLs with GPS data.")
        self.fileInput.setText("https://raw.githubusercontent.com/ianare/exif-samples/master/jpg/gps/DSCN0027.jpg")
        input_layout.addWidget(self.fileInput)
        browseButton = QPushButton('Browse', self)
        browseButton.clicked.connect(self.browseFiles)
        browseButton.setToolTip("Browse for local image files with GPS data.")
        input_layout.addWidget(browseButton)
        main_layout.addLayout(input_layout)

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
        main_layout.addLayout(action_layout)

        # Status Label
        self.statusLabel = QLabel(f"Loaded Locations: {len(self.markers)}", self)
        main_layout.addWidget(self.statusLabel)

        # Marker List
        main_layout.addWidget(QLabel('Locations:'))
        self.fileList = QListWidget(self)
        self.fileList.itemDoubleClicked.connect(self.editMarker)
        self.fileList.setToolTip("Double-click to rename a location; all loaded locations appear here.")
        main_layout.addWidget(self.fileList)

        # Marker Management Buttons
        marker_buttons = QHBoxLayout()
        addMarkerButton = QPushButton('Add Custom Location', self)
        addMarkerButton.clicked.connect(self.addMarker)
        addMarkerButton.setToolTip("Manually add a location with custom coordinates.")
        marker_buttons.addWidget(addMarkerButton)
        removeMarkerButton = QPushButton('Remove Selected', self)
        removeMarkerButton.clicked.connect(self.removeMarker)
        removeMarkerButton.setToolTip("Remove the currently selected location.")
        marker_buttons.addWidget(removeMarkerButton)
        clearButton = QPushButton('Clear All', self)
        clearButton.clicked.connect(self.clearAll)
        clearButton.setToolTip("Remove all locations from the list.")
        marker_buttons.addWidget(clearButton)
        main_layout.addLayout(marker_buttons)

        # Save/Load Buttons
        save_load_layout = QHBoxLayout()
        saveButton = QPushButton('Save Locations', self)
        saveButton.clicked.connect(self.saveData)
        saveButton.setToolTip("Save all locations to a JSON file.")
        save_load_layout.addWidget(saveButton)
        loadSavedButton = QPushButton('Load Saved Locations', self)
        loadSavedButton.clicked.connect(lambda: self.loadSavedData())
        loadSavedButton.setToolTip("Add locations from a saved JSON file.")
        save_load_layout.addWidget(loadSavedButton)
        helpButton = QPushButton('Help', self)
        helpButton.clicked.connect(self.showHelp)
        helpButton.setToolTip("View instructions for using the app.")
        save_load_layout.addWidget(helpButton)
        main_layout.addLayout(save_load_layout)

        self.setLayout(main_layout)
        self.setGeometry(300, 300, 600, 400)

    def browseFiles(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg)")
        if files:
            self.fileInput.setText(", ".join(files))
            QMessageBox.information(self, "Success", f"Selected {len(files)} image(s). Click 'Load Location' to process.")

    def loadGPSData(self):
        inputs = [x.strip() for x in self.fileInput.text().split(',')]
        if not inputs or all(not x for x in inputs):
            QMessageBox.warning(self, "Oops", "Please enter an image URL or path first!")
            return
        new_locations = 0
        for item in inputs:
            try:
                if item.startswith('http'):
                    if 'github.com' in item and '/blob/' in item:
                        item = item.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                    loc, timestamp = self.get_loc(item, from_file=False)
                else:
                    if not os.path.exists(item):
                        raise FileNotFoundError(f"File not found: {item}")
                    loc, timestamp = self.get_loc(item, from_file=True)
                if loc:
                    if not self.is_duplicate(loc, item):
                        self.markers.append((loc, item, timestamp))
                        self.fileList.addItem(item)
                        new_locations += 1
                    else:
                        reply = QMessageBox.question(self, "Duplicate Found", 
                                                    f"'{item}' already exists. Overwrite?", 
                                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            self.removeMarkerByName(item)
                            self.markers.append((loc, item, timestamp))
                            self.fileList.addItem(item)
                            new_locations += 1
                else:
                    self.fileList.addItem(f"{item} - No GPS Data Found")
            except requests.RequestException as e:
                self.fileList.addItem(f"{item} - Network Error: {str(e)}")
                logging.error(f"Network error loading {item}: {str(e)}")
            except FileNotFoundError as e:
                self.fileList.addItem(f"{item} - {str(e)}")
            except Exception as e:
                self.fileList.addItem(f"{item} - Error: {str(e)}")
                logging.error(f"Error loading {item}: {str(e)}")
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
            if from_file:
                with Image.open(file_or_url) as img:
                    exif_data = img._getexif()
                    if not exif_data:
                        return None, None
                    exif_data = {TAGS.get(tag, tag): value for tag, value in exif_data.items()}
            else:
                response = requests.get(file_or_url, timeout=5)
                response.raise_for_status()
                img_data = io.BytesIO(response.content)
                with Image.open(img_data) as img:
                    exif_data = img._getexif()
                    if not exif_data:
                        return None, None
                    exif_data = {TAGS.get(tag, tag): value for tag, value in exif_data.items()}
            loc = self.get_gps_data(exif_data)
            timestamp = exif_data.get('DateTime', None)  # e.g., "2023:01:15 14:30:45"
            return loc, timestamp
        except Exception as e:
            raise Exception(f"Processing failed: {str(e)}")

    def get_gps_data(self, tags):
        if 'GPSInfo' not in tags or not tags['GPSInfo']:
            return None
        gps_info = {GPSTAGS.get(key, key): value for key, value in tags['GPSInfo'].items()}
        lat = gps_info.get('GPSLatitude')
        lat_ref = gps_info.get('GPSLatitudeRef')
        lon = gps_info.get('GPSLongitude')
        lon_ref = gps_info.get('GPSLongitudeRef')
        if lat and lat_ref and lon and lon_ref:
            try:
                lat = self.convert_to_degrees(lat, lat_ref)
                lon = self.convert_to_degrees(lon, lon_ref)
                return [lat, lon]
            except Exception as e:
                logging.error(f"GPS conversion error: {str(e)}")
        return None

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
            for loc, name, timestamp in self.markers:
                popup_text = f"<b>{name}</b>"
                if timestamp:
                    date, time = timestamp.split(" ")
                    date = date.replace(":", "-")  # Convert "YYYY:MM:DD" to "YYYY-MM-DD"
                    popup_text += f"<br>Time: {time}<br>Date: {date}"
                folium.Marker(loc, popup=popup_text).add_to(m)
            temp_html = 'temp_map.html'
            m.save(temp_html)
            webbrowser.open('file://' + os.path.realpath(temp_html))
            QMessageBox.information(self, "Map Ready", "Map opened in your browser!")
        except Exception as e:
            QMessageBox.critical(self, "Map Error", f"Failed to display map: {str(e)}")
            logging.error(f"Map display error: {str(e)}")
        finally:
            if os.path.exists('temp_map.html'):
                try:
                    os.remove('temp_map.html')
                except Exception as e:
                    logging.error(f"Couldn’t remove temp_map.html: {str(e)}")

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
                logging.error(f"Save error: {str(e)}")

    def loadSavedData(self, fileName=None):
        if not fileName:
            fileName, _ = QFileDialog.getOpenFileName(self, "Load Saved Locations", "", "JSON Files (*.json)")
        if fileName:
            try:
                with open(fileName, 'r') as f:
                    new_markers = json.load(f)
                new_locations = 0
                for marker in new_markers:
                    loc, name = marker[0], marker[1]
                    timestamp = marker[2] if len(marker) > 2 else None  # Backward compatibility
                    if not self.is_duplicate(loc, name):
                        self.markers.append((loc, name, timestamp))
                        self.fileList.addItem(name)
                        new_locations += 1
                    else:
                        reply = QMessageBox.question(self, "Duplicate Found", 
                                                    f"'{name}' already exists. Overwrite?", 
                                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            self.removeMarkerByName(name)
                            self.markers.append((loc, name, timestamp))
                            self.fileList.addItem(name)
                            new_locations += 1
                self.updateStatus()
                self.last_file = fileName
                self.save_last_file(fileName)
                QMessageBox.information(self, "Loaded", f"Added {new_locations} location(s) from {fileName}!")
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Couldn’t load: {str(e)}")
                logging.error(f"Load error: {str(e)}")

    def editMarker(self, item):
        current_name = item.text()
        new_name, ok = QInputDialog.getText(self, 'Rename Location', 'New name:', text=current_name)
        if ok and new_name:
            for i, (loc, name, timestamp) in enumerate(self.markers):
                if name == current_name:
                    self.markers[i] = (loc, new_name, timestamp)
                    break
            self.fileList.item(self.fileList.row(item)).setText(new_name)
            QMessageBox.information(self, "Renamed", f"Changed to '{new_name}'!")

    def addMarker(self):
        dialog = QInputDialog(self)
        dialog.setLabelText("Location name:")
        dialog.setTextValue("New Place")
        if dialog.exec_():
            name = dialog.textValue()
            if not name:
                QMessageBox.warning(self, "Oops", "Please enter a name!")
                return
            dialog = QInputDialog(self)
            dialog.setLabelText("Latitude (e.g., 40.7128, -90 to 90):")
            dialog.setTextValue("40.7128")
            if dialog.exec_():
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
                if dialog.exec_():
                    try:
                        lon = float(dialog.textValue())
                        if not -180 <= lon <= 180:
                            raise ValueError("Longitude must be between -180 and 180.")
                        loc = [lat, lon]
                        if not self.is_duplicate(loc, name):
                            self.markers.append((loc, name, None))  # No timestamp for manual entry
                            self.fileList.addItem(name)
                            self.updateStatus()
                            QMessageBox.information(self, "Added", f"Added '{name}' at {lat}, {lon}!")
                        else:
                            QMessageBox.warning(self, "Duplicate", f"'{name}' with those coordinates already exists!")
                    except ValueError as e:
                        QMessageBox.warning(self, "Invalid Input", f"Bad longitude: {str(e)}")

    def removeMarker(self):
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
        for i, (_, marker_name, _) in enumerate(self.markers):
            if marker_name == name:
                del self.markers[i]
                break

    def clearAll(self):
        if not self.markers:
            QMessageBox.information(self, "Nothing to Clear", "No locations loaded!")
            return
        reply = QMessageBox.question(self, "Confirm Clear", "Remove all locations?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.markers = []
            self.fileList.clear()
            self.updateStatus()
            QMessageBox.information(self, "Cleared", "All locations removed!")

    def is_duplicate(self, loc, name):
        for existing_loc, existing_name, _ in self.markers:
            if (abs(existing_loc[0] - loc[0]) < 0.0001 and 
                abs(existing_loc[1] - loc[1]) < 0.0001 and 
                existing_name == name):
                return True
        return False

    def updateStatus(self):
        self.statusLabel.setText(f"Loaded Locations: {len(self.markers)}")

    def showHelp(self):
        help_text = (
            "Welcome to Easy GPS Map Viewer!\n\n"
            "1. **Load Locations**: Enter image URLs/paths, click 'Load Location' to add them.\n"
            "2. **View Map**: Click 'View Map' to see all locations with time/date if available.\n"
            "3. **Add Custom**: Add a manual location with coordinates (no timestamp).\n"
            "4. **Edit**: Double-click a location to rename it.\n"
            "5. **Save/Load**: Save to a file or load more locations.\n"
            "6. **Remove/Clear**: Remove one or all locations.\n\n"
            "Tip: Images must have GPS EXIF data. Timestamps appear on map pins if present."
        )
        QMessageBox.information(self, "How to Use", help_text)

    def load_last_file(self):
        if os.path.exists('last_file.txt'):
            try:
                with open('last_file.txt', 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logging.error(f"Error loading last file: {str(e)}")
        return None

    def save_last_file(self, path):
        try:
            with open('last_file.txt', 'w') as f:
                f.write(path)
        except Exception as e:
            logging.error(f"Error saving last file: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MapUI()
    ex.show()
    sys.exit(app.exec_())
