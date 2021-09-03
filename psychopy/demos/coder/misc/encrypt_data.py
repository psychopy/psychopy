#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo to illustrate encryption and decryption of a data file using pyFileSec
"""

from pyfilesec import SecFile, GenRSA
import os

# Logging is available, optional:
# from psychopy import logging
# logging.console.setLevel(logging.INFO)
# pfs.logging = logging

# We need a data file to encrypt, e.g., containing "sensitive" info:
datafile = 'data.txt'
with open(datafile, 'wb') as file:
    file.write("confidential data, e.g., participant's drug-use history")

# To set up for encryption, give it to a SecFile:
sf = SecFile(datafile)
msg = 'make a file:\n  file name: "%s"\n  contents: "%s"'
print(msg % (sf.file, sf.snippet))
print('  is encrypted: %s' % sf.is_encrypted)

# These particular RSA keys are ONLY for testing
# see pyfilesec.genrsa() to make your own keys)
# paths to new tmp files that hold the keys
pubkey, privkey, passphrase = GenRSA().demo_rsa_keys()

# To encrypt the file, use the RSA public key:
sf.encrypt(pubkey)
msg = 'ENCRYPT it:\n  file name: "%s"\n  contents (base64): "%s . . ."'
print(msg % (sf.file, sf.snippet))
print('  is encrypted: %s' % sf.is_encrypted)

# To decrypt the file, use the matching RSA private key (and its passphrase):
sf.decrypt(privkey, passphrase)
msg = 'DECRYPT it:\n  file name: "%s"\n  contents: "%s"'
print(msg % (sf.file, sf.snippet))
print('  is encrypted: %s' % sf.is_encrypted)

# clean-up the tmp files:
for file in [sf.file, pubkey, privkey, passphrase]:
    os.unlink(file)

# The contents of this file are in the public domain.
