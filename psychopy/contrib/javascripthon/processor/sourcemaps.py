# -*- coding: utf-8 -*-
# Copyright (c) Waldemar Kornewald, Alberto Berti
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of the copyright holder nor the names of its
#        contributors may be used to endorse or promote products
#        derived from this software without specific prior written
#        permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from base64 import b64encode
from bisect import bisect_right
from collections import namedtuple
import json
import re


# A single base 64 digit can contain 6 bits of data. For the base 64
# variable length quantities we use in the source map spec, the first
# bit is the sign, the next four bits are the actual value, and the
# 6th bit is the continuation bit. The continuation bit tells us
# whether there are more digits in this value following this digit.
#
#   Continuation
#   |    Sign
#   |    |
#   V    V
#   101011
VLQ_BASE_SHIFT = 5

# binary: 100000
VLQ_BASE = 1 << VLQ_BASE_SHIFT

# binary: 011111
VLQ_BASE_MASK = VLQ_BASE - 1

# binary: 100000
VLQ_CONTINUATION_BIT = VLQ_BASE

BASE64_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
BASE64_CHAR_TO_INT = dict(map(reversed, enumerate(BASE64_CHARS)))


class SourceMapDecodeError(ValueError):
    pass


def decode_vlqs(segment):
    """
    Decode a string of VLQ-encoded data.

    Returns:
      a list of integers.
    """

    values = []

    vlq = shift = 0
    for c in segment:
        val = BASE64_CHAR_TO_INT[c]
        cont = val & VLQ_CONTINUATION_BIT
        # Each character is 6 bits:
        # 5 of value and the high bit is the continuation.
        val &= VLQ_BASE_MASK
        vlq += val << shift
        shift += VLQ_BASE_SHIFT

        if not cont:
            # The low bit of the unpacked value is the sign.
            vlq, sign = vlq >> 1, vlq & 1
            if sign:
                vlq = -vlq
            values.append(vlq)
            vlq = shift = 0

    if vlq or shift:
        raise SourceMapDecodeError('leftover vlq/shift in vlq decode')

    return values


def encode_vlq(num):
    """Encode a single number in VLQ format"""
    vlq = (-num << 1) + 1 if num < 0 else num << 1
    result = ''
    while not result or vlq > 0:
        digit = vlq & VLQ_BASE_MASK
        vlq >>= VLQ_BASE_SHIFT
        if vlq > 0:
            digit |= VLQ_CONTINUATION_BIT
        result += BASE64_CHARS[digit]
    return result


source_map_url_re = re.compile(
    r'/[\*/][#@]\s*sourceMappingURL=([^\s*]+)\s*(?:\*/)?')


def discover(source):
    source = source.splitlines()
    # Source maps are only going to exist at either the top or bottom
    # of the document.  Technically, there isn't anything indicating
    # *where* it should exist, so we are generous and assume it's
    # somewhere either in the first or last 5 lines.  If it's
    # somewhere else in the document, you're probably doing it wrong.
    if len(source) > 10:
        possibilities = source[:5] + source[-5:]
    else:
        possibilities = source

    for line in set(possibilities):
        result = source_map_url_re.findall(line)
        if result:
            return result[0]
    return None


def strip(content):
    return source_map_url_re.sub('', content)


# namedtuples have a nice repr and they support comparison (useful for
# bisect search)
class Token(namedtuple('TokenBase', 'dst_line dst_col src src_line src_col '
                       'name mapping')):
    __slots__ = ()

    def __new__(cls, dst_line=0, dst_col=0, src='', src_line=0, src_col=0,
                name=None, mapping=None):
        return super(Token, cls).__new__(cls, dst_line, dst_col,
                                         src, src_line, src_col, name, mapping)


def shift_tokens(tokens, dst_line=0, dst_col=0, src_line=0, src_col=0):
    return [t._replace(dst_line=t.dst_line + dst_line,
                       dst_col=t.dst_col + dst_col,
                       src_line=t.src_line + src_line,
                       src_col=t.src_col + src_col)
            for t in tokens]


TOKEN_SPEC = (
    ('LINECOMMENT', r'//'),
    ('COMMENTSTART', r'/\*'),
    ('COMMENTEND', r'\*/'),
    ('DELIM',   r'[{}\[\]();]'),
)
token_re = re.compile('|'.join('(?P<%s>%s)' % pair for pair in TOKEN_SPEC),
                      re.UNICODE | re.MULTILINE | re.DOTALL)


def identity_tokenize(content, src):
    in_comment = False
    for line_num, line in enumerate(content.splitlines()):
        if line.strip():
            start_column = len(line) - len(line.lstrip())
            if start_column:
                yield Token(line_num, 0, src, line_num, 0)
            yield Token(line_num, start_column, src, line_num, start_column)
        for match in token_re.finditer(line):
            kind = match.lastgroup
            value = match.group(kind)
            if in_comment:
                if kind == 'COMMENTEND' and in_comment:
                    in_comment = False
            elif kind == 'COMMENTSTART':
                in_comment = True
            elif kind == 'LINECOMMENT':
                break
            elif kind == 'DELIM':
                column = match.start()
                if column > start_column:
                    yield Token(line_num, column, src, line_num, column)


def identity_map(content, src):
    return SourceMap(identity_tokenize(content, src), {src: content})


