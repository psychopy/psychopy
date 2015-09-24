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

sudo rm -r dist/PsychoPy2.app #the previous version
sudo rm -r ../dist/PsychoPy2.app #the previous version in 'main' location
python setupApp.py py2app
sudo chmod -R g+w dist/PsychoPy2.app
#remove matplotlib tests (45mb)
rm -r dist/PsychoPy2.app/Contents/Resources/lib/python2.7/matplotlib/tests
#strip all other architectures from binaries and move both to ../dist
ditto --rsrc --arch x86_64 dist/PsychoPy2.app ../dist/PsychoPy2.app
mv dist/PsychoPy2.app ../dist/PsychoPy2_fat.app

mv dist/* ../dist/
