#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is a helper to keep demos in a reasonably consistent style
  For all demos/coder/subdir/*.py (there are ~70 or so total), write out a new file: coder_updated/subdir/*
"""

import sys
import glob
import os
import re
import io


valid_var_re = re.compile(r"^[a-zA-Z_][\w]*$")
coding = '# -*- coding: utf-8 -*-\n'
demo_license = '\n# The contents of this file are in the public domain.\n'


def get_contents(f1):
    with io.open(f1, 'r', encoding='utf-8-sig') as f:
        return f.read()


def add_shebang_encoding_future(f1):
    if not f1.startswith('#!'):
        f1 = '#!/usr/bin/env python\n' + f1
    
    if '# -*- coding:' not in f1:
        f = f1.split('\n', 1)
        f1 = f[0] + '\n' + coding + f[1]

    return f1


def remove_doublesharp_trailing_whitespace(f1):
    f1 = f1.replace('##', '#')
    f1 = f1.replace('\n#\n', '\n\n')
    return '\n'.join([line.rstrip() for line in f1.splitlines()]) + '\n'


def replace_PatchStim(f1):
    return f1.replace('PatchStim', 'GratingStim')


def replace_xrange(f1):
    return f1.replace('xrange', 'range')


def replace_myWin_win(f1):
    f1 = f1.replace('myWin', 'win')
    if 'iohub' in f1:
        f1 = f1.replace('window', 'win')
    return f1.replace('win.update()', 'win.flip')


def add_win_close_quit_demo_license(f1):
    # remove first, then add back consistently
    lines = f1.strip().splitlines()
    # need to avoid removing if they are indented:
    if lines[-2].startswith('win.close()') or lines[-2].startswith('core.quit()'):
        lines[-2] = ''
    if lines[-1].startswith('win.close()') or lines[-1].startswith('core.quit()'):
        lines[-1] = ''
    f1 = '\n'.join(lines)
    
    f1 += '\n'
    if 'Window(' in f1:  #  a visual.Window() is defined somewhere
        f1 += '\nwin.close()\n'
    if [line for line in lines if 'psychopy' in line and 'core' in line and 'import' in line]:
        f1 += 'core.quit()\n'

    if not demo_license in f1:
        f1 = f1 + demo_license
    
    return f1


def convert_inline_comments(f1):
    lines = f1.splitlines()
    for i, line in enumerate(lines):
        lines[i] = line.replace('#', '# ').replace('#  ', '# ')
        if '#' in line and not line.strip().startswith('#'):
            lines[i] = lines[i].replace('#', '  #').replace('   #', '  #').replace('   #', '  #')
    return '\n'.join(lines)


def replace_commas_etc(f1):
    # do after shebang, encoding
    f1 = f1.replace(',', ', ').replace(',  ', ', ')
    f1 = f1.replace('=visual', ' = visual')
    f1 = f1.replace('=data', ' = data').replace('=numpy', ' = numpy')
    for op in ['+', '*', '>', '<', '==']:  # too tricky, don't do: % = / -
        f1 = f1.replace(op, ' ' + op + ' ')
        f1 = f1.replace('  ' + op, ' ' + op).replace(op + '  ', op + ' ')
    f1 = f1.replace('> =', '>= ').replace(' < =', ' <= ')
    f1 = f1.replace('> >', '>> ').replace('< <', '<< ')
    f1 = f1.replace('* *', '**').replace('# !', '#!').replace('- * -', '-*-')
    f1 = f1.replace('+ =', '+= ').replace('+=  ', '+= ').replace('- =', '-= ').replace('* =', '*= ')
    f1 = f1.replace(' + + ', '++')  # bits++, mono++ etc
    
    lines = f1.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            continue
        if line.strip().endswith(';'):
            lines[i] = line.strip('; ')
        if ':' in line and not ('"' in line or "'" in line):
            lines[i] = line.replace(':', ': ').replace(': \n', ':\n').replace(':  ', ': ')
    f1 = '\n'.join(lines)
    f1 = f1.replace('\n\n\n', '\n\n')
    f1 = f1.replace('\n\n"""', '\n"""').replace('\n"""','\n\n"""', 1)
    f1 = f1.replace('\n"""', '\n"""\n').replace('\n"""\n\n', '\n"""\n')
    
    return f1


def is_var_name(name):
    return all([valid_var_re.match(n) for n in name.split('.')])


def replace_equals(f1):
    lines = f1.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            continue
        if '=' in line:
            left, right = line.split('=', 1)
            if is_var_name(left):
                lines[i] = ' = '.join([left, right])
                lines[i] = lines[i].replace('=  ', '=')
    return '\n'.join(lines)


def uk_to_us_spelling(f1):
    f1 = f1.replace('centre', 'center').replace('centerd', 'centered')
    f1 = f1.replace('nitialise', 'nitialize')
    f1 = f1.replace('colour', 'color')
    f1 = f1.replace('analyse', 'analyze')
    return f1


def split_multiline(f1):
    lines = f1.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            continue
        if 'if' in line and ':' in line and not ('"' in line or "'" in line) and not line.strip().endswith(':'):
            pre, post = line.split(':', 1)
            if post and not (post.strip().startswith('#') or ']' in line):
                pre_indent = '    '
                count = 0
                while pre.startswith(pre_indent):
                    count += 1
                    pre_indent = '    ' * count
                lines[i] = pre + ':\n' + pre_indent + post.strip()
    return '\n'.join(lines)


def demo_update_one(filename):
    """convert file contents to updated style etc
    """
    f = get_contents(filename)
    if not len(f.strip()):
        return ''  # eg __init__.py
    f = remove_doublesharp_trailing_whitespace(f)
    f = add_shebang_encoding_future(f)
    f = add_win_close_quit_demo_license(f)
    f = convert_inline_comments(f)
    f = replace_xrange(f)
    f = replace_commas_etc(f)  # do after shebang, encoding
    f = replace_PatchStim(f)
    f = replace_myWin_win(f)
    f = replace_equals(f)
    f = uk_to_us_spelling(f)
    f = split_multiline(f)
    return f


def demo_update_two(filename):
    f = get_contents(filename)
    if not len(f.strip()):
        return ''  # eg __init__.py
    f = f + '\n'
    return f


if __name__ == '__main__':
    # run from within psychopy/demos/
    dirs = [d for d in glob.glob('coder/*') if os.path.isdir(d)]
    if not dirs:
        sys.exit('in wrong directory')
    if not os.path.isdir('coder_updated'):
        os.mkdir('coder_updated')
    for d in dirs:
        if not os.path.isdir(d.replace('coder', 'coder_updated')):
            os.mkdir(d.replace('coder', 'coder_updated'))
        py = glob.glob(d + '/*.py')
        for f1 in py:
            if '__init__.py' in f1:
                continue
            new = demo_update_two(f1)
            
            #"""
            out = f1.replace('coder', 'coder_updated')
            with io.open(out, 'wb') as fh:
                fh.write(new)
            print(new)
            
            try:
                compile(new, '', 'exec')
            except Exception:
                print(out)
                raise
