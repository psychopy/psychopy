# Why are all these files blank?

Unless you're reading this file from within the built PsychoPy package, all of the translation files in this folder will be blank. The data you're looking for is in the [psychopy-translation](https://github.com/psychopy/psychopy-translation) repository; when PsychoPy is built, the files are pulled from that repo and inserted into this folder.

To manually insert these files, you can clone and install psychopy-translation as a Python package, then call:

```
python -m psychopy_translation.generate --folder path/to/this/folder --format mo
```

However, please do not commit those files to this repo.