class SourceMap:
    def __init__(self, tokens=(), sources_content=None, raw=None,
                 ignore_errors=False):
        self.tokens = []
        if sources_content is None:
            self.sources_content = {}
        else:
            self.sources_content = sources_content.copy()
        self.raw = {} if raw is None else raw.copy()
        self.ignore_errors = ignore_errors
        map(self.add_token, tokens)

    def add_token(self, token):
        if not self.tokens or token[:2] > self.tokens[-1][:2]:
            self.tokens.append(token)
        else:
            index = bisect_right(self.tokens, token)
            if not self.ignore_errors and index and \
                    self.tokens[index - 1][:2] == token[:2]:
                raise ValueError(
                    'Token with given dst_line and dst_col already exists:\n'
                    'Existing: {}\nAdded: {}'.format(self.tokens[index - 1],
                                                     token))
            self.tokens.insert(index, token)

    @classmethod
    def decode(cls, source, ignore_errors=True):
        """Decode string or dict back into a sourcemap."""
        if isinstance(source, dict):
            smap = source
        else:
            # According to the spec a source map may be prepended with
            # ")]}'" to cause a JavaScript error. In that case ignore the
            # entire first line.
            if source[:4] == ")]}'":
                source = source.split('\n', 1)[1]
            smap = json.loads(source)

        sources = smap['sources']
        names = list(map(str, smap['names']))
        lines = smap['mappings'].split(';')

        source_root = smap.get('source_root')
        if source_root is not None:
            sources = ['/'.join((source_root, s)) for s in sources]

        tokens = []

        dst_col = src_id = src_line = src_col = name_id = 0
        for dst_line, line in enumerate(lines):
            dst_col = 0
            for segment in line.split(','):
                if not segment:
                    continue
                fields = decode_vlqs(segment)
                dst_col += fields[0]
                if dst_col < 0:
                    raise SourceMapDecodeError(
                        'Segment {} has negative dst_col'.format(segment, fields))

                src = None
                name = None
                if len(fields) not in (1, 4, 5):
                    raise SourceMapDecodeError(
                        'Invalid segment {}, parsed as {}'.format(segment, fields))
                if len(fields) > 1:
                    src_id += fields[1]
                    if not 0 <= src_id < len(sources):
                        raise SourceMapDecodeError(
                            'Segment {} references source {} which '
                            'does not exist'.format(
                                segment, src_id))
                    src = sources[src_id]
                    src_line += fields[2]
                    if src_line < 0:
                        raise SourceMapDecodeError(
                            'Segment {} has negative src_line'.format(segment))
                    src_col += fields[3]
                    if src_col < 0:
                        raise SourceMapDecodeError(
                            'Segment {} has negative src_col'.format(segment))

                if len(fields) > 4:
                    name_id += fields[4]
                    if not 0 <= name_id < len(names):
                        raise SourceMapDecodeError(
                            'Segment {} references name {} which '
                            'does not exist'.format(
                                segment, name_id))
                    name = names[name_id]

                tokens.append(Token(dst_line, dst_col, src, src_line, src_col,
                                    name))

        sources_content = {src: content
                           for src, content in zip(
                                   sources, smap.get('sourcesContent',
                                                     (None,) * len(sources)))
                           if content is not None}
        return cls(tokens, sources_content, raw=smap,
                         ignore_errors=ignore_errors)

    def encode(self):
        """Encode the given sourcemap object into a mapping that contains all
        the fields wanted by the sourcemaps *spec*.

        :return: a dictionary containing the encoded sourcemap fields
        :rtype: dict
        """
        sources = {}
        prev_src_id = next_src_id = 0
        prev_src_line = prev_src_col = 0
        names = {}
        prev_name_id = next_name_id = 0
        mappings = []
        prev_dst_line = -1
        for token in self.tokens:
            while prev_dst_line < token.dst_line:
                prev_dst_line += 1
                prev_dst_col = 0
                segments = []
                mappings.append(segments)
            vlq = [token.dst_col - prev_dst_col]
            prev_dst_col = token.dst_col
            if token.src:
                source_id = sources.get(token.src)
                if source_id is None:
                    sources[token.src] = source_id = next_src_id
                    next_src_id += 1
                vlq.append(source_id - prev_src_id)
                vlq.append(token.src_line - prev_src_line)
                vlq.append(token.src_col - prev_src_col)
                if token.name:
                    name_id = names.get(token.name)
                    if name_id is None:
                        names[token.name] = name_id = next_name_id
                        next_name_id += 1
                    vlq.append(name_id - prev_name_id)
                    prev_name_id = name_id
                prev_src_id = source_id
                prev_src_line = token.src_line
                prev_src_col = token.src_col
            segments.append(''.join(map(encode_vlq, vlq)))
        data = {'version': 3,
                'mappings': ';'.join(map(','.join, mappings)),
                'sources': sorted(sources, key=lambda x: sources[x]),
                'names': sorted(names, key=lambda x: names[x])}
        data['sourcesContent'] = list(map(self.sources_content.get,
                                          data['sources']))
        return data

    def stringify(self, inline_comment=False):
        """Encode a SourceMap and return a string of its JSON dump, optionally
        encoding it with base64.

        :param sourcemap: the sourcemap
        :type sourcemap: class:`~.SourceMap`
        :param bool inline_comment: set it to ``True`` if the sourcemap is
          intended to be added as a comment in the source body
        :return: a string containing the encoded sourcemap fields
        :rtype: str
        """
        data = json.dumps(self.encode())
        if inline_comment:
            data = ('\n//# sourceMappingURL=data:text/json;base64,%s\n' %
                    b64encode(data.encode('utf-8')).decode('ascii'))
        return data
