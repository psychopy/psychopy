rem build simple distributions
python setup.py bdist_egg
python setup.py sdist --formats=zip
python setup.py bdist_wininst --install-script=psychopy_post_inst.py

rem install the current version to site-packages
python setup.py install

xcopy /I /Y PsychoPy.egg-info\PKG-INFO dist\
xcopy /I /Y psychopy\*.txt C:\Python25
rem build the installer
makensis.exe /v3 buildCompleteInstaller.nsi
move /Y "StandalonePsychoPy*.exe" dist\
