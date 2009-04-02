rem build simple distributions
python setup.py bdist_egg
python setup.py sdist --formats=zip
python setup.py bdist_wininst --install-script=psychopy_post_inst.py

rem install the current version to site-packages
cd C:\USERS\jwp\Code\PsychoPy\svn\trunk\
python setup.py install

rem build the app (in PsychoPyIDE\dist) and the installer (in \trunk\dist)
cd C:\USERS\jwp\Code\PsychoPy\svn\trunk\PsychoPyIDE
python setupApp.py py2exe
cd C:\USERS\jwp\Code\PsychoPy\svn\trunk
xcopy /I /Y psychopy\demos PsychoPyIDE\dist\demos
xcopy /I /Y windlls\*.dll PsychoPyIDE\dist
rem build the installer
makensis.exe buildExeInstaller.nsi
xcopy /I /Y "StandalonePsychoPy-x.xx.x-win32.exe" dist\