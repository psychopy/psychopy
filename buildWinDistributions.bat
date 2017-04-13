rem build simple distributions
rem python setup.py bdist_egg
rem python setup.py sdist --formats=zip
rem python setup.py bdist_wininst --install-script=psychopy_post_inst.py

rem remove editable installation
pip uninstall psychopy -y
rem install the current version to site-packages
pip install .

xcopy /I /Y psychopy\*.txt C:\Python27
copy /Y C:\Windows\System32\avbin.dll avbin.dll
xcopy /Y C:\Windows\System32\py*27.dll C:\Python27
rem build the installer
makensis.exe /v3 buildCompleteInstaller.nsi
rem "C:\Program Files\Caphyon\Advanced Installer 13.1\bin\x86\AdvancedInstaller.com" /rebuild PsychoPy_AdvancedInstallerProj.aip

rem moving files to ..\dist
move /Y "StandalonePsychoPy*.exe" ..\dist\
move /Y dist\* ..\dist\

rem uninstall psychopy from site-packages
pip uninstall psychopy -y
rem re-install the current version as editable/developer
pip install -e .
