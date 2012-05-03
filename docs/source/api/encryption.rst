
:mod:`psychopy.contrib.opensslwrap` Encryption *(beta)*
=======================================================

Overview
--------

**Aim:** Better protect psychology and neuroscience lab information from casual inspection
or accidental disclosure, using public-key encryption for security and flexibility.

Example use-case: Encrypt a data file on a testing-room computer for better privacy and
data integrity, before moving or archiving it. Do so from wihtin PsychoPy, without
ever needing to be able to decrypt on the same computer or store a decryption
password in an archive.

Encryption involves some special considerations that are not relevant to other
aspects of PsychoPy. Perhaps the most important thing to note is that, depending on your
circumstances, the use of encryption can conflict with policies of your boss or
institution (or even government). You are responsible for knowing your situation,
and for the consequences of your decisions about whether and how to use encryption.

**Status & Caveats:** As of April 2012, this is **beta software**, made available for
**evaluation and testing purposes**. All feedback can be posted to the psychopy-dev list.

The built-in tests can be run from the command line::

    $ python opensslwrap.py

or save the output to a log file (not sure about Windows syntax for this)::

    $ python opensslwrap.py >& test.log
    
They can also be run from the PsychoPy test-suite (under testContrib).

Reports of failed tests are especially welcome, as are ideas for other tests, or
questions or comments about the documentation (below). Reports of successful
tests with information about the operating system are also useful. The command line
tests are designed to work without requiring that psychopy be installed.

If the test output ends with "test SUCCESS, reporting complete", that's a success.
(If the testContrib test-battery passes
from the PsychoPy test-suite, that is also success.) Note that some of the tests
are designed to check error situations; i.e., what is being tested is that situations
that should fail, do fail, and are recognized as failure situations. This means
that you **should** see some things that look exactly like error messages along
the way (e.g., "RSA operation error"); the key thing is seeing SUCCESS at the end.

If you venture beyond running the test-suite, which is certainly encouraged, please
do so for testing purposes, not for mission-critical applications. To try it out,
you will need at least one RSA key pair. (For the test-suite, key pairs are auto-generated
and then deleted). A hint for the curious: "openssl genrsa --help", or look through
the test code, and then do your homework. For high-quality keys, PGP or GnuPG are better.

You should **not** assume that it will meet HIPAA, FIPS 140-2, or some other requirement.
There's been no proper security audit at this point; the effective level of security
is currently best described as "unknown". The aim is that the encryption will be
effective for the  purpose of data transfer and storage within a lab, and assumes
that a) the data have low economic value data, and b) the lab has reasonable physical
and network security, and has only trusted people working there.

The encryption is
definitely strong enough to cause trouble if used incorrectly. Consider an example:
Although you can lock yourself out of your own car, you can hire someone with training
and special tools to break in on your behalf. With encryption, however, it would
likely be prohibitively expensive to hire someone to break in on your behalf, and
might not be possible. So you could actually lose your data by trying to secure it.
Please also note that, for better security, the default behavior is to delete the
unencrypted original file (it can be retained, as an option; see Example 2 below).

**Security strategy:** The methods provided rely only on the widely used software
package, OpenSSL, using its implementation of RSA and AES (which are industry standards).
Many people are invested in making OpenSSL robust, and one specific version of OpenSSL
has received FIPS 140-2 certification (http://www.openssl.org/docs/fips/fipsnotes.html).
The effective weak link is almost certainly not cryptographic but rather in how the
encryption key(s) are handled, which partly depends on you, including generation,
signing, storage, backup. (For what its worth: the cryptographic weak link is
the RSA public key, especially because: 1) key verification is not attempted, and
2) you, as the user, can provide keys of varying strengths, including key length,
entropy quality, provenance, handling.) If the keys are bad or compromised, the
encryption strength is basically irrelevant.

