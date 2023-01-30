import argparse
import os
import io
import requests
import folium
import exifread

def parse_args():
  parser = argparse.ArgumentParser(description="Extracts EXIF data and generates a map.")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("-f", "--files", type=str, nargs='+', help="Path to image files")
  group.add_argument("-u", "--urls", type=str, nargs='+', help="URLs of images")
  parser.add_argument("-m", "--map", type=str, help="Path to save map")
  parser.add_argument("-t", "--tiles", type=str, help="Map tiles (default: OpenStreetMap)", default="OpenStreetMap")
  return parser.parse_args()

def get_loc(file_or_url, from_file=True):
  try:
    if from_file:
      ext = os.path.splitext(file_or_url)[1].lower()
      if ext not in [".jpg", ".jpeg"]:
        return None
      with open(file_or_url, "rb") as file:
        tags = exifread.process_file(file)
    else:
      response = requests.get(file_or_url)
      ext = os.path.splitext(urlparse(file_or_url).path)[1].lower()
      if ext not in [".jpg", ".jpeg"]:
        return None
      file = io.BytesIO(response.content)
      tags = exifread.process_file(file)
    if not tags:
      return None
    lat = tags.get("GPS GPSLatitude").values
    lat_ref = tags.get("GPS GPSLatitudeRef").values
    lon = tags.get("GPS GPSLongitude").values
    lon_ref = tags.get("GPS GPSLongitudeRef").values
    lat = exifread.utils.decimal_to_dms(lat, lat_ref)
    lon = exifread.utils.decimal_to_dms(lon, lon_ref)
    return [lat, lon]
  except:
    return None

def main():
  args = parse_args()
  markers = []
  for file_or_url in args.files or args.urls:
    loc = get_loc(file_or_url, from_file=args.files is not None)
    if loc:
      markers.append(loc)
  if not markers:
    print("No valid GPS data found.")
    return
  avg_lat = sum(x[0] for x in markers) / len(markers)
  avg_lon = sum(x[1] for x in markers) / len(markers)
  m = folium.Map(location=[avg_lat, avg_lon], zoom_start=16, tiles=args.tiles)
  if args.map:
    m.save(args.map)
  else:
    m.show()
  for marker in markers:
    folium.Marker(location=marker).add_to(m)
if __name__ == "__main__":
  main()
