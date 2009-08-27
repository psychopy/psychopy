rem build simple distributions
python setup.py bdist_egg
python setup.py sdist --formats=zip
python setup.py bdist_wininst --install-script=psychopy_post_inst.py

rem install the current version to site-packages
cd C:\USERS\jwp\Code\PsychoPy\svn\trunk\
python setup.py install

rem build the app (in PsychoPyIDE\dist) and the installer (in \trunk\dist)
rem cd C:\USERS\jwp\Code\PsychoPy\svn\trunk\PsychoPyIDE

rem python setupApp.py py2exe
rem cd C:\USERS\jwp\Code\PsychoPy\svn\trunk
rem xcopy /I /Y psychopy\demos PsychoPyIDE\dist\demos
xcopy /I /Y windlls\*.dll dist

xcopy /I /Y *.txt C:\Python25
rem build the installer
makensis.exe buildCompleteInstaller.nsi
xcopy /I /Y "StandalonePsychoPy-x.xx.xx-win32.exe" dist\