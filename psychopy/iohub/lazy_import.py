# Copyright (C) 2006-2010 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# NB This file comes unaltered (apart from this sentence) from the bzrlib
# by Canonical (the library supporting the Bazaar code versioning system)

"""Functionality to create lazy evaluation objects.

This includes waiting to import a module until it is actually used.

Most commonly, the 'lazy_import' function is used to import other modules
in an on-demand fashion. Typically use looks like::

    from bzrlib.lazy_import import lazy_import
    lazy_import(globals(), '''
    from bzrlib import (
        errors,
        osutils,
        branch,
        )
    import bzrlib.branch
    ''')

Then 'errors, osutils, branch' and 'bzrlib' will exist as lazy-loaded
objects which will be replaced with a real object on first use.

In general, it is best to only load modules in this way. This is because
it isn't safe to pass these variables to other functions before they
have been replaced. This is especially true for constants, sometimes
true for classes or functions (when used as a factory, or you want
to inherit from them).

"""

from __future__ import absolute_import


class BzrError(Exception):
    """Base class for errors raised by bzrlib.

    :cvar internal_error: if True this was probably caused by a bzr bug and
        should be displayed with a traceback; if False (or absent) this was
        probably a user or environment error and they don't need the gory
        details.  (That can be overridden by -Derror on the command line.)

    :cvar _fmt: Format string to display the error; this is expanded
        by the instance's dict.

    """

    internal_error = False

    def __init__(self, msg=None, **kwds):
        """Construct a new BzrError.

        There are two alternative forms for constructing these objects.
        Either a preformatted string may be passed, or a set of named
        arguments can be given.  The first is for generic "user" errors which
        are not intended to be caught and so do not need a specific subclass.
        The second case is for use with subclasses that provide a _fmt format
        string to print the arguments.

        Keyword arguments are taken as parameters to the error, which can
        be inserted into the format string template.  It's recommended
        that subclasses override the __init__ method to require specific
        parameters.

        :param msg: If given, this is the literal complete text for the error,
           not subject to expansion. 'msg' is used instead of 'message' because
           python evolved and, in 2.6, forbids the use of 'message'.

        """
        Exception.__init__(self)
        if msg is not None:
            # I was going to deprecate this, but it actually turns out to be
            # quite handy - mbp 20061103.
            self._preformatted_string = msg
        else:
            self._preformatted_string = None
            for key, value in kwds.items():
                setattr(self, key, value)

    def _format(self):
        s = getattr(self, '_preformatted_string', None)
        if s is not None:
            # contains a preformatted message
            return s
        try:
            fmt = self._get_format_string()
            if fmt:
                d = dict(self.__dict__)
                s = fmt % d
                # __str__() should always return a 'str' object
                # never a 'unicode' object.
                return s
        except Exception as e:
            pass  # just bind to 'e' for formatting below
        else:
            e = None
        return 'Unprintable exception %s: dict=%r, fmt=%r, error=%r' \
            % (self.__class__.__name__,
               self.__dict__,
               getattr(self, '_fmt', None),
               e)

    def __unicode__(self):
        u = self._format()
        if isinstance(u, bytes):
            # Try decoding the str using the default encoding.
            u = unicode(u)
        elif not isinstance(u, unicode):
            # Try to make a unicode object from it, because __unicode__ must
            # return a unicode object.
            u = u'{}'.format(u)
        return u

    def __str__(self):
        s = self._format()
        if isinstance(s, unicode):
            s = s.encode('utf8')
        else:
            # __str__ must return a str.
            s = str(s)
        return s

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))

    def _get_format_string(self):
        """Return format string for this exception or None."""
        fmt = getattr(self, '_fmt', None)
        if fmt is not None:
            #from bzrlib.i18n import gettext
            def gettext(t):
                return t
            return gettext(unicode(fmt))  # _fmt strings should be ascii

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__dict__ == other.__dict__


class InternalBzrError(BzrError):
    """Base class for errors that are internal in nature.

    This is a convenience class for errors that are internal. The
    internal_error attribute can still be altered in subclasses, if
    needed. Using this class is simply an easy way to get internal
    errors.

    """

    internal_error = True


