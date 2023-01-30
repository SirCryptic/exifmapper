# exifmapper


```
usage: exifmapper.py [-h] (-f FILES [FILES ...] | -u URLS [URLS ...]) [-m MAP] [-t TILES]

Extracts EXIF data and generates a map.

options:
  -h, --help            show this help message and exit
  -f FILES [FILES ...], --files FILES [FILES ...]
                        Path to image files
  -u URLS [URLS ...], --urls URLS [URLS ...]
                        URLs of images
  -m MAP, --map MAP     Path to save map
  -t TILES, --tiles TILES
                        Map tiles (default: OpenStreetMap)
```

**USAGE EXAMPLES:**

Extract EXIF data from local image files and generate a map:
```
python exifmapper.py -f image1.jpg image2.jpg -m map.html
```
Extract EXIF data from image URLs and generate a map:

```
python exifmapper.py -u https://example.com/image1.jpg https://example.com/image2.jpg -m map.html
```

Extract EXIF data from local image files, generate a map with custom map tiles (terrain):
```
python exifmapper.py -f image1.jpg image2.jpg -m map.html -t StamenTerrain
```
