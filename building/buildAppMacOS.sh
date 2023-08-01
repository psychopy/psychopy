#!/bin/sh
CODESIGN_ID=$1
CODESIGN_PASSWORD=$2

if [ -z "$CODESIGN_ID" ]
then
    SIGN=1 # can't sign without a codesign ID
else
    SIGN=$3 # 1=Build-only, 2=Sign-and-Sign, 3=Sign-only
fi

# defVersion=$(python -c 'import psychopy; print(psychopy.__version__)')
version=$(<version)  # reads from the version file

declare -a pythons=("python3.10")
declare -a names=("PsychoPy_py310")
declare -a todo=(0) # or  (1 0) to do both

for i in todo; do
    # mount the disk image and delete previous copy of app
#    echo "Opening disk image for app"
#    hdiutil detach "/Volumes/PsychoPy" -quiet
#    hdiutil attach "../dist/StandalonePsychoPy3_tmpl.dmg"
#    osascript -e "set Volume 0.2"
#    say -v Karen "password"
#    sudo rm -R /Volumes/PsychoPy/PsychoPy3*   
    if (( $SIGN==1  || $SIGN==2 )); then
        echo "building"
        # remove old pyc files
        find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

        echo $i "BUILDING: ${pythons[$i]} __ ${names[$i]} in $(pwd)"
        dmgName="../dist/Standalone${names[$i]}-$version-MacOS.dmg"

        ${pythons[$i]} setupApp.py py2app || { echo 'setupApp.py failed' ; exit 1; }
        # copy over git-core folder
        cp -R -L /usr/local/git/libexec/git-core dist/${names[$i]}.app/Contents/Resources/git-core

        # remove matplotlib tests (45mb)
        rm -r dist/${names[$i]}.app/Contents/Resources/lib/python3.10/matplotlib/tests
        # strip all other architectures from binaries and move both to __fat copy
        mv dist/${names[$i]}.app dist/${names[$i]}__fat.app
        echo "stripping i386 using ditto"
        ditto --arch x86_64 dist/${names[$i]}__fat.app dist/${names[$i]}.app
    fi
    if (( $SIGN==2  || $SIGN==3 )); then
        echo "signing"
        # built and stripped. Now mac codesign. Running in 2 steps to allow the detach step to work
        ${pythons[$i]} building/apple_sign.py --app "${names[$i]}.app" --runPostDmgBuild 0 --id $CODESIGN_ID --pwd $CODESIGN_PASSWORD
        ${pythons[$i]} building/apple_sign.py --app "${names[$i]}.app" --runPreDmgBuild 0  --id $CODESIGN_ID --pwd $CODESIGN_PASSWORD
    fi
done
