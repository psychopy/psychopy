from pathlib import Path
import subprocess
import re
import time, sys
import argparse
import shutil

thisFolder = Path(__file__).parent

with Path().home()/ 'keys/apple_ost_id' as p:
    IDENTITY = p.read_text().strip()
with Path().home()/ 'keys/apple_psychopy3_app_specific' as p:
    PWORD = p.read_text().strip()

ENTITLEMENTS = thisFolder / "entitlements.plist"
BUNDLE_ID = "org.opensciencetools.PsychoPy3"
USERNAME = "admin@opensciencetools.org"

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
        self._dmgFile = None

    def signAll(self):
        # remove files that we know will fail the signing:
        for filename in signer.appFile.glob("**/Frameworks/SDL*"):
            shutil.rmtree(filename)
        for filename in signer.appFile.glob("**/Frameworks/eyelink*"):
            shutil.rmtree(filename)

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
        # ready? Let's do this!
        t0 = time.time()
        for filename in files:
            print('.', end='')
            sys.stdout.flush()
            self.signSingleFile(filename, verbose=False, removeFailed=False)
        print(f'...done signing dylibs in {time.time()-t0:.03f}s')
        # then sign the outer app file
        print('Signing app')
        sys.stdout.flush()
        # t0 = time.time()
        # self.signSingleFile(self.appFile, removeFailed=False)
        # print(f'...done signing app in {time.time()-t0:.03f}s')
        # sys.stdout.flush()

    def signSingleFile(self, filename, removeFailed=False, verbose=True,
                       appFile=False):
        cmd = ['codesign',
               '--sign',  IDENTITY,
               '--entitlements', str(ENTITLEMENTS),
               '--force',
               '--timestamp',
               #'--deep',  # probably not needed for libs but maybe if Framework?
               '--options', 'runtime',
               str(filename),
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
        return self.signCheck(filename, verbose=False)

    def signCheck(self, filepath=None, verbose=False, strict=True):
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
            print(f"exitcode={exitcode}: {output}")

        # check for warnings
        warnings=[]
        for line in output.split("\n"):
            if 'warning' in line.lower():
                warnings.append(line)
        if warnings:
            print(filepath)
            for line in warnings:
                print("  ", line)
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
        if not 'No errors uploading' in output:
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
        if self._dmgFile:
            return self._dmgFile
        print("Opening disk image for app")
        dmgTemplate = thisFolder/"../../dist/StandalonePsychoPy3_tmpl.dmg"
        exitcode, output = subprocess.getstatusoutput(
                "hdiutil detach '/Volumes/PsychoPy' -quiet")
        exitcode, output = subprocess.getstatusoutput(
                f"hdiutil attach '{dmgTemplate.resolve()}'")
#    echo "Opening disk image for app"
#    hdiutil detach "/Volumes/PsychoPy" -quiet
#    hdiutil attach "../dist/StandalonePsychoPy3_tmpl.dmg"
#    osascript -e "set Volume 0.2"
#    say -v Karen "password"
#    sudo rm -R /Volumes/PsychoPy/PsychoPy3*

        return self._dmgFile

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
            if exitcode==0:
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

    def checkAppleLogFile(self):
        cmdStr = f"xcrun altool --notarization-info {self._appNotarizeUUID} -u {USERNAME} -p {PWORD}"

        exitcode, output = subprocess.getstatusoutput(cmdStr)
        print(f"exitcode={exitcode}: {output}")


if __name__ == "__main__":
    with open(thisFolder.parent / "version") as f:
        defaultVersion = f.read().strip()
    parser = argparse.ArgumentParser(description="Codesigning PsychoPy.app")
    parser.add_argument("--app", help=("Path to the app bundle, "
                                       "assumed to be in dist/"),
                        action='store', required=False, default="PsychoPy3.app")
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
        signer.signAll()
        # signer.signSingleFile(signer.appFile, removeFailed=False, verbose=True)
        signer.signCheck(verbose=False)

        # signer.upload(signer.zipFile)
        # signer.awaitNotarized()
        # signer.staple(signer.appFile)

        # make dmg and repeat
        # signer.upload(signer.dmgFile)
        # signer.awaitNotarized()
        # signer.staple(signer.dmgFile)
