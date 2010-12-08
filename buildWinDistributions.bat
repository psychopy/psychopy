rem build simple distributions
rem python setup.py bdist_egg
python setup.py sdist --formats=zip
python setup.py bdist_wininst --install-script=psychopy_post_inst.py

rem install the current version to site-packages
python setup.py install

del C:\Python26\Lib\site-packages\psychopy.pth
xcopy /I /Y psychopy\*.txt C:\Python26
rem build the installer
makensis.exe /v3 buildCompleteInstaller.nsi

rem moving files to ..\dist
move /Y "StandalonePsychoPy*.exe" ..\dist\
move /Y dist\* ..\dist\

rem reinsert my dev .pth file
xcopy /I /Y ..\psychopy.pth C:\Python26\Lib\site-packages\psychopy.pth