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

declare -a pythons=("python2" "python3")
declare -a names=("PsychoPy2" "PsychoPy2_PY3")

for i in 0 1; do
    echo $i "BUILDING:" ${pythons[$i]} "__" ${names[$i]}
    dmgName="../dist/Standalone${names[$i]}-$version-MacOS.dmg"

    sudo rm -r dist/${names[$i]}.app #the previous version
    sudo rm -r ../dist/${names[$i]}.app #the previous version in 'main' location
    ${pythons[$i]} setupApp.py py2app || { echo 'setupApp.py failed' ; exit 1; }

    # remove matplotlib tests (45mb)
    rm -r dist/${names[$i]}.app/Contents/Resources/lib/python2.7/matplotlib/tests
    # strip all other architectures from binaries and move both to ../dist
    echo "stripping i386 using ditto"
    ditto --rsrc --arch x86_64 dist/PsychoPy2.app ../dist/${names[$i]}.app
    mv dist/${names[$i]}.app ../dist/${names[$i]}__fat.app

    # mount the disk image to put the app in
    echo "Opening disk image for app"
    hdiutil detach "/Volumes/PsychoPy" -quiet
    hdiutil attach "../dist/StandalonePsychoPy--64bit.dmg"
    say -v Karen "password"
    sudo rm -R "/Volumes/PsychoPy/${names[$i]}.app"
    echo "cp -R ../dist/${names[$i]}.app /Volumes/PsychoPy"
    cp -R "../dist/${names[$i]}.app" "/Volumes/PsychoPy"
    hdiutil detach "/Volumes/PsychoPy"
    echo "removing prev dmg (although may not exist)"
    rm $dmgName
    echo "creating zlib-compressed dmg: $dmgName"
    hdiutil convert "../dist/StandalonePsychoPy--64bit.dmg" -format UDZO -o $dmgName

done

say -v Karen "all done"
