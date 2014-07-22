
"""demo to illustrate encryption and decryption of a data file using pyFileSec
"""
from pyfilesec import SecFile, GenRSA
import os

# Logging is available, optional:
#from psychopy import logging
#logging.console.setLevel(logging.INFO)
#pfs.logging = logging

# We need a data file to encrypt, e.g., containing "sensitive" info:
datafile = 'data.txt'  # filename
with open(datafile, 'wb') as file:
    file.write("confidential data, e.g., participant's drug-use history")  # data in the file

# To set up for encryption, give it to a SecFile:
sf = SecFile(datafile)
print 'make a file:\n  file name: "%s"\n  contents: "%s"' % (sf.file, sf.snippet)
print '  is encrypted: %s' % sf.is_encrypted

# These particular RSA keys are ONLY for testing; see pyfilesec.genrsa() to make your own keys)
pubkey, privkey, passphrase = GenRSA().demo_rsa_keys()  # paths to new tmp files that hold the keys

# To encrypt the file, use the RSA public key:
sf.encrypt(pubkey)
print 'ENCRYPT it:\n  file name: "%s"\n  contents (base64): "%s . . ."' % (sf.file, sf.snippet)
print '  is encrypted: %s' % sf.is_encrypted

# To decrypt the file, use the matching RSA private key (and its passphrase):
sf.decrypt(privkey, passphrase)
print 'DECRYPT it:\n  file name: "%s"\n  contents: "%s"' % (sf.file, sf.snippet)
print '  is encrypted: %s' % sf.is_encrypted

# clean-up the tmp files:
for file in [sf.file, pubkey, privkey, passphrase]:
    os.unlink(file)