class IllegalUseOfScopeReplacer(InternalBzrError):

    _fmt = ('ScopeReplacer object %(name)r was used incorrectly:'
            ' %(msg)s%(extra)s')

    def __init__(self, name, msg, extra=None):
        BzrError.__init__(self)
        self.name = name
        self.msg = msg
        if extra:
            self.extra = ': ' + str(extra)
        else:
            self.extra = ''


class InvalidImportLine(InternalBzrError):

    _fmt = 'Not a valid import statement: %(msg)\n%(text)s'

    def __init__(self, text, msg):
        BzrError.__init__(self)
        self.text = text
        self.msg = msg


class ImportNameCollision(InternalBzrError):

    _fmt = ('Tried to import an object to the same name as'
            ' an existing object. %(name)s')

    def __init__(self, name):
        BzrError.__init__(self)
        self.name = name


class ScopeReplacer(object):
    """A lazy object that will replace itself in the appropriate scope.

    This object sits, ready to create the real object the first time it
    is needed.

    """

    __slots__ = ('_scope', '_factory', '_name', '_real_obj')

    # If you to do x = y, setting this to False will disallow access to
    # members from the second variable (i.e. x). This should normally
    # be enabled for reasons of thread safety and documentation, but
    # will be disabled during the selftest command to check for abuse.
    _should_proxy = True

    def __init__(self, scope, factory, name):
        """Create a temporary object in the specified scope. Once used, a real
        object will be placed in the scope.

        :param scope: The scope the object should appear in
        :param factory: A callable that will create the real object.
            It will be passed (self, scope, name)
        :param name: The variable name in the given scope.

        """
        object.__setattr__(self, '_scope', scope)
        object.__setattr__(self, '_factory', factory)
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_real_obj', None)
        scope[name] = self

    def _resolve(self):
        """Return the real object for which this is a placeholder."""
        name = object.__getattribute__(self, '_name')
        real_obj = object.__getattribute__(self, '_real_obj')
        if real_obj is None:
            # No obj generated previously, so generate from factory and scope.
            factory = object.__getattribute__(self, '_factory')
            scope = object.__getattribute__(self, '_scope')
            obj = factory(self, scope, name)
            if obj is self:
                raise IllegalUseOfScopeReplacer(
                    name, msg='Object tried'
                    " to replace itself, check it's not using its own scope.")

            # Check if another thread has jumped in while obj was generated.
            real_obj = object.__getattribute__(self, '_real_obj')
            if real_obj is None:
                # Still no preexisting obj, so go ahead and assign to scope and
                # return. There is still a small window here where races will
                # not be detected, but safest to avoid additional locking.
                object.__setattr__(self, '_real_obj', obj)
                scope[name] = obj
                return obj

        # Raise if proxying is disabled as obj has already been generated.
        if not ScopeReplacer._should_proxy:
            raise IllegalUseOfScopeReplacer(
                name, msg='Object already replaced, did you assign it'
                          ' to another variable?')
        return real_obj

    def __getattribute__(self, attr):
        obj = object.__getattribute__(self, '_resolve')()
        return getattr(obj, attr)

    def __setattr__(self, attr, value):
        obj = object.__getattribute__(self, '_resolve')()
        return setattr(obj, attr, value)

    def __call__(self, *args, **kwargs):
        obj = object.__getattribute__(self, '_resolve')()
        return obj(*args, **kwargs)


def disallow_proxying():
    """Disallow lazily imported modules to be used as proxies.

    Calling this function might cause problems with concurrent imports
    in multithreaded environments, but will help detecting wasteful
    indirection, so it should be called when executing unit tests.

    Only lazy imports that happen after this call are affected.

    """
    ScopeReplacer._should_proxy = False


