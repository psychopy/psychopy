
rem install the current version to site-packages
cd C:\USERS\jwp\Code\PsychoPy\svn\trunk\
python setup.py install

rem build the app
cd C:\USERS\jwp\Code\PsychoPy\svn\trunk\PsychoPyIDE
python setupApp.py py2exe
cd C:\USERS\jwp\Code\PsychoPy\svn\trunk
xcopy /I /Y psychopy\demos PsychoPyIDE\dist\demos

rem build the installer
rem "C:\Program Files\NSIS\makensis.exe" buildExeInstaller.nsi