#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Tools for working with packages within the Python environment.
"""

__all__ = [
    'getDistributions',
    'addDistribution',
    'getInstalledPackages'
]

import pkg_resources


def getDistributions():
    """Get a list of active distributions in the current environment.

    Returns
    -------
    list
        List of paths where active distributions are located. These paths
        refer to locations where packages containing importable modules and
        plugins can be found.

    """
    toReturn = list()
    toReturn.extend(pkg_resources.working_set.entries)  # copy

    return toReturn


def addDistribution(distPath):
    """Add a distribution to the current environment.

    This function can be used to add a distribution to the present environment
    which contains Python packages that have importable modules or plugins.

    Parameters
    ----------
    distPath : str
        Path to distribution. May be either a path for a directory or archive
        file (e.g. ZIP).

    """
    pkg_resources.working_set.add_entry(distPath)


def getInstalledPackages():
    """Get a mapping of installed packages with their metadata for the current
    environment.

    Returns
    -------
    dict
        Mapping where keys (`str`) are found package names and values are
        metadata. Metadata are mappings where keys (`str`) are field names and
        values (`Any`) are data related to each field.

    """
    toReturn = dict()

    # get packages and metadata
    for pkg in pkg_resources.working_set:
        pkg = pkg_resources.get_distribution(pkg.key)
        metadata = pkg.get_metadata(pkg.PKG_INFO)

        # parse metadata

        inHeader = True
        descriptionText = []
        metadict = dict()
        for line in metadata.split('\n'):
            if not line and inHeader:
                inHeader = False

            if not inHeader:
                descriptionText.append(line + '\n')  # restore NL after split
                continue

            # valid single line fields
            singleFields = (
                'Metadata-Version',
                'Name',
                'Version',
                'Summary',
                'Home-page',
                'Author',
                'Author-email',
                'License',
                'Keywords',
                'Description-Content-Type'
            )

            if any([line.startswith(f + ':') for f in singleFields]):
                fieldName, fieldValue = [p.strip() for p in line.split(':', 1)]
                # add only if the field is not already present
                if fieldName not in metadict.keys():
                    metadict[fieldName] = fieldValue
            elif line.startswith('Classifier:'):  # todo - handle these cases
                pass
            elif line.startswith('Requires-Dist:'):
                pass
            elif line.startswith('Platform:'):
                pass
            elif line.startswith('Requires-Python:'):
                pass

        if descriptionText:
            metadict['Description'] = ''.join(descriptionText)

        toReturn[pkg.key] = metadict

    return toReturn


if __name__ == "__main__":
    pass
