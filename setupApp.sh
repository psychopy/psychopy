#!/bin/sh

#shouldn't need sudo for any of this - if so remove the dist, build and PsychoPy.egg-info

echo DID YOU UPDATE THE CHANGELOG?
sudo rm -r build

python setup.py sdist --format=zip
python setup.py egg_info
python setup.py bdist_egg
#then handle the mac app bundle
rm psychopy/demos/*.pyc
rm psychopy/prefSite.cfg

rm -r dist/PsychoPy2.app
rm -r ../dist/PsychoPy2.app
python setupApp.py py2app #shouldn't need sudo for this
chmod -R g+w dist/PsychoPy2.app
#strip all other architectures from binaries and move both to ../dist
ditto --rsrc --arch i386 dist/PsychoPy2.app ../dist/PsychoPy2.app
mv dist/PsychoPy2.app ../dist/PsychoPy2_fat.app

mv dist/* ../dist/