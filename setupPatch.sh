echo DID YOU UPDATE THE CHANGELOG?
sudo python setup.py sdist --format=zip#create the zip version
sudo python setup.py egg_info #to upload info to pypi
sudo python setup.py bdist_egg #an egg file for distribution