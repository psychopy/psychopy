from pathlib import Path
import subprocess
import re
import time, sys, os
import argparse
import shutil
import dmgbuild

thisFolder = Path(__file__).parent
finalDistFolder = thisFolder.parent.parent/'dist'

with Path().home()/ 'keys/apple_ost_id' as p:
    IDENTITY = p.read_text().strip()
with Path().home()/ 'keys/apple_psychopy3_app_specific' as p:
    PWORD = p.read_text().strip()

ENTITLEMENTS = thisFolder / "entitlements.plist"
BUNDLE_ID = "org.opensciencetools.psychopy"
USERNAME = "admin@opensciencetools.org"

SIGN_ALL = True
NOTARIZE = True

# handy resources for info:
#
# why use zip file to notarize as well as dmg:
#   https://deciphertools.com/blog/notarizing-dmg/
# notarize from Python:
#   https://github.com/najiji/notarizer/blob/master/notarize.py
# apple entitlements:
#     https://developer.apple.com/documentation/xcode/notarizing_macos_software_before_distribution/resolving_common_notarization_issues


class AppSigner:
    def __init__(self, appFile, version, destination=None):
        self.appFile = Path(appFile)
        self.version = version
        self.destination = destination
        self._zipFile = None #'/Users/lpzjwp/code/psychopy/git/dist/PsychoPy3_2020.2.3.zip'
        self._appNotarizeUUID = None #'4f48ef26-8cf2-499b-a3ad-4b788c19e11e'
        self._dmgBuildFile = None

    def signAll(self):
        # remove files that we know will fail the signing:
        for filename in self.appFile.glob("**/Frameworks/SDL*"):
            shutil.rmtree(filename)
        for filename in self.appFile.glob("**/Frameworks/eyelink*"):
            shutil.rmtree(filename)

        # this never really worked - probably the files signed in wrong order?
        # find all the included dylibs
        print('Signing dylibs:', end='')
        files = list(self.appFile.glob('**/*.dylib'))
        files.extend(self.appFile.glob('**/*.so'))
        files.extend(self.appFile.glob('**/git-core/git*'))
        files.extend(self.appFile.glob('**/cv2/.dylibs/*'))
        # ffmpeg
        files.extend(self.appFile.glob('**/imageio_ffmpeg/binaries/*'))
        files.extend(self.appFile.glob('**/resources/ffmpeg/ffmpeg-osx*'))
        # PyQt
        files.extend(self.appFile.glob('**/Versions/5/Qt*'))
        files.extend(self.appFile.glob('**/Contents/MacOS/QtWebEngineProcess'))
        files.extend(self.appFile.glob('**/Resources/lib/python3.6/lib-dynload/*.so'))
        files.extend(self.appFile.glob('**/Frameworks/Python.framework/Versions/3.6/Python'))
        files.extend(self.appFile.glob('**/Frameworks/Python.framework'))
        files.extend(self.appFile.glob('**/Contents/MacOS/python'))

        # ready? Let's do this!
        t0 = time.time()
        for filename in files:
            print('.', end='')
            sys.stdout.flush()
            if filename.exists():  # might have been removed since glob
                self.signSingleFile(filename, verbose=False, removeFailed=True)
        print(f'...done signing dylibs in {time.time()-t0:.03f}s')

        # then sign the outer app file
        print('Signing app')
        sys.stdout.flush()
        t0 = time.time()
        self.signSingleFile(self.appFile, removeFailed=False)
        print(f'...done signing app in {time.time()-t0:.03f}s')
        sys.stdout.flush()

    def signSingleFile(self, filename, removeFailed=False, verbose=True,
                       appFile=False):
        cmd = ['codesign', str(filename),
               '--sign',  IDENTITY,
               '--entitlements', str(ENTITLEMENTS),
               '--force',
               '--timestamp',
               # '--deep',  # not recommended although used in most demos
               '--options', 'runtime',
               ]
        cmdStr = ' '.join(cmd)
        if verbose:
            print(cmdStr)
        exitcode, output = subprocess.getstatusoutput(cmdStr)
        # if failed or verbose then give info
        if exitcode != 0 or ('failed' in output) or (verbose and output):
            print(output)
        # if failed and removing then remove
        if (exitcode != 0 or 'failed' in output) and removeFailed:
            Path(filename).unlink()
            print(f"REMOVED FILE {filename}: failed to codesign")
        return self.signCheck(filename, verbose=False, removeFailed=removeFailed)

    def signCheck(self, filepath=None, verbose=False, strict=True,
                  removeFailed=False):
        """Checks whether a file is signed and returns a list of warnings"""
        if not filepath:
            filepath = self.appFile
        # just check the details
        strictFlag = "--strict" if strict else ""
        cmdStr = f'codesign -dvvv {strictFlag} {filepath}'
        # make the call
        if verbose:
            print(cmdStr)
        exitcode, output = subprocess.getstatusoutput(cmdStr)
        if verbose:
            print(f"Checking that codesign worked: {output}")

        # check for warnings
        warnings=[]
        for line in output.split("\n"):
            if 'warning' in line.lower():
                warnings.append(line)
        if warnings:
            print(filepath)
            for line in warnings:
                print("  ", line)
            if removeFailed:
                Path(filepath).unlink()
                print(f"REMOVED FILE {filepath}: failed to codesign")
        return warnings

    def upload(self, fileToNotarize):
        filename = Path(fileToNotarize).name
        print(f'Sending {filename} to apple for notarizing')
        cmdStr = (f"xcrun altool --notarize-app -t osx -f {fileToNotarize} "
                  f"--primary-bundle-id {BUNDLE_ID} -u {USERNAME} ")
        print(cmdStr)
        cmdStr += f"-p {PWORD}"
        t0 = time.time()
        exitcode, output = subprocess.getstatusoutput(cmdStr)
        if (exitcode == 0) and not ('No errors uploading' in output):
            print(f'[Error] Upload failed: {output}')
            exit(1)
        m = re.match('.*RequestUUID = (.*)\n', output, re.S)
        uuid = m.group(1).strip()
        self._appNotarizeUUID = uuid
        print(f'Uploaded file {filename} in {time.time()-t0:.03f}s: {uuid}')
        print(f'Upload to Apple completed at {time.ctime()}')
        return uuid

    @property
    def dmgFile(self):
        if not self._dmgBuildFile:
            self._dmgBuildFile = self._buildDMG()
        return self._dmgBuildFile

    @property
    def zipFile(self):
        if self._zipFile:
            return self._zipFile
        else:
            print("Creating zip archive to send to Apple: ", end='')
            zipFilename = self.appFile.parent / (self.appFile.stem+f'_{self.version}.zip')
            shutil.rmtree(zipFilename, ignore_errors=True)
            # zipFilename.unlink(missing_ok=True)  # remove the file if it exists
            t0 = time.time()
            cmdStr = f'/usr/bin/ditto -c -k --keepParent {self.appFile} {zipFilename}'
            print(cmdStr)
            exitcode, output = subprocess.getstatusoutput(cmdStr)
            if exitcode == 0:
                print(f"Done creating zip in {time.time()-t0:.03f}s")
            else:
                print(output)
            self._zipFile = zipFilename
            return zipFilename

    def awaitNotarized(self):
        while self.checkStatus(self._appNotarizeUUID):  # returns True while in progress
            time.sleep(30)


    def checkStatus(self, uuid):
        cmd = ['xcrun', 'altool', '--notarization-info', self._appNotarizeUUID,
               '-u', USERNAME, '-p', PWORD]
        cmdStr = ' '.join(cmd)
        exitcode, output = subprocess.getstatusoutput(cmdStr)

        in_progress = 'Status: in progress' in output
        success = 'Status: success' in output

        if not in_progress:
            print(f'Notarization completed at {time.ctime()}')
            if not success:
                print('*********Notarization failed*************')
                print(output)
                exit(1)

        return in_progress

    def staple(self, filepath):
        cmdStr = f'xcrun stapler staple {filepath}'
        print(cmdStr)
        exitcode, output = subprocess.getstatusoutput(cmdStr)
        print(f"exitcode={exitcode}: {output}")
        if exitcode != 0:
            print('*********Staple failed*************')
            exit(1)

    def checkAppleLogFile(self):
        cmdStr = f"xcrun altool --notarization-info {self._appNotarizeUUID} -u {USERNAME} -p {PWORD}"

        exitcode, output = subprocess.getstatusoutput(cmdStr)
        print(f"exitcode={exitcode}: {output}")

    def dmgBuild(self):
        dmgFilename = str(self.appFile).replace(".app", "_rw.dmg")
        appName = self.appFile.name
        print(f"building dmg file: {dmgFilename}")
        # remove previous file if it's there
        if Path(dmgFilename).exists():
            os.remove(dmgFilename)
        # then build new one

        icon = (thisFolder.parent /
                'psychopy/app/Resources/psychopy.icns').resolve()
        background = (thisFolder / "dmg722x241.tiff").resolve()
        dmgbuild.build_dmg(
                filename=dmgFilename,
                volume_name=f'PsychoPy-{self.version}',  # avoid spaces
                settings={
                    'format': 'UDRW',
                    'files': [str(self.appFile)],
                    'symlinks': { 'Applications': '/Applications' },
                    'size': '3g',  # but maybe irrelevant in UDRW mode?
                    'badge_icon': str(icon),
                    'background': None,  # background
                    'icon_size': 128,
                    'icon_locations': {
                        'PsychoPy.app': (150, 160),
                        'Applications': (350, 160)
                    },
                    'window_rect': ((600, 600), (500, 400)),
                },
        )
        return dmgFilename

    def dmgStapleInside(self):
        dmgFilename = str(self.appFile).replace(".app", "_rw.dmg")
        appName = self.appFile.name
        """Staple the notarization to the app inside the r/w dmg file"""
        # staple the file inside the dmg
        cmdStr = f"hdiutil attach '{dmgFilename}'"
        exitcode, output = subprocess.getstatusoutput(cmdStr)
        volName = output.split('\t')[-1]
        self.staple(f"'{volName}/{appName}'")
        cmdStr = f"hdiutil detach '{volName}' -quiet"
        print(f'cmdStr was: {cmdStr}')
        for n in range(5):  # if we do this too fast then it fails. Try 5 times
            time.sleep(5)
            exitcode, output = subprocess.getstatusoutput(cmdStr)
            print(output)
            if exitcode == 0:
                break  # succeeded so stop
        if exitcode != 0:
            print(f'*********Failed to detach {volName} (wrong name?) *************')
            exit(1)

    def dmgCompress(self):
        dmgFilename = str(self.appFile).replace(".app", "_rw.dmg")
        dmgFinalFilename = finalDistFolder/(f"StandalonePsychoPy-{self.version}-macOS.dmg")
        # remove previous file if it's there
        if Path(dmgFinalFilename).exists():
            os.remove(dmgFinalFilename)

        cmdStr = f"hdiutil convert {dmgFilename} " \
                 f"-format UDZO " \
                 f"-o {dmgFinalFilename}"
        exitcode, output = subprocess.getstatusoutput(cmdStr)
        print(output)
        if exitcode != 0:
            print(f'****Failed to compress {dmgFilename} to {dmgFinalFilename} (is it not ejected?) ****')
            exit(1)
        return dmgFinalFilename


