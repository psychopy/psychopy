gource --load-config gource.cfg -o gource.ppm
ffmpeg -y -r 25 -f image2pipe -vcodec ppm -i gource.ppm -i ../airtone_-_slowLane.mp3 -t 00:03:05 -b:v 800K gource_psychopy.mkv
rm -R gource.ppm  # the ppm (uncompressed frames) is over 13Gb


# attached audio file (CC-BY-NC) is:
# slowLane by airtone (c) copyright 2017 Licensed under a Creative Commons Attribution Noncommercial  (3.0) license. http://dig.ccmixter.org/files/airtone/56231
