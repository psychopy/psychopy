from psychopy import prefs

import os
import sys
import subprocess

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


# https://stackoverflow.com/questions/28291909/gitpython-and-ssh-keys:
#     import os
#     from git import Repo
#     from git import Git
#
#     git_ssh_identity_file = os.path.expanduser('~/.ssh/id_rsa')
#     git_ssh_cmd = 'ssh -i %s' % git_ssh_identity_file
#
#     with Git().custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
#          Repo.clone_from('git@....', '/path', branch='my-branch')


def saveKeyPair(filepath, comment=''):
    """Generate and save a key pair (private and public) and return the public
    key as text

    filepath : unicode

        path to the (private) key. The public key will be filepath+'.pub'

    For PsychoPy on Pavlovia the filepath should be
        os.path.join(psychopy.prefs.paths['userprefs'], "ssh", username)

    """
    if type(comment) is not bytes:
        comment = comment.encode('utf-8')
    if type(filepath) is not bytes:
        filepath = filepath.encode('utf-8')

    try:  # try using ssh-keygen (more standard and probably faster)
        folder = os.path.split(filepath)[0]
        if not os.path.isdir(folder):
            os.mkdir(folder)
        output = subprocess.check_output([b'ssh-keygen',
                                          b'-C', comment,
                                          b'-f', filepath,
                                          b'-P', b''])
        # then read it back in to pass back
        public_key = getPublicKey(filepath + b".pub")
    except subprocess.CalledProcessError:
        # generate private/public key pair
        key = rsa.generate_private_key(backend=default_backend(),
                                       public_exponent=65537,
                                       key_size=4096)
        # get public key in OpenSSH format
        public_key = key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH)

        # get private key in PEM container format
        pem = key.private_bytes(encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption())

        # check that the root folder exists
        folder = os.path.dirname(filepath)
        if not os.path.exists(folder):
            os.makedirs(folder)
        # save private key
        with open(filepath, 'wb') as f:
            f.write(pem)
        os.chmod(filepath, 0o400)  # make sure the private key is only self-readable

        with open(filepath+'.pub', 'wb') as f:
            f.write(public_key)

    # whether we used ssh-keygen or home-grown we should try to ssh-add
    # because we're using a non-standard location
    if sys.platform == 'win32':
        pass  # not clear that this command exists on win32!
        # response = subprocess.check_output(['cmd', 'ssh-add', filepath])
    else:
        response = subprocess.check_output(['ssh-add', filepath])
    return public_key

def getPublicKey(filepath):
    """
    For PsychoPy on Pavlovia the filepath should be
        os.path.join(psychopy.prefs.paths['userprefs'], "ssh", username)
    """
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as f:
            pubKey = f.read()
    else:
        raise IOError("No ssh public key file found at {}".format(filepath))
    if type(pubKey) == bytes:  # in Py3 convert to UTF-8
        pubKey = pubKey.decode('utf-8')
    return pubKey


if __name__ == '__main__':
    from psychopy import prefs
    username = 'jon'
    fileRoot = os.path.join(prefs.paths['userPrefsDir'], "ssh", username)
    print(saveKeyPair(fileRoot))
    print(getPublicKey(fileRoot+'.pub'))