class ImportReplacer(ScopeReplacer):
    """This is designed to replace only a portion of an import list.

    It will replace itself with a module, and then make children
    entries also ImportReplacer objects.

    At present, this only supports 'import foo.bar.baz' syntax.

    """

    # '_import_replacer_children' is intentionally a long semi-unique name
    # that won't likely exist elsewhere. This allows us to detect an
    # ImportReplacer object by using
    #       object.__getattribute__(obj, '_import_replacer_children')
    # We can't just use 'isinstance(obj, ImportReplacer)', because that
    # accesses .__class__, which goes through __getattribute__, and triggers
    # the replacement.
    __slots__ = ('_import_replacer_children', '_member', '_module_path')

    def __init__(self, scope, name, module_path, member=None, children={}):
        """Upon request import 'module_path' as the name 'module_name'. When
        imported, prepare children to also be imported.

        :param scope: The scope that objects should be imported into.
            Typically this is globals()
        :param name: The variable name. Often this is the same as the
            module_path. 'bzrlib'
        :param module_path: A list for the fully specified module path
            ['bzrlib', 'foo', 'bar']
        :param member: The member inside the module to import, often this is
            None, indicating the module is being imported.
        :param children: Children entries to be imported later.
            This should be a map of children specifications.
            ::

                {'foo':(['bzrlib', 'foo'], None,
                    {'bar':(['bzrlib', 'foo', 'bar'], None {})})
                }

        Examples::

            import foo => name='foo' module_path='foo',
                          member=None, children={}
            import foo.bar => name='foo' module_path='foo', member=None,
                              children={'bar':(['foo', 'bar'], None, {}}
            from foo import bar => name='bar' module_path='foo', member='bar'
                                   children={}
            from foo import bar, baz would get translated into 2 import
            requests. On for 'name=bar' and one for 'name=baz'

        """
        if (member is not None) and children:
            raise ValueError('Cannot supply both a member and children')

        object.__setattr__(self, '_import_replacer_children', children)
        object.__setattr__(self, '_member', member)
        object.__setattr__(self, '_module_path', module_path)

        # Indirecting through __class__ so that children can
        # override _import (especially our instrumented version)
        cls = object.__getattribute__(self, '__class__')
        ScopeReplacer.__init__(self, scope=scope, name=name,
                               factory=cls._import)

    def _import(self, scope, name):
        children = object.__getattribute__(self, '_import_replacer_children')
        member = object.__getattribute__(self, '_member')
        module_path = object.__getattribute__(self, '_module_path')
        module_python_path = '.'.join(module_path)
        if member is not None:
            module = __import__(
                module_python_path,
                scope,
                scope,
                [member],
                level=0)
            return getattr(module, member)
        else:
            module = __import__(module_python_path, scope, scope, [], level=0)
            for path in module_path[1:]:
                module = getattr(module, path)

        # Prepare the children to be imported
        for child_name, (child_path, child_member, grandchildren) in \
                children.items():
            # Using self.__class__, so that children get children classes
            # instantiated. (This helps with instrumented tests)
            cls = object.__getattribute__(self, '__class__')
            cls(module.__dict__, name=child_name,
                module_path=child_path, member=child_member,
                children=grandchildren)
        return module


