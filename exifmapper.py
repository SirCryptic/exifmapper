import exifread
import geopy
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="exifmapper")

# Get the directory containing the image files
directory = input("Enter the directory containing the image files: ")

# Get all image files in the specified directory
for file in os.listdir(directory):
    if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".JPG") or file.endswith(".JPEG"):
        # Open the image file
        with open(file, "rb") as image_file:
            # Read the exif data
            exif_data = exifread.process_file(image_file)
            # Get the GPS information
            gps_latitude = exif_data["GPS GPSLatitude"]
            gps_latitude_ref = exif_data["GPS GPSLatitudeRef"]
            gps_longitude = exif_data["GPS GPSLongitude"]
            gps_longitude_ref = exif_data["GPS GPSLongitudeRef"]
            # Convert the GPS data to decimal degrees
            latitude = convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                latitude = 0 - latitude
            longitude = convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                longitude = 0 - longitude
            # Get the address of the location
            location = geolocator.reverse(f"{latitude}, {longitude}")
            print(f"{file}: {location.address}")

# Function to convert the GPS data to decimal degrees
def convert_to_degrees(value):
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)
    return d + (m / 60.0) + (s / 3600.0
