#! python3

"""Using Python to create a cross-platform function to 
compare sha checksums (mostly because windows pwsh annoying) """

import hashlib

def checksum(filename, sha_file, alg='sha256'):
    """Verify a hash and raise error if fails"""
    computed_hash = getattr(hashlib, alg)
    computed_hash = hashlib.sha256()
    with open(filename, 'rb') as f:
        computed_hash.update(f.read())
    computed_hash = computed_hash.hexdigest()
    with open(sha_file) as f:
        hash_value = f.read().split()[0]
    if computed_hash != hash_value:
        raise ValueError(f"The hash did not match:\n"
                         f"  - {filename}: {repr(computed_hash)}\n"
                         f"  - {sha_file}: {repr(hash_value)}")
    print(f"Confirmed checksum OK for: {filename}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
                    prog = 'checksum.py',
                    description = 'Checks a hash against a known sha '
                                  'value and raises error if not equal')
    parser.add_argument('filename')
    parser.add_argument('sha_file')
    parser.add_argument('alg', default='sha256')
    args = parser.parse_args()
    checksum(args.filename, args.sha_file, args.alg)