def main():

    with open(thisFolder.parent / "version") as f:
        defaultVersion = f.read().strip()
    parser = argparse.ArgumentParser(description="Codesigning PsychoPy.app")
    parser.add_argument("--app", help=("Path to the app bundle, "
                                       "assumed to be in dist/"),
                        action='store', required=False, default="PsychoPy.app")
    parser.add_argument("--version", help="Version of the app",
                        action='store', required=False, default=defaultVersion)
    parser.add_argument("--file", help="path for a single file to be signed",
                        action='store', required=False, default=None)
    args = parser.parse_args()
    if args.file:  # not the whole app - just sign one file
        distFolder = (thisFolder / '../dist').resolve()
        signer = AppSigner(appFile='',
                           version=None)
        signer.signSingleFile(args.file, removeFailed=False, verbose=True)
        signer.signCheck(args.file, verbose=True)
    else:  # full app signing and notarization
        distFolder = (thisFolder / '../dist').resolve()
        signer = AppSigner(appFile=distFolder/args.app,
                           version=args.version)
        if SIGN_ALL:
            signer.signAll()
        signer.signCheck(verbose=False)

        if NOTARIZE:
            signer.upload(signer.zipFile)
            # build the read/writable dmg file while waiting for notarize
            signer.dmgBuild()
            # notarize and staple
            signer.awaitNotarized()
            signer.dmgStapleInside()
        else:
            # just build the dmg
            signer.dmgBuild()

        dmgFile = signer.dmgCompress()
        signer.signSingleFile(dmgFile, removeFailed=False, verbose=True)

        if NOTARIZE:
            signer.upload(dmgFile)
            # notarize and staple
            signer.awaitNotarized()
            signer.staple(dmgFile)


if __name__ == "__main__":
    main()
