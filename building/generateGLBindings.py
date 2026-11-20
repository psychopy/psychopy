#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Generate `psychopy/tools/opengl/_bindings.py` (and `_enumgroups.py`) from
the Khronos OpenGL registry (`building/khronos/gl.xml`).

The bindings have every OpenGL 1.0 to 4.6 function and constant, without the
removals of the core profile, plus those of the extensions in `EXTENSIONS`.
Generation fails if PsychoPy uses an OpenGL name the bindings don't have, so
add the extension it's from to `EXTENSIONS`.

To update the registry, replace `gl.xml` with a newer version and its commit in
`COMMIT`, then run this script and commit the result::

    python building/generateGLBindings.py

"""

import argparse
import re
import runpy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / 'building' / 'khronos' / 'gl.xml'
COMMIT = ROOT / 'building' / 'khronos' / 'COMMIT'
PACKAGE = ROOT / 'psychopy' / 'tools' / 'opengl'
BINDINGS = '_bindings.py'
ENUM_GROUPS = '_enumgroups.py'  # for error messages

#: Extensions to bind, besides the core API. These are the ones PsychoPy uses,
#: and those bound by `pyglet.gl` (so nothing it had is missing).
EXTENSIONS = [
    # used by PsychoPy
    'GL_APPLE_vertex_array_object',
    'GL_ARB_fragment_shader',
    'GL_ARB_geometry_shader4',
    'GL_ARB_shader_objects',
    'GL_ARB_texture_float',
    'GL_ARB_vertex_shader',
    'GL_EXT_framebuffer_blit',
    'GL_EXT_framebuffer_multisample',
    'GL_EXT_framebuffer_object',
    # bound by pyglet
    'GL_ARB_bindless_texture',
    'GL_ARB_gpu_shader_int64',
    'GL_ARB_multisample',
    'GL_EXT_texture_compression_s3tc',
    'GL_NV_mesh_shader',
]

# OpenGL names used as attributes of a module (e.g. `GL.glClear`)
_ATTRIBUTE_NAME = re.compile(r'\b(?:GL|gl|pygletgl)\.(gl[A-Z]\w*|GL_\w+)\b')
# OpenGL names imported from PsychoPy's OpenGL modules
_IMPORT_FROM = re.compile(
    r'from\s+psychopy\.tools\.(?:pygletgl|opengl)\s+import\s+'
    r'(\([^)]*\)|[^\n]*)')
_NAME = re.compile(r'\b(gl[A-Z]\w*|GL_\w+)\b')


def findUsedNames(root):
    """Find the OpenGL function and constant names PsychoPy uses.

    Parameters
    ----------
    root : Path
        Directory to search the Python files in.

    Returns
    -------
    set of str
        Names (e.g. `'glClear'`, `'GL_TEXTURE_2D'`).

    """
    names = set()
    for path in root.rglob('*.py'):
        if PACKAGE in path.parents:
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        # leave out commented out code
        text = '\n'.join(
            line for line in text.splitlines()
            if not line.lstrip().startswith('#'))
        names.update(_ATTRIBUTE_NAME.findall(text))
        for imported in _IMPORT_FROM.findall(text):
            names.update(_NAME.findall(imported))

    return names


def _parseParam(elem):
    """`(ptype, pointer depth)` of a command's `<param>` or `<proto>`."""
    ptype = elem.find('ptype')
    text = ''.join(elem.itertext())
    name = elem.find('name').text
    if '[' in text:
        raise ValueError(f'unsupported array declaration: {text!r}')
    declaration = text[:text.rindex(name)]

    return (ptype.text if ptype is not None else 'void',
            declaration.count('*'))


def _paramGroups(cmd):
    """Groups of the enumerant and bitmask arguments of a command (e.g.
    `{0: 'EnableCap'}` for `glEnable`), used to name their values in error
    messages. Enumerants without a group are `''`, so any name is used."""
    groups = {}
    for i, param in enumerate(cmd.findall('param')):
        ptype, depth = _parseParam(param)
        if depth:
            continue
        if ptype == 'GLenum':
            groups[i] = param.get('group', '')
        elif ptype in ('GLbitfield', 'GLint') and param.get('group'):
            # e.g. `internalformat` of `glTexImage2D()` is a `GLint`
            groups[i] = param.get('group')

    return groups


def _ctype(ptype, depth):
    """Python expression for the `ctypes` type of a parameter, following the
    conventions of `pyglet.gl` so the same values can be passed."""
    if ptype == 'void':
        # pointers to void of any depth are `void *`, as in pyglet
        return 'POINTER(GLvoid)' if depth else 'None'

    expr = ptype
    for _ in range(depth):
        expr = f'POINTER({expr})'

    return expr


def _requirements(parent, api='gl'):
    """`(commands, enums)` required by a `<feature>` or `<extension>`."""
    commands, enums = [], []
    for require in parent.findall('require'):
        if require.get('api', api) != api:
            continue
        commands += [e.get('name') for e in require.findall('command')]
        enums += [e.get('name') for e in require.findall('enum')]

    return commands, enums


def _header(title, commit):
    """Lines at the start of a generated module."""
    return [
        '# -*- coding: utf-8 -*-',
        '',
        f'"""{title}',
        '',
        'Generated by `building/generateGLBindings.py` from the Khronos OpenGL',
        'registry (KhronosGroup/OpenGL-Registry, commit',
        f'{commit}). Do not edit.',
        '',
        '"""',
        '',
    ]


