On OS X, download the latest source release from:

    http://www.music.mcgill.ca/~gary/rtaudio/release

and build with the following::
    
    ./configure CC="gcc -arch i386" CXX="g++ -arch i386"
    make CFLAGS=-m32
    sudo cp librtaudio.a /usr/local/lib
    sudo cp RtAudio.h  RtError.h /usr/local/include