
rm psychopy/demos/*.pyc
cd PsychoPyIDE
sudo rm -r build
sudo rm -r dist
python setupApp.py py2app
cd ..
sudo mv PsychoPyIDE/dist/PsychoPyIDE.app/ ../dist/PsychoPyIDE.app
