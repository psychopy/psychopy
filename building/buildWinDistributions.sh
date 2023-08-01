#! bash

install_pp=$1
# build simple distributions
# python setup.py bdist_egg
# python setup.py sdist --formats=zip
# python setup.py bdist_wininst --install-script=psychopy_post_inst.py

# remove editable installation
# $pyPaths = @("C:\Python36\", "C:\Python36_64\")
# $names = @("PsychoPy3", "PsychoPy3")
# $archs = @("win32", "win64")
thisPath="py\\"
thisName="PsychoPy"
thisArch="win64"

# read from the version file
v=$(cat version | tr -d '\n')

# try to uninstall psychopy from site-packages
# re-install the current version as editable/developer
${thisPath}python.exe -m pip install . --no-deps --force
cp psychopy\*.txt $thisPath

# build the installer
cmdStr="makensis.exe /v3 /DPRODUCT_VERSION=${v} /DPRODUCT_NAME=${thisName} /DARCH=${thisArch} /DPYPATH=${thisPath} buildCompleteInstaller.nsi"
echo $cmdStr
cmd.exe $cmdStr
# "C:\Program Files\Caphyon\Advanced Installer 13.1\bin\x86\AdvancedInstaller.com" /rebuild PsychoPy_AdvancedInstallerProj.aip
