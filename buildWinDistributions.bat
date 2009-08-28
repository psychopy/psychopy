rem build simple distributions
rem python setup.py bdist_egg
python setup.py sdist --formats=zip
python setup.py bdist_wininst --install-script=psychopy_post_inst.py

rem install the current version to site-packages
python setup.py install

xcopy /I /Y *.txt C:\Python25
rem build the installer
makensis.exe /v2 buildCompleteInstaller.nsi
move /Y "StandalonePsychoPy*.exe" dist\