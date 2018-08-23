gource --load-config gource.cfg -o gource.ppm
ffmpeg -y -b:v 800K -r 60 -f image2pipe -vcodec ppm -i gource.ppm -vcodec libx264 -vpre baseline -crf 28 -threads 0 psychopy_dev.mp4
ffmpeg -y -b:v 800K -r 25 -f image2pipe -vcodec ppm -i gource.ppm psychopy_dev.mkv
rm -R gource.ppm
