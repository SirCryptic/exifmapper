##created by sircryptic
##
## feel free to try fix my jank ass code
##
def get_gps_from_exif file
  `exiftool -c "%.6f" #{file} | grep GPS | grep Position`.scan(/(\d+\.\d+)/);
end

zoom = 2;
path = "*.jpg";
map_url = "https://staticmap.openstreetmap.de/staticmap.php?&zoom=#{zoom}&size=865x512&maptype=mapnik&markers=" ;
all = Dir.glob(path);
total = all.count
has_gps = 0;
meta_exif = 0;
all.each do |file|
  if gps = get_gps_from_exif(file)
    if gps.count==2 # lat and long
      coord = "#{gps[0][0]},#{gps[1][0]}"
      puts "=> #{file} @ #{coord}"
      map_url += "#{coord},lightblue3#{file}"
      meta_exif+=1
      has_gps+=1
    end
  end
end
puts "=> Total #{total} images | #{meta_exif} with EXIF | #{has_gps} with location";
puts ("=> Percentage with location = %3.2f" % [(has_gps*100).to_f/total]);
puts "=> Map URL: #{map_url}"
