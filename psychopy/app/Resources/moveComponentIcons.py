import os
from os.path import join, split, isdir
import shutil

cmpFolder = join("..", "..", "experiment", "components")
components = os.listdir(cmpFolder)

def shipOut(theme):
	"""Move component icons from Resources folders to component folders, allowing themes to be customisable
	without requiring component developers to have to deal with each app theme individually"""
	# Get origin location & files
	orig = join(os.getcwd(), theme, "components")
	if isdir(orig):
		files = os.listdir(orig)
	else:
		return
	# For each file
	for fname in files:
		# Check whether it corresponds to a component
		stripped = fname.replace("@2x.png", "").replace(".png", "")
		if stripped in components:
			# Move to corresponding component folder
			dest = join(cmpFolder, stripped, theme)
			shutil.move(
				join(orig, fname),
				join(dest, fname)
			)

def shipIn(theme):
	"""Return component icons from component folders to corresponding Resources folder"""
	for comp in components:
		# Set destination (Resources folder for this theme)
		dest = join(os.getcwd(), theme, "components")
		# Get origin location & files
		orig = join(cmpFolder, comp, theme)
		if isdir(orig) and isdir(dest):
			files = os.listdir(orig)
			for fname in files:
				# Move back to resources folder
				shutil.move(
					join(orig, fname),
					join(dest, fname)
				)

# Get all themes
themes = os.listdir(os.getcwd())
# For each theme, if it is valid, perform shipOut
for theme in themes:
	if isdir(theme):
		shipOut(theme)