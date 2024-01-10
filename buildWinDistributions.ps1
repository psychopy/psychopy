#! powershell

param ($install_pp=1)
# build simple distributions
# python setup.py bdist_egg
# python setup.py sdist --formats=zip
# python setup.py bdist_wininst --install-script=psychopy_post_inst.py

# remove editable installation
# $pyPaths = @("C:\Python36", "C:\Python36_64")
# $names = @("PsychoPy3", "PsychoPy3")
# $archs = @("win32", "win64")
$pyPaths = @("C:\Python38")
$names = @("PsychoPy")
$archs = @("win64")

# read from the version file
$versionfile = Join-Path $pwd "version"
$v = [Io.File]::ReadAllText($versionfile).Trim()

for ($i=0; $i -lt $pyPaths.Length; $i++) {
    [console]::beep(440,300); [console]::beep(880,300)
    # try to uninstall psychopy from site-packages
    # re-install the current version as editable/developer
    if ($install_pp -eq 1) {
        Invoke-Expression ("& '{0}python.exe' -m pip install . --no-deps --force" -f $pyPaths[$i])
        echo ("Installed current PsychoPy")
        xcopy /I /Y psychopy\*.txt $pyPaths[$i]
    }

    # build the installer
    $thisPath = $pyPaths[$i]
    $thisName = $names[$i]
    $thisArch = $archs[$i]
    $cmdStr = "makensis.exe /v3 /DPRODUCT_VERSION={0} /DPRODUCT_NAME={1} /DARCH={2} /DPYPATH={3} buildCompleteInstaller.nsi" -f $v, $thisName, $thisArch, $thisPath
    echo $cmdStr
    Invoke-Expression $cmdStr
    # "C:\Program Files\Caphyon\Advanced Installer 13.1\bin\x86\AdvancedInstaller.com" /rebuild PsychoPy_AdvancedInstallerProj.aip

    if ($install_pp -eq 1) {
        # try to uninstall psychopy from site-packages
        Invoke-Expression ("& '{0}python.exe' -m pip uninstall -y psychopy" -f $pyPaths[$i])
        # re-install the current version as editable/developer
        Invoke-Expression ("& '{0}python.exe' -m pip install -e . --no-deps" -f $pyPaths[$i])
    }
}

echo 'moving files to ..\dist'
Move-Item -Force "StandalonePsychoPy*.exe" "..\dist"
Move-Item -Force dist\* "..\dist"

[console]::beep(880,300); [console]::beep(440,300)
