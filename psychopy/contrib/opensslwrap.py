#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Basic file encryption for psych & human neuro research, using openssl."""

# Copyright (c) Jonathan Peirce, 2012
# released under the GPLv3 licence with an additional exemption
# (following the advice here: http://www.openssl.org/support/faq.html#LEGAL2):
# This program is released under the GPL with the additional exemption that
# compiling, linking, and/or using OpenSSL is allowed.

'''
    Think about / to-do / extensions:
    - sign this file and make signature available
    - does tgz actually compress at all, given that gz is after encryption?
    - good to support gpg or pgp
    - rewrite as a class
    - rewrite:
        def encrypt(file, pub, pad='-oaep', meta=True, keep=None, out='', fxn=None)
        def decrypt(file, priv, pad='-oaep', pphr='', out='', fxn=None)
        where fxn = dict, fxn['method'] = name of method to call with **fxn args
'''
__author__ = 'Jeremy R. Gray'

import os, sys, platform, shutil, tarfile
import random
import time, codecs # codecs just for date
from tempfile import mkdtemp, NamedTemporaryFile
import subprocess
from base64 import b64encode, b64decode
import hashlib


# set up to be independent of psychopy, eg, to decrypt() on server:
loggingID = os.path.splitext(os.path.basename(__file__))[0]
logging_t0 = time.time()

class _log2stderr(object): # need 'object' to support older python versions
    """Send logging to stderr"""
    def debug(self, msg):
        print >> sys.stderr, "%.4f  %s: %s" % (time.time() - logging_t0, loggingID, msg)
    error = warning = exp = data = info = debug
logging = _log2stderr()
if __name__ != '__main__': # use psychopy logging if available
    try:
        from psychopy import logging
    except:
        pass

# for command-line testing, currently verbose means: also show shellCall()s
verbose = False
if len(sys.argv) > 1 and sys.argv[1] in ['-v','--verbose']:
    del sys.argv[1]
    verbose = True
    