Using a public-key as part of encryption allows a non-secret "password" (the public
key) to be distributed for encryption. This separates encryption from decryption,
allowing logical and physical separation, giving considerable flexibility. The idea
is that anyone anywhere can encrypt information that only a trusted process (with
access to the private keys) can decrypt. Anyone anywhere can know the process used
to achieve the encryption without compromising the achievable degree of security.
Its the private key that is essential to keep private.

Some considerations:

- Tests are provided as part of the library. To run all tests, run "python opensslwrap.py"
  from the command line. This should work on machines with python 2.5+ and openssl 0.9.8+.
- OpenSSL is not distributed as part of the library. You need to obtain it separately
  (and may already have it; see Installation, below).
- Encrypt and decrypt only on trusted machines, with access limited to trusted people.
- By design, the computer used for encryption can be different from the computer used
  for decryption; it can be a different device, operating system, and openssl version.
- "Best practice" is not to move your private key from the machine on which it was
  generated; certainly never ever email it. Its fine to share the public key.
- Some good advice from GnuPG: "If your system allows for encrypted swap partitions,
  please make use of that feature."

**Usage Examples:**

In general items are given as the name of a file, not as the item itself.

1. Encrypt a plaintext file named `data`, using a .pem format RSA `pubkey`::

    >>> from opensslwrap import *
    >>> data = '/path/to/data.txt'
    >>> pubkey = '/path/to/my/pubkey.pem'
    >>> ciphertext = encrypt(data, pubkey)

   `ciphertext` is a path to (i.e., the file name of) the newly encrypted data,
   `data` is the path to the unencrypted (original, plaintext) data, and `pubkey`
   is the path to the PEM format public-key.
   
   .. note:: The default behavior is to delete the unencrypted file, `data`. This
            seems safer from a security standpoint.

   .. note:: The private key is not involved at all in encryption, meaning that
            it can be stored on another machine entirely.

2. Same as example 1, but don't delete the original (unencrypted) datafile::

    >>> ciphertext = encrypt(data, pubkey, keep='orig')

3.  Decrypt the ciphertext, using the private key that's paired with
    `pubkey`, with an optional `passphrase` stored in a file (will try to prompt for passphrase
    if `privkey` has a passphrase and its path is not given)::

      >>> plaintext = decrypt(ciphertext, privkey [, passphrase])
    
4. Change (rotate) the RSA encryption keys, swapping out an old one, replacing
   with a new one (again, using filenames)::

     >>> rotate(ciphertext, privkey_old, pubkey_new, priv_passphrase)

**Questions:**

Q: Will encryption make my data safe?

A: Think of it as adding another layer of security, of itself not
being a complete solution. There are many issues involved in securing your
data, and encryption alone does not magically solve all of them. Security needs
to be considered at all stages in the process. The encryption provided (RSA + AES)
is genuinely strong encryption (and as such could cause problems). Key management
is the hard part (which is why PsychoPy does not attempt to do it for you.)

Q: What if I think my private RSA private key is no longer private?

A: Obviously, try to avoid this situation. If it happens: 1) Generate a new
RSA key-pair, and then 2) `rotate()` the encryption on all files that were encrypted
using the public key associated with the compromised private key (see below on how
to rotate).

The meta-data includes information about what public key was used for
encryption, to make it easier to identify the relevant files. But even without that
information, you could just try rotate()'ing the encryption on all files, and it
would only succeed for those with the right key pair. The meta-data are not
required for key rotation. PsychoPy is not needed for rotation (or decryption).
Even opensslwrap is not needed: It is just a wrapper to make it easier to work with
standard, strong encryption tools (i.e., openssl).

Q: What if the internal (AES) password was disclosed (i.e., not the private
key but the one-time password that is used for the AES encryption)?

A: This is not very likely, and it would affect at most one file. Fix: Just `rotate()`
the encryption for that file--using the same keys is fine. That is, if you decrypt
and re-encrypt (i.e., rotate) with the same key pair, a new internal one-time password
will be generated during the re-encryption step. (The old AES password is not re-used,
ever, which is a crucial difference between the AES password and the RSA key pair.)