class ImportProcessor(object):
    """Convert text that users input into lazy import requests."""

    # TODO: jam 20060912 This class is probably not strict enough about
    #       what type of text it allows. For example, you can do:
    #       import (foo, bar), which is not allowed by python.
    #       For now, it should be supporting a superset of python import
    #       syntax which is all we really care about.

    __slots__ = ['imports', '_lazy_import_class']

    def __init__(self, lazy_import_class=None):
        self.imports = {}
        if lazy_import_class is None:
            self._lazy_import_class = ImportReplacer
        else:
            self._lazy_import_class = lazy_import_class

    def lazy_import(self, scope, text):
        """Convert the given text into a bunch of lazy import objects.

        This takes a text string, which should be similar to normal
        python import markup.

        """
        self._build_map(text)
        self._convert_imports(scope)

    def _convert_imports(self, scope):
        # Now convert the map into a set of imports
        for name, info in self.imports.items():
            self._lazy_import_class(scope, name=name, module_path=info[0],
                                    member=info[1], children=info[2])

    def _build_map(self, text):
        """Take a string describing imports, and build up the internal map."""
        for line in self._canonicalize_import_text(text):
            if line.startswith('import '):
                self._convert_import_str(line)
            elif line.startswith('from '):
                self._convert_from_str(line)
            else:
                raise InvalidImportLine(
                    line, "doesn't start with 'import ' or 'from '")

    def _convert_import_str(self, import_str):
        """This converts a import string into an import map.

        This only understands 'import foo, foo.bar, foo.bar.baz as bing'

        :param import_str: The import string to process

        """
        if not import_str.startswith('import '):
            raise ValueError('bad import string %r' % (import_str,))
        import_str = import_str[len('import '):]

        for path in import_str.split(','):
            path = path.strip()
            if not path:
                continue
            as_hunks = path.split(' as ')
            if len(as_hunks) == 2:
                # We have 'as' so this is a different style of import
                # 'import foo.bar.baz as bing' creates a local variable
                # named 'bing' which points to 'foo.bar.baz'
                name = as_hunks[1].strip()
                module_path = as_hunks[0].strip().split('.')
                if name in self.imports:
                    raise ImportNameCollision(name)
                # No children available in 'import foo as bar'
                self.imports[name] = (module_path, None, {})
            else:
                # Now we need to handle
                module_path = path.split('.')
                name = module_path[0]
                if name not in self.imports:
                    # This is a new import that we haven't seen before
                    module_def = ([name], None, {})
                    self.imports[name] = module_def
                else:
                    module_def = self.imports[name]

                cur_path = [name]
                cur = module_def[2]
                for child in module_path[1:]:
                    cur_path.append(child)
                    if child in cur:
                        cur = cur[child][2]
                    else:
                        next = (cur_path[:], None, {})
                        cur[child] = next
                        cur = next[2]

    def _convert_from_str(self, from_str):
        """This converts a 'from foo import bar' string into an import map.

        :param from_str: The import string to process

        """
        if not from_str.startswith('from '):
            raise ValueError('bad from/import %r' % from_str)
        from_str = from_str[len('from '):]

        from_module, import_list = from_str.split(' import ')

        from_module_path = from_module.split('.')

        for path in import_list.split(','):
            path = path.strip()
            if not path:
                continue
            as_hunks = path.split(' as ')
            if len(as_hunks) == 2:
                # We have 'as' so this is a different style of import
                # 'import foo.bar.baz as bing' creates a local variable
                # named 'bing' which points to 'foo.bar.baz'
                name = as_hunks[1].strip()
                module = as_hunks[0].strip()
            else:
                name = module = path
            if name in self.imports:
                raise ImportNameCollision(name)
            self.imports[name] = (from_module_path, module, {})

    def _canonicalize_import_text(self, text):
        """Take a list of imports, and split it into regularized form.

        This is meant to take regular import text, and convert it to the
        forms that the rest of the converters prefer.

        """
        out = []
        cur = None
        continuing = False

        for line in text.split('\n'):
            line = line.strip()
            loc = line.find('#')
            if loc != -1:
                line = line[:loc].strip()

            if not line:
                continue
            if cur is not None:
                if line.endswith(')'):
                    out.append(cur + ' ' + line[:-1])
                    cur = None
                else:
                    cur += ' ' + line
            else:
                if '(' in line and ')' not in line:
                    cur = line.replace('(', '')
                else:
                    out.append(line.replace('(', '').replace(')', ''))
        if cur is not None:
            raise InvalidImportLine(cur, 'Unmatched parenthesis')
        return out


def lazy_import(scope, text, lazy_import_class=None):
    """Create lazy imports for all of the imports in text.

    This is typically used as something like::

        from bzrlib.lazy_import import lazy_import
        lazy_import(globals(), '''
        from bzrlib import (
            foo,
            bar,
            baz,
            )
        import bzrlib.branch
        import bzrlib.transport
        ''')

    Then 'foo, bar, baz' and 'bzrlib' will exist as lazy-loaded
    objects which will be replaced with a real object on first use.

    In general, it is best to only load modules in this way. This is
    because other objects (functions/classes/variables) are frequently
    used without accessing a member, which means we cannot tell they
    have been used.

    """
    # This is just a helper around ImportProcessor.lazy_import
    proc = ImportProcessor(lazy_import_class=lazy_import_class)
    return proc.lazy_import(scope, text)


# The only module that this module depends on is 'bzrlib.errors'. But it
# can actually be imported lazily, since we only need it if there is a
# problem.

lazy_import(globals(), """
from bzrlib import errors
""")
