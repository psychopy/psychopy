#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Generate template of translation file (.po) from source tree.
# preferences/generateHints.py is automatically invoked to update 
# localization of popup hints on the Preference Dialog.
# 
#

from __future__ import absolute_import, print_function

import os
import sys
import subprocess
import codecs
import shutil
import git
import babel.messages.frontend
import babel.messages.pofile
import argparse

from psychopy import __version__ as psychopy_version

#
# commandline argument
#

parser = argparse.ArgumentParser(description='usage: foo.py [-h] [-c]')
parser.add_argument('-c', '--commit', action='store_true', help='Commit messages.pot if updated.', required=False)

command_args = parser.parse_args()

#
# hints.py must be updated to find new hints
#

subprocess.call(['python', 'generateHints.py'], cwd='../preferences')

#
# Extracting messages and generating new template file
#

new_pot_filename = 'messages_new.pot'
current_pot_filename = 'messages.pot'

argv = ['pybabel', '-q', 'extract',
        '--input-dirs=..',
        '--project=PsychoPy',
        '--version='+psychopy_version,
        '-k', '_translate',
        '-o', new_pot_filename]

babel_frontend = babel.messages.frontend.CommandLineInterface()
babel_frontend.run(argv)

#
# Comparing new and current pot file.
#

new_pot_messages = []
current_pot_id = []
untranslated_new = []

with codecs.open(new_pot_filename, 'r', 'utf-8') as fp:
    for message in babel.messages.pofile.read_po(fp):
        if message.id:
            new_pot_messages.append(message)

if not os.path.exists(current_pot_filename):
    # if current pot file doesn't exist, copy it from new pot file.
    shutil.copy(new_pot_filename, current_pot_filename)

with codecs.open(current_pot_filename, 'r', 'utf-8') as fp:
    for message in babel.messages.pofile.read_po(fp):
        if message.id:
            current_pot_id.append(message.id)

for message in new_pot_messages:
    if not message.id in current_pot_id:
        untranslated_new.append(message)


#
# Output summary
#
n_untranslated_locale = []

for root, dirs, files in os.walk('../app/locale/'):
    for file in files:
        if file=='messages.po':
            po_message_id = []
            n_untranslated = 0
            locale_identifier = os.path.basename(os.path.dirname(root))
            with codecs.open(os.path.join(root, file), 'r', 'utf-8') as fp:
                catalog = babel.messages.pofile.read_po(fp)
                for message in catalog:
                    if message.id:
                        po_message_id.append(message.id)
            for message in new_pot_messages:
                if not message.id in po_message_id:
                    n_untranslated += 1
            n_untranslated_locale.append((locale_identifier, n_untranslated))

n_messages = len(new_pot_messages)
summary_message = '\nNumber of messages in *.py files: {}\n'.format(n_messages)
summary_message += 'New message(s): {}\n\n'.format(len(untranslated_new))
summary_message += 'Untranslated message(s)\n'

for locale_identifier, n in n_untranslated_locale:
    summary_message += '  {}:{:>8} ({:>5.1f}%)\n'.format(locale_identifier, n, 100*n/n_messages)

# output to stdout
sys.stdout.write(summary_message)


#
# Update current pot file only if new strings were found.
#


if len(untranslated_new) > 0:
    # replace current pot file with new one.
    os.remove(current_pot_filename)
    os.rename(new_pot_filename, current_pot_filename)

    # add and commit template file if --commit is given
    if command_args.commit:
        sys.stdout.write('\nCommit messages.pot...\n')
        repo = git.Repo('../../')
        
        
        pot_file_path = 'psychopy/localization/' + current_pot_filename
        print(pot_file_path)
        print([item.a_path for item in repo.index.diff(None)])
        if pot_file_path in repo.untracked_files or pot_file_path in [item.a_path for item in repo.index.diff(None)]:
            repo.index.add([pot_file_path])
            repo.index.commit('ENH: Translation template is updated')

else:
    # keep current pot file and remove new one.
    os.remove(new_pot_filename)
