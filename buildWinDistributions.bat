rem build simple distributions
rem python setup.py bdist_egg
rem python setup.py sdist --formats=zip
rem python setup.py bdist_wininst --install-script=psychopy_post_inst.py

rem install the current version to site-packages
python setup.py install

del C:\Python27\Lib\site-packages\psychopy.pth
xcopy /I /Y psychopy\*.txt C:\Python27
rem build the installer
makensis.exe /v3 buildCompleteInstaller.nsi

rem moving files to ..\dist
move /Y "StandalonePsychoPy*.exe" ..\dist\
move /Y dist\* ..\dist\

rem reinsert my dev .pth file
ECHO F|xcopy /I /Y ..\psychopy.pth C:\Python27\Lib\site-packages\psychopy.pth