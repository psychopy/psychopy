# build simple distributions
# python setup.py bdist_egg
# python setup.py sdist --formats=zip
# python setup.py bdist_wininst --install-script=psychopy_post_inst.py

# remove editable installation
$pips = @("pip2", "pip3")
$pyN = @("27", "36")
$pyPaths = @("C:\Python27\", "C:\PROGRA~1\Python36\")
$names = @("PsychoPy2", "PsychoPy2_PY3")
# get PsychoPy version from file
$v = [Io.File]::ReadAllText("C:\Users\lpzjwp\code\psychopy\git\version").Trim()

for ($i=0; $i -lt 2; $i++) {
    # try to uninstall psychopy from site-packages
    Invoke-Expression ("{0} uninstall psychopy -y" -f $pips[$i])
    # re-install the current version as editable/developer
    Invoke-Expression ("{0} install . --no-deps" -f $pips[$i])
	echo Installed current PsychoPy
    xcopy /I /Y psychopy\*.txt $pyPaths[$i]
    xcopy /Y C:\Windows\System32\avbin.dll $pyPaths[$i]\avbin.dll
    if ($i -eq '0') {
        xcopy /Y C:\Windows\System32\py*27.dll C:\Python27
    }
    # build the installer
    $thisPath = $pyPaths[$i]
    $thisName = $names[$i]
    $cmdStr = "makensis.exe /v2 /DPRODUCT_VERSION={0} /DPRODUCT_NAME={1} /DPYPATH={2} buildCompleteInstaller.nsi" -f $v, $thisName, $thisPath
    echo $cmdStr
    Invoke-Expression $cmdStr
    # "C:\Program Files\Caphyon\Advanced Installer 13.1\bin\x86\AdvancedInstaller.com" /rebuild PsychoPy_AdvancedInstallerProj.aip

    echo 'moving files to ..\dist'

    # try to uninstall psychopy from site-packages
    Invoke-Expression ("{0} uninstall psychopy -y" -f $pips[$i])
    # re-install the current version as editable/developer
    Invoke-Expression ("{0} install -e . --no-deps" -f $pips[$i])
}

Move-Item -Force "StandalonePsychoPy*.exe" ..\dist\
Move-Item -Force dist\* ..\dist\