def generate(registry, commit):
    """Generate the source of `_bindings.py` and `_enumgroups.py`.

    Parameters
    ----------
    registry : Path
        Path to `gl.xml`.
    commit : str
        Commit of the OpenGL registry repository `gl.xml` is from.

    Returns
    -------
    tuple
        Sources of `_bindings.py` and `_enumgroups.py` (`str`), and the names
        the bindings define (`set` of `str`).

    """
    root = ET.parse(registry).getroot()

    enumValues = {}
    enumGroups = {}  # names of the enumerants in each group
    for enum in root.iterfind('enums/enum'):
        if enum.get('api', 'gl') == 'gl':
            enumValues[enum.get('name')] = enum.get('value')
            for group in filter(None, enum.get('group', '').split(',')):
                enumGroups.setdefault(group, []).append(enum.get('name'))
    commandElems = {
        cmd.find('proto/name').text: cmd
        for cmd in root.iterfind('commands/command')}

    # what each name requires, from the first feature or extension it's in
    required = {}
    for feature in root.iterfind('feature'):
        if feature.get('api') != 'gl':
            continue
        commands, enums = _requirements(feature)
        for name in commands + enums:
            required.setdefault(name, f"OpenGL {feature.get('number')}")

    extensions = {ext.get('name'): ext for ext in root.iterfind(
        'extensions/extension')}
    for extName in EXTENSIONS:
        ext = extensions[extName]
        if 'gl' not in ext.get('supported').split('|'):
            raise ValueError(f'{extName} is not an OpenGL extension')
        commands, enums = _requirements(ext)
        for name in commands + enums:
            required.setdefault(name, extName)

    typeNames = set(runpy.run_path(str(PACKAGE / '_types.py'))['__all__'])

    lines = _header('OpenGL functions and constants.', commit) + [
        'from ctypes import POINTER',
        '',
        'from ._lib import link as _link',
        'from ._types import *',
        '',
        '# constants',
    ]
    names = set()
    for name in sorted(n for n in required if n in enumValues):
        value = enumValues[name]
        int(value, 0)  # check it's an integer literal
        lines.append(f'{name} = {value}')
        names.add(name)

    lines += ['', '# functions']
    usedGroups = set()  # groups of function arguments
    bitmaskGroups = set()
    for name in sorted(n for n in required if n in commandElems):
        cmd = commandElems[name]
        types = [_parseParam(cmd.find('proto'))]
        types += [_parseParam(param) for param in cmd.findall('param')]
        for ptype, _ in types:
            if ptype != 'void' and ptype not in typeNames:
                raise ValueError(f'{name} uses unknown type {ptype}')
        restype = _ctype(*types[0])
        argtypes = ', '.join(_ctype(*t) for t in types[1:])
        groups = _paramGroups(cmd)
        usedGroups.update(groups.values())
        bitmaskGroups.update(
            groups[i] for i, (ptype, _) in enumerate(types[1:])
            if i in groups and ptype == 'GLbitfield')
        groupsArg = f', {groups!r}' if groups else ''
        lines.append(
            f"{name} = _link('{name}', {restype}, [{argtypes}], "
            f"'{required[name]}'{groupsArg})")
        names.add(name)

    lines += [
        '',
        "__all__ = [_name for _name in dict(globals())",
        "           if _name.startswith(('gl', 'GL_'))]",
        '',
    ]

    # names of the constants in each group used by an argument
    groupLines = _header(
        'Groups of OpenGL constants, for naming argument values in error '
        'messages.', commit)
    groupLines.append('GROUPS = {')
    for group in sorted(usedGroups - {''}):
        members = sorted(n for n in enumGroups.get(group, ()) if n in names)
        if not members:
            continue
        groupLines.append(f'    {group!r}: (')
        groupLines += [f'        {n!r},' for n in members]
        groupLines.append('    ),')
    groupLines += [
        '}',
        '',
        '# groups of bit flags, whose values are combined with `|`',
        'BITMASKS = frozenset({',
    ]
    groupLines += [f'    {g!r},' for g in sorted(bitmaskGroups)]
    groupLines += ['})', '']

    return '\n'.join(lines), '\n'.join(groupLines), names


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument(
        '--output-dir', type=Path, default=PACKAGE,
        help='directory to write the modules to (default: %(default)s)')
    parser.add_argument(
        '--no-check', action='store_true',
        help="don't check that PsychoPy only uses names in the bindings")
    args = parser.parse_args(argv)

    bindings, groups, names = generate(REGISTRY, COMMIT.read_text().strip())

    if not args.no_check:
        missing = findUsedNames(ROOT / 'psychopy') - names
        if missing:
            sys.exit(
                'PsychoPy uses OpenGL names that are not in the bindings (add '
                'the extensions they are from to EXTENSIONS):\n  ' +
                '\n  '.join(sorted(missing)))

    for fileName, source in [(BINDINGS, bindings), (ENUM_GROUPS, groups)]:
        (args.output_dir / fileName).write_text(
            source, encoding='utf-8', newline='\n')
    print(f'Wrote {len(names)} names to {args.output_dir}')


if __name__ == '__main__':
    main()
