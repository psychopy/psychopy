#! powershell

param ($install_pp=1)
# build simple distributions
# python setup.py bdist_egg
# python setup.py sdist --formats=zip
# python setup.py bdist_wininst --install-script=psychopy_post_inst.py

# remove editable installation
# $pyPaths = @("C:\Python36\", "C:\Python36_64\")
# $names = @("PsychoPy3", "PsychoPy3")
# $archs = @("win32", "win64")
$pyPaths = @("py\")
$names = @("PsychoPy")
$archs = @("win64")

# read from the version file
$versionfile = Join-Path $pwd "version"
$v = [Io.File]::ReadAllText($versionfile).Trim()

for ($i=0; $i -lt $pyPaths.Length; $i++) {

    # build the installer
    $thisPath = $pyPaths[$i]
    $thisName = $names[$i]
    $thisArch = $archs[$i]
    $cmdStr = "makensis.exe /v3 /DPRODUCT_VERSION={0} /DPRODUCT_NAME={1} /DARCH={2} /DPYPATH={3} buildCompleteInstaller.nsi" -f $v, $thisName, $thisArch, $thisPath
    echo $cmdStr
    Invoke-Expression $cmdStr
    # "C:\Program Files\Caphyon\Advanced Installer 13.1\bin\x86\AdvancedInstaller.com" /rebuild PsychoPy_AdvancedInstallerProj.aip

}
