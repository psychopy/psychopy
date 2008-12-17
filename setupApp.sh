echo 'DID YOU UPDATE THE CHANGELOG?'
python setup.py sdist #create the tar.gz version
python setup.py egg_info #to upload info to pypi
python setup.py bdist_egg #an egg file for distribution
#then handle the mac app bundle
rm psychopy/demos/*.pyc
cd PsychoPyIDE
sudo rm -r build
sudo rm -r dist
python setupApp.py py2app
cd ..
sudo mv PsychoPyIDE/dist/PsychoPyIDE.app/ dist/PsychoPyIDE.app
