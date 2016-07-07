#!/bin/sh

echo "DID YOU UPDATE THE CHANGELOG?"
printf "Version (e.g. 1.84.0) : " # no new line
read version

sudo rm -r build

python setup.py sdist --format=zip
python setup.py egg_info
python setup.py bdist_egg
# then handle the mac app bundle
rm psychopy/demos/*.pyc
rm psychopy/prefSite.cfg

sudo rm -r dist/PsychoPy2.app #the previous version
sudo rm -r ../dist/PsychoPy2.app #the previous version in 'main' location
python setupApp.py py2app
# sudo chmod -R g+w dist/PsychoPy2.app #Jon: not sure this is needed
# remove matplotlib tests (45mb)
rm -r dist/PsychoPy2.app/Contents/Resources/lib/python2.7/matplotlib/tests
# strip all other architectures from binaries and move both to ../dist
echo "stripping i386 using ditto"
ditto --rsrc --arch x86_64 dist/PsychoPy2.app ../dist/PsychoPy2.app
mv dist/PsychoPy2.app ../dist/PsychoPy2_fat.app

# mount the disk image to put the app in
echo "Opening disk image for app"
hdiutil detach "/Volumes/PsychoPy" -quiet
hdiutil attach "../dist/StandalonePsychoPy--64bit.dmg"
sudo rm -R "/Volumes/PsychoPy/PsychoPy2.app"
echo "cp -R ../dist/PsychoPy2.app /Volumes/PsychoPy"
cp -R "../dist/PsychoPy2.app" "/Volumes/PsychoPy"
hdiutil detach "/Volumes/PsychoPy"
echo "creating zlib-compressed dmg"
hdiutil convert "../dist/StandalonePsychoPy--64bit.dmg" -format UDZO -o  "../dist/StandalonePsychoPy-$version-OSX_64bit.dmg"