Q: What if I lose my private key?

A: The whole idea is that, if you don't have the private key, the encryption should
be strong enough that data recovery is a very expensive proposition, if its even
possible (and hopefully its not possible). You should design your procedures under
the assumption that data recovery will not be possible if you lose the private key.
If you do lose the key, resign yourself to the idea that your encrypted data are
going to stay encrypted forever. This is not at all to say that it is impossible
for the encryption to be compromised by someone, just that you should not plan on
being able to do it, or even hire someone to do it.

**Known limitations:**

- Depends on calls to openssl using files, and files can sometimes be slow. In turn,
  this could cause something to fail. This is unlikely based on tests so far, but
  if it happens, just try again.
- File sizes are assumed to fit entirely in RAM, with no checking (generally fine).
- Testing so far has been in limited testing environments. All tests pass on:

    - Mac 10.6.8  OpenSSL 0.9.8r  python 2.7.1
    - Win XP sp2  OpenSSL 1.0.1  python 2.6.6
    - CentOS 6.2  OpenSSL 1.0.0  python 2.7.2 (without psychopy installed)

    Plus: a file encrypted on mac decrypted on both Win XP and CentOS.

**Principles and Approach:**

- Rely exclusively on standard widely available & supported tools and algorithms.
  OpenSSL and the basic approach (RSA + AES 256) are well-understood and recommended,
  e.g., http://crypto.stackexchange.com/a/15/ .
- Eventually opensslwrap.py will be signed and verifyable (once its more stable).
- Avoid obfuscation and "security through obscurity".
  Obfuscation does not enchance security, yet can make data recovery more difficult 
  or expensive. So transparency is more important. For this reason, meta-data
  are generated by default (which can be disabled). In particular, using explicit
  labels in file names does not compromise security; it just makes things less obscure..
- Encryption will refuse to proceed if the OpenSSL version < '0.9.8'; this will
  eventually go higher.
- Encryption will not proceed if the public key < 1024 bits (but go with 2048).
- AES256 is very strong cryptographically but requires a password (for symmetric
  encryption). A one-time password is generated, and never re-used for other data. 
- One key step is to use the password (and salt) to AES-encrypt the data::

    $ openssl enc -e -aes-256-cbc -a -salt -in file.txt -out file.enc -pass file:<pwd_file>

- A second key step is to RSA public-key encrypt the password (using OAEP padding)::

    $ openssl rsautl -in pwd_file.txt -out pwd_file.rsa -inkey public.pem -pubin -oaep -encrypt

- Include a hash (sha256) of the encrypted file in the meta-data.
- Bundle the bits together for ease of archiving and handling (one .tgz file,
  using ".enc" as the extension). 
- Decrypt by using the private key to recover the password (which is one of the files in
  the .tgz bundle), and then use the password to recover the data (from the AES-
  encrypted file in the bundle).
- The program does not try to manage the RSA keys. Its completely up to you (the user).
- Use and return full paths to files, to reduce ambiguity.

Installing OpenSSL
---------------------

- Mac & linux: openssl should be installed already, typically in /usr/bin/openssl
  If fact, if openssl is in a different location, a warning will be generated.
- Windows: download from http://www.slproweb.com/products/Win32OpenSSL.html
  On win XP, install into C:\\OpenSSL-Win32\\bin\\openssl.exe;
  Windows Vista and later will try to discover the installation path (not tested)
    
Encryption *(beta)*
-------------------
.. autofunction:: psychopy.contrib.opensslwrap.encrypt

Decryption *(beta)*
-------------------
.. autofunction:: psychopy.contrib.opensslwrap.decrypt

Key rotation *(beta)*
------------
.. autofunction:: psychopy.contrib.opensslwrap.rotate

Sign & verify *(beta)*
-------------
.. autofunction:: psychopy.contrib.opensslwrap.sign
.. autofunction:: psychopy.contrib.opensslwrap.verify
