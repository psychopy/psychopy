rem python24
rem c:/python24/python setup.py bdist_wininst --install-script=psychopy_post_inst.py

rem python25
rem python setupEgg.py bdist_egg
python setupEgg.py sdist --formats=zip
python setup.py bdist_wininst --install-script=psychopy_post_inst.py
rem dist\PsychoPy-0.93.0.win32-py2.5.exe
