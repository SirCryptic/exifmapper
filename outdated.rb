##created by sircryptic
##
## feel free to try fix my jank ass code
##
require 'exifr'

def get_gps_coordinates(file)
  exif = EXIFR::JPEG.new(file)
  if exif.gps
    [exif.gps.latitude, exif.gps.longitude]
  else
    nil
  end
end

zoom = 2
path = "*.jpg"
map_url = "https://staticmap.openstreetmap.de/staticmap.php?&zoom=#{zoom}&size=865x512&maptype=mapnik&markers="
all_files = Dir.glob(path)
total_files = all_files.count
has_gps = 0
meta_exif = 0

all_files.each do |file|
  gps = get_gps_coordinates(file)
  if gps
    coord = "#{gps[0]},#{gps[1]}"
    puts "=> #{file} @ #{coord}"
    map_url += "#{coord},lightblue3#{file}"
    meta_exif += 1
    has_gps += 1
  end
end

puts "=> Total #{total_files} images | #{meta_exif} with EXIF | #{has_gps} with location"
puts "=> Percentage with location = %3.2f" % [(has_gps*100.0/total_files)]
puts "=> Map URL: #{map_url}"
