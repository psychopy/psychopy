# To modify component icons:

Create the desired icons in your preferred image editor, export them as .png files to this folder in the following sizes, with the following suffixes:

| Size | Suffix | Example           |
| ---- | ------ | ----------------- |
| 48px | 48     | aperture48.png    |
| 96px | 48@2x  | aperture48@2x.png |

Make sure that the filenames (before applying the suffix) match the name of the components' folder in `Psychopy/Experiment`, if you are using Adobe Illustrator to create icons then this is best achieved by naming the artboard for each icon to match the component folder.

Once the desired icons are in this folder, run `moveComponentIcons.py` from the Resources folder. This will move icons to the corresponding component folder, where they can be used by Psychopy.