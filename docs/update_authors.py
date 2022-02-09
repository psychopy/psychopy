#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Regenerate AUTHORS.md
"""
import codecs
import warnings
from datetime import datetime
from psychopy.core import shellCall
from pathlib import Path

repo_path = Path(__file__).parent.parent
authors_path = repo_path/'AUTHORS.md'
git_command = 'git --no-pager shortlog -s HEAD %s' % repo_path
last_run = datetime.utcnow().strftime('%B %d, %Y')

authors_header = """Authors
-------

**PsychoPy is developed through community effort.**

The project was created and is maintained by Jonathan Peirce.
The following individuals have contributed code or documentation to 
PsychoPy:\n
"""

do_not_edit_note = """
---
*This list was auto-generated via `gen_authors.py`. Do not edit manually.*\n
*Last updated on %s (UTC).*
""" % last_run


if __name__ == '__main__':
    short_log = shellCall(git_command)
    
    authors = []
    for line in short_log.splitlines():
        contributions, author = tuple(line.split('\t'))
        if author != 'unknown':
            authors.append(author)
        else:
            msg = ('Unknown author found and skipped; please revise the output '
                   'of `git shortlog -se` and consider amending .mailmap')
            warnings.warn(msg)

    with codecs.open(authors_path, 'w', encoding='utf-8') as f:
        f.write(authors_header)
        f.writelines(['* %s\n' % author for author in authors])
        f.write(do_not_edit_note)
