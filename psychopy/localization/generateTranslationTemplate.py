#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Generate template of translation file (.po) from source tree.
# preferences/generateHints.py is automatically invoked to update 
# localization of popup hints on the Preference Dialog.
# 
#

import os
import sys
import subprocess
import shutil
import git
import babel.messages.frontend
import polib
import argparse

from psychopy import __version__ as psychopy_version

locale_dir = '../app/locale/'
new_pot_filename = 'messages_new.pot'
current_pot_filename = 'messages.pot'
babel_frontend = babel.messages.frontend.CommandLineInterface()

target_files = [
    'psychopy/localization/messages.pot',
    'psychopy/preferences/hints.py',
    'psychopy/alerts/alertsCatalogue/alertmsg.py'
]

poedit_mime_headers = {
    "X-Poedit-KeywordsList": "_translate",
    "X-Poedit-Basepath": "../../../..", 
    "X-Poedit-SourceCharset": "UTF-8",
    "X-Poedit-SearchPath-0:": ".",
    "X-Poedit-SearchPathExcluded-0": "app/localization/utils",
    "X-Poedit-SearchPathExcluded-1": "app/Resources"
}

def generate_new_template(verbose=False):
    """
    Generate new POT file using pybabel.
    Before running pybabel, generateHints.py and generateAlertmsg.py are called
    to update lists of hints and alerts.
    
    Returns:
        None
    """

    # hints.py must be updated to find new hints and alarts
    if verbose:
        print('Generate hints.py... ', end='')
    subprocess.call(['python', 'generateHints.py'], cwd='../preferences')
    if verbose:
        print('Done.\nGenerate alartmsg.py... ', end='')
    subprocess.call(['python', 'generateAlertmsg.py'], cwd='../alerts/alertsCatalogue')
    if verbose:
        print('Done.')

    # Extracting messages and generating new template file

    if verbose:
        print('Generating new template file... ', end='')
    argv = ['pybabel', '-q', 'extract',
            '--input-dirs=..',
            '--project=PsychoPy',
            '--version='+psychopy_version,
            '--keyword=_translate',
            '--output-file='+new_pot_filename,
            '--ignore-dirs="app/localization/utils app/Resources"']
    babel_frontend.run(argv)
    if verbose:
        print('Done.')

def find_new_entries(verbose=False):
    """
    Count new entries in the new POT file.
    
    Returns:
        int: number of new entries.
        int: number of entries in the new POT file.
    """
    if verbose:
        print('Making a list of message IDs in the new template... ', end='')

    new_pot_msgids = []
    current_pot_msgids = []
    untranslated_new = 0

    if not os.path.exists(current_pot_filename):
        # if current pot file doesn't exist, copy it from new pot file.
        if verbose:
            print('INFO: create {}... '.format(current_pot_filename), end='')
        shutil.copy(new_pot_filename, current_pot_filename)

        # all entries are new.
        po_new = polib.pofile(new_pot_filename)
        untranslated_new = len(po_new.untranslated_entries())

    else:
        po_new = polib.pofile(new_pot_filename)
        for entry in po_new:
            if entry.msgid != '':
                new_pot_msgids.append(entry.msgid)
    
        po = polib.pofile(current_pot_filename)
        for entry in po:
            if entry.msgid != '':
                current_pot_msgids.append(entry.msgid)
    
        for id in new_pot_msgids:
            if id not in current_pot_msgids:
                untranslated_new += 1

    if verbose:
        print('{} new entries are found. Done.'.format(untranslated_new))
    return untranslated_new, len(po_new.untranslated_entries())