# want this early, to query for current openssl version:
def _shellCall(shellCmdList, stderr=False):
    """do a shell command via subprocess, return stdout (and stderr if requested).
    always log stderr; cmdList seems to handle all white-space in filename issues
    """
    if verbose:
        logging.debug('_shellCall: %s' % (' | '.join(shellCmdList)) )
    proc = subprocess.Popen(shellCmdList,  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    so, se = proc.communicate()
    del proc
    if se: logging.error(se.strip())
    if stderr:
        return so.strip(), se.strip()
    else:
        return so.strip()

# basic info about openssl on this system:
if sys.platform not in ['win32']:
    # its probably installed in the usual place:
    OPENSSL = _shellCall(['which', 'openssl'])
    if OPENSSL not in ['/usr/bin/openssl']: # mac, rhel/centos, ubuntu, neurodebian
        msg = 'unexpected location for openssl binary: %s' % OPENSSL
        logging.warning(msg)
else:
    # windows: win XP requires manual install, unclear where it will / should end up
    guess = _shellCall(['where', '/r', 'C:\\', 'openssl']) # vista and later, not tested
    if not (os.path.isfile(guess) and guess.endswith('openssl.exe') ):
        guess = 'C:/OpenSSL-Win32/bin/openssl.exe'
        if not os.path.isfile(guess):
            cwd = os.path.split(os.path.abspath(__file__))[0] 
            guess = os.path.join(cwd, os.path.abspath('openssl.exe'))
            if not os.path.isfile(guess):
                msg = 'failed to find openssl.exe locally.\n' +\
                      '? download from http://www.slproweb.com/products/Win32OpenSSL.html\n' +\
                      '? expecting C:\\OpenSSL-Win32\\bin\\openssl.exe, or %s\\openssl.exe' % cwd
                logging.error(msg)
                raise AttributeError(msg)
    OPENSSL = guess
opensslVersion = _shellCall([OPENSSL, 'version'])
if opensslVersion.split()[1] < '0.9.8':
    msg = 'openssl version too old (%s), need 0.9.8 or newer' % opensslVersion
    logging.error(msg)
    raise ValueError(msg)
logging.info('openssl binary  = %s' % OPENSSL)
logging.info('openssl version = %s' % opensslVersion)

# constants to use:
RSA_PADDING = '-oaep' # actual arg for openssl rsautl
BUNDLE_EXT = '.enc'   # for tgz of AES, PWD.RSA, META
AES_EXT = '.aes256'   # extension for AES encrypted data file
PWD_EXT = 'pwd'       # extension for file containing password
RSA_EXT = '.rsa'      # extension for RSA encrypted password file
META_EXT = '.meta'    # extension for meta-data


class PublicKeyTooShortError(StandardError):
    '''Error to indicate that a public key is not long enough'''
class DecryptError(StandardError):
    '''Error to signify that decryption failed.'''
class PrivateKeyError(StandardError):
    '''Error to signify that loading a private key failed.'''
class InternalFormatError(StandardError):
    '''Error to indicate bad file names inside .tgz file (start with . or /)'''

def _sha256b64(file, b64=True):
    """Return hash of a file, sha256 base64 (hex) encoded by default.
    could also use openssl for this, but that requires a shellCall, slower
    """
    dgst = hashlib.sha256()
    dgst.update(open(file, 'rb').read())
    if b64:
        hash = dgst.hexdigest()
    else:
        hash = dgst.digest()
    return hash

printableCharList = [c for c in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+_']
def _onetimePwd(n):
    """Generate a password of printable characters, length n.
    Using openssl for this is slower because it uses a file."""
    savedState = random.getstate()
    random.seed() # either a hash of current system time, or os.urandom() if available
    nch = n * printableCharList
    random.shuffle(nch)
    random.setstate(savedState)
    return ''.join(nch[:n])

def _wipeClose(file, passes=1):
    """Try to secure-delete (wipe) a file; unknown effectiveness; assert no file"""
    bytes = os.path.getsize(file.name)
    try:
        for i in xrange(passes):
            file.seek(0)
            file.write('\0' * bytes) # might help, might not; worth trying
        file.close()
    finally:
        try:
            os.remove(file.name)
        except:
            pass # NamedTemporaryFile is deleted on close()
        assert not os.path.isfile(file.name) # yikes, file remains after secure delete attempted

def _openTmp(file='tmp', mode='w+b'):
    """Return a named temporary file, ideally using tempfile"""
    if sys.platform == 'win32':
        tmp = open(_uniqFileName(file), mode)
    else:
        tmp = NamedTemporaryFile()

    return tmp

def _uniqFileName(filename):
    """Avoid file name collisions by appending '+' (before EXT)"""
    while os.path.isfile(filename) or os.path.isdir(filename):
        if filename.endswith(PWD_EXT + RSA_EXT):
            filename = filename.replace(PWD_EXT + RSA_EXT, '') + '+' + PWD_EXT + RSA_EXT
        elif filename.endswith(AES_EXT):
            filename = filename.replace(AES_EXT, '') + '+' + AES_EXT
        elif filename.endswith(META_EXT):
            filename = filename.replace(META_EXT, '') + '+' + META_EXT
        else:
            filename += '+'
    return filename

def _getMetaData(datafile, dataEncFile, pubkey, encMethod):
    """Return info about an encryption context, as a multiline string"""
    try:
        now = codecs.utf_8_decode(time.strftime("%Y_%b_%d_%H%M", time.localtime()))[0]
    except UnicodeDecodeError:
        # use an all-numeric date (to sidestep the unicode error)
        now = codecs.utf_8_decode(time.strftime("%Y_%m_%d_%H%M", time.localtime()))[0]
    md = []
    md.append('orig file path: ' + os.path.abspath(datafile) )
    md.append('HMAC-sha256 of encrypted file: %s' % _sha256b64(dataEncFile) )
    pubkey = open(pubkey).readlines()
    md.append('public key (first 20): ' + pubkey[1][0:20] )
    md.append('encryption: ' + loggingID + '.' + encMethod)
    md.append('RSA padding: ' + RSA_PADDING )
    md.append('encrypted on date: ' + now )
    md.append('openssl version: ' + opensslVersion )
    if sys.platform in ['darwin']:
        OSXver, _, architecture = platform.mac_ver()
        platInfo = 'darwin ' + OSXver + ' ' + architecture
    elif sys.platform.startswith('linux'):
        platInfo = 'linux '+platform.release()
    elif sys.platform in ['win32']:
        platInfo = 'windowsversion=' + repr(sys.getwindowsversion())
    else:
        platInfo = '[unknown]'
    md.append('platform: ' + platInfo)
    md.append('--- end of meta-data %s ---' % now)
    return '\n'.join(md)

def encrypt(datafile, pubkeyPem, meta=True, keep=None):
    """Encrypt a file using openssl, AES-256, and an RSA public-key.
    
    Returns: full path to the encrypted file (= .tgz bundle of 3 files). By default
    the original plaintext is deleted after encryption (see parameter `keep`).
    
    The idea is that you can have and share a public key, which anyone can use to
    encrypt things that only you can decrypt. Generating good keys and
    managing them is non-trivial, and is entirely up to you. (GPG can help a lot.)
    For better security, it is good to use signed public keys. No attempt is made
    here to verify key signatures automatically; you could do so manually using `verify()`.
    
    :Parameters:
    
        `datafile`:
            The path (name) of the original plaintext file to be encrypted.
        `pubkeyPem`:
            The public key to use, specified as the path to a .pem file. Example
            file contents (1024 bit pub.pem)::
            
                -----BEGIN PUBLIC KEY-----
                MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBALcw2C2Tyiq514Nc+Oe1TvweyzK92PSm
                s7KYMziTNcMy50E9KjSb7k8U/6Jaz/foeWFJqID1cmiyj1whZfZ4KycCAwEAAQ==
                -----END PUBLIC KEY-----
                
        `meta`:
            If `True`, include meta-data as plaintext in the archive::
            
                original file name & sha256 of encrypted
                platform & date
                openssl version, padding
                pubkey info (to aid in key rotation)
                
        `keep`:
            None (default) = remove original (unencrypted) & all intermediate files (more secure)
            'orig' = leave original file, delete intermediate (encrypted) files
            'all' = leave all intermed files & orig (for testing purposes)
    """
    logging.debug('encrypt (beta): start')
    if not datafile or not os.path.isfile(datafile):
        msg = 'encrypt (beta): no data to encrypt; %s not found'  % datafile
        logging.error(msg)
        raise ValueError(msg)
    # good file names:
    if not pubkeyPem or not os.path.isfile(pubkeyPem): 
        msg = 'encrypt (beta): missing public-key.pem file; %s not found' % pubkeyPem
        logging.error(msg)
        raise ValueError(msg)    
    # can't / don't proceed without a pub key of sufficient length:
    pkLen = len(open(pubkeyPem).read()) # proxy for number of bits in key
    if pkLen < 271: # or 451 chars for 2048 bit
        raise PublicKeyTooShortError("public key < 1024 bits")
    if not keep in [None, 'orig', 'all']:
        raise ValueError("encrypt (beta): bad value for 'keep' parameter")
    
    # do encryption via encMethod: data.txt --> (data.aes256, data.aes256.pwd.rsa, data.meta)
    # the two ideas here are 1) to do the call in a way that ensures that the call is
    # documentatble (in meta-data), so encMethod is the name that is actually used.
    # and 2) with more work, this will allow a user to specify some other encryption 
    # tool, eg, gpg or pgp, and that will be able to just drop as and arg (+ kwarg dict), while
    # retaining the .tgz bundle part
    encMethod = '_encrypt_rsa_aes256cbc'
    dataEncFile, pEncFile = eval(encMethod + '(datafile, pubkeyPem)')
    
    # bundle as a tarfile: (data.aes256, data.aes256.pwd.rsa) --> data.enc.tgz:
    savedLocation = os.path.abspath(os.path.curdir)
    root, _ = os.path.split(os.path.abspath(datafile))
    os.chdir(root) # cd into dir containing datafile
    tgzFile = _uniqFileName(os.path.splitext(datafile)[0] + BUNDLE_EXT) # same name, new ext
    files = [dataEncFile, pEncFile] # files to be bundled in .tgz
    # encryption meta-data:
    if meta:
        metaDataFile = os.path.split(datafile)[1] + META_EXT
        f = open(metaDataFile, 'wb')
        # idea: append new meta after a string, e.g., old meta data in rotate
        if type(meta) == str:
            f.write(meta+'\n')
        f.write(_getMetaData(datafile, dataEncFile, pubkeyPem, encMethod))
        f.close()
        files.append(metaDataFile)
    tar = tarfile.open(tgzFile, "w:gz")
    for name in files:
        # remove leading tmp path info from name
        tar.add( os.path.split(name)[1] )
        if keep != 'all':
            os.remove(name) # remove intermediate encrypted files
    tar.close()
    os.chdir(savedLocation)
    if not keep: # remove unencrypted original
        os.remove(datafile)

    return os.path.abspath(tgzFile)    

def _encrypt_rsa_aes256cbc(datafile, pubkeyPem):
    """Encrypt a datafile using openssl to do rsa pub-key + aes256cbc.
    """
    logging.debug('_encrypt_rsa_aes256cbc: start')
    pwd = _onetimePwd(n=65)
    pwdText = _openTmp()
    pwdText.write(pwd)
    try:
        pwdText.seek(0) # go back to start of tmp file
        
        # RSA-PUBKEY-encrypt the password, to file:
        pwdFileRsa = PWD_EXT +'_file' + RSA_EXT
        cmdRSA = [OPENSSL, 'rsautl', '-in', pwdText.name, '-out', pwdFileRsa,
                     '-inkey', pubkeyPem, '-keyform', 'PEM',
                     '-pubin', RSA_PADDING, '-encrypt']
        so = _shellCall(cmdRSA)
        
        # AES-256-CBC encrypt datafile, using the one pwd:
        dataFileEnc = os.path.abspath(datafile) + AES_EXT
        pwdFileRsaNew = _uniqFileName(dataFileEnc + pwdFileRsa.replace('_file', ''))
        os.rename(pwdFileRsa, pwdFileRsaNew) # rename the pwd_file to match the datafile
        
        # here gzip the raw datafile?
        cmdAES = [OPENSSL, 'enc', '-aes-256-cbc', '-a', '-salt', '-in', datafile,
               '-out', dataFileEnc, '-pass', 'file:' + pwdText.name]
        so = _shellCall(cmdAES)
    finally:
        _wipeClose(pwdText)
    
    return os.path.abspath(dataFileEnc), os.path.abspath(pwdFileRsaNew)

def decrypt(dataEnc, privkeyPem, passphraseFile='', outFile=''):
    """Decrypt a file that was encoded using `encrypt()`.
    
    To get the data back, need two files: `data.enc` and `privkey.pem`. If the
    private key has a passphrase, you'll need that too.
    """
    logging.debug('decrypt (beta): start')
    privkeyPem = os.path.abspath(privkeyPem)
    dataEnc = os.path.abspath(dataEnc)
    if passphraseFile:
        passphraseFile = os.path.abspath(passphraseFile)
        
    # check for bad paths:
    if not dataEnc or not os.path.isfile(dataEnc):
        raise ValueError('could not find <file>%s file %s' % (BUNDLE_EXT, str(dataEnc)))
    if not tarfile.is_tarfile(dataEnc):
        raise AttributeError('%s lacks expected internal format (.tgz)' % dataEnc)
    tar = tarfile.open(dataEnc, "r:gz")
    badNames = [f for f in tar.getmembers() if f.name[0] in ['.', os.sep] or f.name[1:3] == ':\\']
    if len(badNames):
        raise InternalFormatError(
            'unexpected file name(s) internal file (leading . or %s)' % os.sep)
    
    # extract & decrypt:
    tmp = mkdtemp()
    try:
        tar.extractall(path=tmp) # extract from .tgz file
        tar.close()
        fileList = os.listdir(tmp) # expect 2 or 3 files, identify them:
        for f in fileList:
            if f.endswith(AES_EXT):
                dataFileEnc = os.path.join(tmp, f)
            elif f.endswith(PWD_EXT + RSA_EXT):
                pwdFileRsa = os.path.join(tmp, f)
            elif f.endswith(META_EXT):
                metaFile = os.path.join(tmp, f)
        # decrypt to a file within tmp:
        dataFileDecr = _decrypt_rsa_aes256cbc(dataFileEnc, pwdFileRsa, privkeyPem,
                                passphraseFile=passphraseFile, outFile=outFile) 
        # move dec and meta files out of tmp:
        newLocation = _uniqFileName(dataFileDecr.replace(tmp, '').lstrip(os.sep))
        os.rename(dataFileDecr, newLocation) 
        newLocationMeta = _uniqFileName(metaFile.replace(tmp, '').lstrip(os.sep))
        os.rename(metaFile, newLocationMeta)
    finally:
        try:
            shutil.rmtree(tmp, ignore_errors=False)
        except WindowsError:
            assert not len(os.listdir(tmp.name)) # oops, should be empty
    
    return os.path.abspath(newLocation)

def _decrypt_rsa_aes256cbc(dataFileEnc, pwdFileRsa, privkeyPem, passphraseFile=None, outFile=''):
    """Decrypt a file that was encoded by _encrypt_rsa_aes256cbc()
    """
    logging.debug('_decrypt_rsa_aes256cbc: start')
    pwdText = _openTmp()
    try:
        # extract unique password from pwdFileRsa using the private key & passphrase
        cmdRSA = [OPENSSL, 'rsautl', '-in', pwdFileRsa, '-out', pwdText.name, '-inkey', privkeyPem]
        if passphraseFile:
            cmdRSA += ['-passin', 'file:' + passphraseFile]
        cmdRSA += [RSA_PADDING, '-decrypt']
        
        so, se = _shellCall(cmdRSA, stderr=True) # extract
        if 'unable to load Private Key' in se:
            raise PrivateKeyError('unable to load Private Key')
        elif 'RSA operation error' in se:
            raise DecryptError('unable to use Private Key, RSA operation error; wrong key?')
        
        # decide on name for decrypted file:
        if outFile:
            dataDecrypted = outFile
        else:
            dataDecrypted = os.path.abspath(dataFileEnc).replace(AES_EXT,'')
        
        # decrypt the data using the recovered password:
        cmdAES = [OPENSSL, 'enc', '-d', '-aes-256-cbc', '-a', '-in', dataFileEnc,
                           '-out', dataDecrypted, '-pass', 'file:'+pwdText.name]
        so, se = _shellCall(cmdAES, stderr=True)
    finally:
        _wipeClose(pwdText)
    if 'bad decrypt' in se:
        raise DecryptError('_decrypt_rsa_aes256cbc: openssl bad decrypt')
    
    return os.path.abspath(dataDecrypted)

def rotate(fileEnc, oldPriv, newPub, passphraseFile=None, keep=None):
    """Swap old encryption for new (decrypt-then-re-encrypt).
    
    Returns path to new encrypted file, adding to the meta-data."""
    logging.debug('starting rotate (beta)')
    fileDec = decrypt(fileEnc, oldPriv, passphraseFile=passphraseFile)
    oldMeta = open(fileDec + META_EXT).read()
    rotMsg = "\n\n--- key rotation: ---"
    time.sleep(.05)
    newFileEnc = encrypt(fileDec, newPub, meta=oldMeta+rotMsg, keep=keep)
    
    return newFileEnc

def sign(file, priv, passphraseFile=None):
    """Use a private key to sign a given file.
    
    Returns the signature as string, which can be passed to `verify()`
    """
    logging.debug('starting sign (beta)')
    tmp_hash = _openTmp()
    h = _sha256b64(file)
    tmp_hash.write( h )
    tmp_hash.seek(0)
    cmdSIGN = [OPENSSL, 'rsautl', '-sign', '-inkey', priv]
    if passphraseFile:
        cmdSIGN += ['-passin', 'file:'+passphraseFile]
    sig = _shellCall(cmdSIGN+['-in', tmp_hash.name])
    _wipeClose(tmp_hash)
    
    return b64encode(sig)

def verify(file, pub, sig):
    """Use a public key to verify file integrity (signature), as matching hash (sha256)
    """
    logging.debug('starting verify (beta)')
    tmp_sig = _openTmp()
    tmp_sig.write( b64decode(sig) )
    tmp_sig.seek(0)
    hashOfFile = _sha256b64(file) # do here = more time between tmp_sig write and hashFromSIg
    cmdVERIFY = [OPENSSL, 'rsautl', '-verify', '-inkey', pub, '-pubin', '-in', tmp_sig.name]
    hashFromSig = _shellCall(cmdVERIFY)
    # file access time can cause intermittent failures, so delay and try again:
    if not hashFromSig.strip():
        tmp_sig.seek(0)
        hashFromSig = _shellCall(cmdVERIFY)
    logging.debug('hash from sig %s' % hashFromSig)
    logging.debug('hash of file  %s' % hashOfFile)
    _wipeClose(tmp_sig)

    return bool( hashFromSig == hashOfFile )

def _testPubEncDec(secretText):
    """Tests: Aim for complete coverage of this file, not of openssl
    """
    def _genRsaKeys(pub='pubkey.pem', priv='privkey.pem', pphr=None, bits=2048):
        """Generate new pub and priv keys, return full path to new files
        
        This is intended for testing purposes, not for general use. Definitely
        need to consider: randomness, bits, file permissions, file location (user
        home dir?), passphrase creation and usage, passphrase as file generally
        not so good, can make sense to have no passphrase, ....
        Well-seeded PRNGs are reasonably good; ideally use hardware RNG
        gnupg sounds pretty good, cross-platform
        """
        logging.debug('_genRsaKeys: start')
        # generate priv key:
        cmdGEN = [OPENSSL, 'genrsa', '-out', priv]
        if pphr:
            cmdGEN += ['-des3', '-passout', 'file:' + pphr]
        cmdGEN +=  [str(bits)]
        so = _shellCall(cmdGEN)
        
        # extract pub from priv:
        cmdGENpub = [OPENSSL, 'rsa', '-in', priv, '-pubout', '-out', pub]
        if pphr:
            cmdGENpub += ['-passin', 'file:' + pphr]
        so = _shellCall(cmdGENpub)
        
        return os.path.abspath(pub), os.path.abspath(priv)
    
    # make a tmp data file holding secrect text, will get encrypted & decrypted:
    cwd = os.path.split(os.path.abspath(__file__))[0] 
    pathToSelf = os.path.abspath(__file__) # for cmd-line version of decryption call
    tmp = mkdtemp()
    logging.debug('tests make tmp dir %s' % tmp)
    try: # so we can always remove the tmp dir, in finally
        os.chdir(tmp) # work inside for easy clean-up
        
        datafile = os.path.join(tmp, 'data.txt')
        f = open(datafile, 'wb')
        f.write(secretText)
        f.close()
        dataFileWHITESPACE = os.path.join(tmp, 'data space.txt')
        shutil.copy(datafile, dataFileWHITESPACE)
        
        # set-up to make some key-pairs to test decrypt(encrypt()) 
        privTmp1 = os.path.join(tmp, 'privkey1.pem')
        pubTmp1 = os.path.join(tmp, 'pubkey1.pem')
        passphrsTmp1 = os.path.join(tmp, 'passphrs1.txt')
        f = open(passphrsTmp1, 'w+b')
        f.write(_onetimePwd(45))
        f.close()
        pub1, priv1 = _genRsaKeys(pubTmp1, privTmp1, pphr=passphrsTmp1, bits=1024)
        
        privTmp2 = os.path.join(tmp, 'privkey2.pem')
        pubTmp2 = os.path.join(tmp, 'pubkey2.pem')
        passphrsTmp2 = os.path.join(tmp, 'passphrs2.txt')
        f = open(passphrsTmp2, 'w+b')
        f.write(_onetimePwd(45))
        f.close()
        #pub2, priv2 = _genRsaKeys(pubTmp2, privTmp2, bits=1024)
        
        logging.debug('test: generating 1024 bit key with passphrase')
        cmd = [OPENSSL, 'rsa', '-in', priv1, '-passin', 'file:'+passphrsTmp1, '-text']
        out = _shellCall(cmd)
        good_new_keypair_bits_1024 = ( out.startswith('Private-Key: (1024 bit)') ) # test
        
        # test decrypt with GOOD passphrase': -----------------
        logging.debug('test good_enc_dec_pphr_1024')
        dataEnc = encrypt(datafile, pub1, keep='all')
        dataEncDec = decrypt(dataEnc, priv1, passphraseFile=passphrsTmp1)
        good_enc_dec_pphr_1024 =  ( open(dataEncDec).read() == secretText ) # test
        
        # test decrypt via command line: -----------------
        logging.debug('test good_enc_dec_cmdline')
        os.remove(dataEncDec) # i.e., try to recreate this decrypted file
        cmdLineCmd = ['python', pathToSelf, dataEnc, priv1, passphrsTmp1]
        dataEncDec_cmd = _shellCall(cmdLineCmd)
        good_enc_dec_cmdline =  ( open(dataEncDec_cmd).read() == secretText ) # test
        
        # encrypt with file name with white space: -----------------
        logging.debug('test good_whitespace_filename_OK')
        try:
            good_whitespace_filename_OK = True # test
            encrypt(dataFileWHITESPACE, pub1, keep='orig')
        except:
            good_whitespace_filename_OK = False # test
        
        # a BAD passphrase should fail: -----------------
        logging.debug('test bad_pphr_1024')
        try:
            bad_pphr_1024 = False # test
            decrypt(dataEnc, priv1, passphraseFile=passphrsTmp2)
        except PrivateKeyError:
            bad_pphr_1024 = True # test
        
        # nesting of decrypt(encrypt(file)) should work: -----------------
        try:
            logging.debug('test good_dec_enc_nest')
            dataDecNest = decrypt(encrypt(datafile, pub1, keep='all'), priv1, passphraseFile=passphrsTmp1)
            good_dec_enc_nest = (open(dataDecNest).read() == secretText ) # test
        except OSError: # rare: sometimes seems too fast for file system, so try again
            logging.debug('test good_dec_enc_nest')
            dataDecNest = decrypt(encrypt(datafile, pub1, keep='all'), priv1, passphraseFile=passphrsTmp1)
            good_dec_enc_nest = (open(dataDecNest).read() == secretText ) # test
        
        # nested, with white space in file name: -----------------
        try:
            logging.debug('test good_whitespace_nested_decenc_OK')
            dataDecNestWhitesp = decrypt(encrypt(dataFileWHITESPACE, pub1, keep='all'), priv1, passphraseFile=passphrsTmp1)
            good_whitespace_nested_decenc_OK = (open(dataDecNestWhitesp).read() == secretText ) # test
        except OSError: # rare: sometimes seems too fast for file system, so try again
            logging.debug('test good_whitespace_nested_decenc_OK')
            dataDecNestWhitesp = decrypt(encrypt(dataFileWHITESPACE, pub1, keep='all'), priv1, passphraseFile=passphrsTmp1)
            good_whitespace_nested_decenc_OK = (open(dataDecNestWhitesp).read() == secretText ) # test
                    
        # a correct-format but KNOWN-BAD (NEW) private key should fail: -----------------
        logging.debug('test bad_decrypt_BAD')
        _, priv2_2048 = _genRsaKeys(pubTmp2, os.path.join(tmp, 'privkey_NEW.pem'), bits=2048)
        try:
            bad_decrypt_BAD = False # test
            dataEncDec = decrypt(dataEnc, priv2_2048) # intended to raise
        except DecryptError:
            bad_decrypt_BAD = True # test
        
        # should refuse-to-encrypt if pub key is too short: -----------------
        logging.debug('test bad_pubkey_too_short')
        pub256, _ = _genRsaKeys('pubkey256.pem', 'privkey256.pem', bits=256)
        try:
            bad_pubkey_too_short = False # test
            dataEnc = encrypt(datafile, pub256) # intended to raise
        except PublicKeyTooShortError:
            bad_pubkey_too_short = True # test
        
        pub2, priv2 = _genRsaKeys(pubTmp2, privTmp2, bits=1024)
        
        # verify a signed file: ---------
        logging.debug('test bad_verify_bad_key')
        reps=10
        good_sig = []
        for i in xrange(reps):
            good_sig.append(sign(datafile, priv1, passphraseFile=passphrsTmp1))
            if reps > 1: logging.debug('test sign, rep %d' % i )
        good_sign = all(good_sig) # test
        sig = good_sig[0]
        
        good_ver = []
        bad_v = []
        bad_ver = []
        # stress test it:
        reps=10
        for i in xrange(reps): 
            good_ver.append(verify(datafile, pub1, sig)) # test
            bad_v.append(not verify(pub1, pub2, sig)) # test
            bad_ver.append(not verify(datafile, pub2, sig)) # test
            logging.debug('test verify, rep %d' % i )
        good_verify = all(good_ver)
        bad_verify = all(bad_v)
        bad_verify_bad_key = all(bad_ver)
        logging.debug( 'rep-test verify x %d: %d %d %d: '% (reps, \
                    len([i for i in good_ver if i]),\
                    len([i for i in bad_v if i]),\
                    len([i for i in bad_ver if i])))
        logging.debug( 'rep-test sign x %d: %d '%( reps, len([i for i in good_sig if i])))
        
        # rotate encryption: -----------------
        logging.debug('test rotate encryption keys')
        en = encrypt(dataFileWHITESPACE, pub1, keep='all')
        ro = rotate(en, priv1, pub2, passphraseFile=passphrsTmp1)
        de = decrypt(ro, priv2)
        good_rotate = bool( open(de).read() == secretText ) # test
        
        # minimal check of the meta-data from key rotation: -----------------
        logging.debug('test good_rotate_metadata')
        # look for two HMAC, check that they differ (do encrypt-then-MAC)
        meta = open(de + META_EXT).readlines()
        hashes = [line.split()[-1] for line in meta if line.startswith('HMAC')]
        good_rotate_metadata = bool( len(hashes) == 2 and not hashes[0] == hashes[1] ) # test
        
    finally: # remove all tmp stuff before doing any asserts
        try:
            shutil.rmtree(tmp, ignore_errors=False)
        except WindowsError:
            if len(os.listdir(tmp)):
                print "test dir left behind was not empty"
            # win xp in parallels: shutil.rmtree removes everything except tmp
            # I get "in use by another process", even after a time.sleep(5)
    
    # NB: 'bad_' tests pass if an error situation results in the appropriate error:
    logging.info('test begin reporting')
    assert good_enc_dec_pphr_1024 # FAILED encrypt -> decrypt using new rsa keys, 1024 bits
    logging.info('PASS good decrypt with good passphrase')
    assert good_new_keypair_bits_1024 # new rsa key FAILED to report 1024 bits
    logging.info('PASS new RSA key reported 1024 bits as requested')
    assert good_enc_dec_cmdline # FAILED to decrypt using command-line call
    logging.info('PASS good decrypt via command line')
    assert good_dec_enc_nest # something FAILED when nesting decrypt(encrypt(file)); just try again?
    logging.info('PASS nested decrypt(encrypt(file)) okay,')
    assert good_whitespace_filename_OK # a filename with whitepsace FAILED
    logging.info('PASS encrypt(file) okay, white space file name')
    assert good_whitespace_nested_decenc_OK # a filename with whitepsace FAILED
    logging.info('PASS nested decrypt(encrypt(file)) okay, white space file name')
    assert bad_pphr_1024 # a known-bad passphrase FAILED to result in an error
    logging.info('PASS a bad passphrase failed')
    assert bad_decrypt_BAD # known-bad private key FAILED to refuse to decrypt
    logging.info('PASS a correct-format but known-bad private key failed')
    assert bad_pubkey_too_short # known-to-be-too-short public key FAILED to refuse to encrypt
    logging.info('PASS refused-to-encrypt when pub key is too short')
    assert good_rotate # failed to properly rotate encryption with new key (decrypt failed)
    logging.info('PASS good decrypt after rotating the encryption key')
    assert good_rotate_metadata # failed to properly generate meta-data during key rotation
    logging.info('PASS minimal reasonableness of meta-data after rotation')
    
    assert good_verify # failed to verify a signed file
    logging.info('PASS verified a signed file')
    assert bad_verify # failed to fail to verify a wrong file (this is an error)
    logging.info('PASS refused to verify bad signature (wrong file)')
    assert good_sign # FAILED to get any return value from a sign() call
    logging.info('PASS got a signature')
    assert bad_verify_bad_key # failed to refuse to verify using wrong pub key (this is an error)
    logging.info('PASS refused to verify bad signature (wrong key)')
    
    logging.info('test SUCCESS, reporting complete')
    #raw_input()
    
if __name__ == '__main__':
    if sys.platform in ['win32']:
        logging.warning('can leave an empty "tmp" dir behind on Windows')

    # command-line usage: arguments determine execution
    if len(sys.argv) == 1:
        """no args => run tests"""
        try:
            logging.console.setLevel(logging.INFO) # for psychopy
        except:
            pass
        logging.info('running self-tests; NB: should see some error messages but not failed tests')
        _testPubEncDec('secret snippet %.6f' % time.time())
    else:
        """pass sys.args to encrypt or decrypt(), eg:
            $ python openssl_wrap.py data.enc.tgz privkey.pem [passphrase_file]
        """
        if sys.argv[1] == 'enc':
            del sys.argv[1]
            print encrypt(*sys.argv[1:])
        elif sys.argv[1] == 'dec':
            del sys.argv[1]
            print decrypt(*sys.argv[1:])
        else:
            print decrypt(*sys.argv[1:])