def merge_new_entries(verbose=False):
    """
    Merge new POT file to PO files.
    The 'Project-Id-Version' and 'POT-Creation-Date' in the PO files will be updated.
    No other metadata will be changed.

    returns:
        None
    """
    if verbose:
        print('Merging new POT to PO files...')

    pot = polib.pofile(new_pot_filename)
    pot_new = polib.pofile(new_pot_filename)
    pot_new.metadata.update(poedit_mime_headers)
    
    for loc in os.listdir(locale_dir):
        lc_message_dir = os.path.join(locale_dir, loc,'LC_MESSAGE')
        messages_po_path = os.path.join(lc_message_dir, 'messages.po')
        if not os.path.exists(lc_message_dir) or not os.path.isdir(lc_message_dir):
            print('WARNING: {} is not a valid locale directory.'.format(loc))
            continue
        if os.path.exists(os.path.join(locale_dir, loc, 'LC_MESSAGE','messages.po')):
            if verbose:
                print('  merge new POT to {}...'.format(messages_po_path))
            po = polib.pofile(messages_po_path)
            po.merge(pot) #merge 
            # update Project-Id-Version and POT-Creation-Date           
            po.metadata['Project-Id-Version'] = pot.metadata['Project-Id-Version']
            po.metadata['POT-Creation-Date'] = pot.metadata['POT-Creation-Date']
            po.save() # overwrite
        else:
            pot_new.metadata['Language'] = loc[:loc.find('_')]
            pot_new.save(messages_po_path)

    if verbose:
        print('Done.')

def check_translation_status(verbose=False):
    """
    Count translated messages in the PO files.

    returns:
        dict: number of translated messages (key: locale code)
    """
    status = {}

    if verbose:
        print('Checking current PO files...', end='')
    for loc in os.listdir(locale_dir):
        lc_message_dir = os.path.join(locale_dir, loc,'LC_MESSAGE')
        messages_po_path = os.path.join(lc_message_dir, 'messages.po')
        if os.path.exists(os.path.join(locale_dir, loc, 'LC_MESSAGE','messages.po')):
            po = polib.pofile(messages_po_path)
            translated = len(po.translated_entries())
            status[loc] = translated
    
    if verbose:
        print('Done.')
    return status


parser = argparse.ArgumentParser(description='usage: generateTranslationTemplate.py [-h] [-c]')
parser.add_argument('-c', '--commit', action='store_true', help='Commit messages.pot if updated.', required=False)
parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed processing information.', required=False)

args = parser.parse_args()

generate_new_template(verbose=args.verbose)
num_new_entries, num_total_entries = find_new_entries(verbose=args.verbose)

# if there are new entries, merge POT to existing PO files.
if num_new_entries > 0:
    merge_new_entries(verbose=args.verbose)

# check translation status
translation_status = check_translation_status(verbose=args.verbose)


summary_message = '\nNumber of messages in *.py files: {}\n'.format(num_total_entries)
summary_message += 'New message(s): {}\n\n'.format(num_new_entries)
summary_message += 'Untranslated message(s)\n'

for loc in translation_status.keys():
    n = translation_status[loc]
    summary_message += '  {}:{:>8} ({:>5.1f}%)\n'.format(loc, n, 100*n/num_total_entries)

# output to stdout
print(summary_message)

# Update current pot file only if new strings were found.

if num_new_entries > 0:
    # replace current pot file with new one.
    os.remove(current_pot_filename)
    os.rename(new_pot_filename, current_pot_filename)

    # add and commit template file if --commit is given
    if args.commit:
        if args.verbose:
            sys.stdout.write('\nCommit messages.pot...\n')

        repo = git.Repo('../../')
        updated = [item.a_path for item in repo.index.diff(None)]
        added = False

        # add if messages.pot is untracked or updated
        for file_path in target_files:
            if file_path in repo.untracked_files or file_path in updated:
                if args.verbose:
                    print('  add {}'.format(file_path))
                repo.index.add(file_path)
                added = True

        for loc in os.listdir(locale_dir):
            file_path = '/'.join(('psychopy/app/locale', loc,'LC_MESSAGE', 'messages.po'))
            if file_path in repo.untracked_files or file_path in updated:
                if args.verbose:
                    print('  add {}'.format(file_path))
                repo.index.add(file_path)
                added = True

        if added:
            repo.index.commit('ENH: Translation template is updated\n\n{}'.format(summary_message))

else:
    # keep current pot file and remove new one.
    os.remove(new_pot_filename)
