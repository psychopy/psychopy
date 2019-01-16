from __future__ import print_function
import sys
import os
import io

from pkg_resources import parse_version
import wx

if parse_version(wx.__version__) < parse_version('2.9'):
    tmpApp = wx.PySimpleApp()
else:
    tmpApp = wx.App(False)
from psychopy import experiment
from psychopy import constants
from psychopy.experiment.components import getAllComponents

# usage: generate or compare all Component.param settings & options

# motivation: catch deviations introduced during refactoring

# use --out to re-generate componsTemplate.txt

# ignore attributes that are there because inherit from object
ignoreObjectAttribs = True

# should not need a wx.App with fetchIcons=False
try:
    allComp = getAllComponents(fetchIcons=False)
except Exception:
    import wx
    if parse_version(wx.__version__) < parse_version('2.9'):
        tmpApp = wx.PySimpleApp()
    else:
        tmpApp = wx.App(False)
    try:
        from psychopy.app import localization
    except Exception:
        pass  # not needed if can't import it
    allComp = getAllComponents(fetchIcons=False)

exp = experiment.Experiment()
relPath = os.path.join(os.path.split(__file__)[0], 'componsTemplate.txt')

if not '--out' in sys.argv:
    with io.open(relPath, 'r', encoding='utf-8-sig') as f:
        target = f.read()

    targetLines = target.splitlines()
    targetTag = {}
    for line in targetLines:
        try:
            t, val = line.split(':',1)
            targetTag[t] = val
        except ValueError:
            # need more than one value to unpack; this is a weak way to
            # handle multi-line default values, eg TextComponent.text.default
            targetTag[t] += '\n' + line  # previous t value
else:
    outfile = open(relPath,'w')

param = experiment.Param('', '')  # want its namespace
ignore = ['__doc__', '__init__', '__module__', '__str__', 'next']
if '--out' not in sys.argv:
    # these are for display only (cosmetic) but no harm in gathering initially:
    ignore += ['hint',
               'label',  # comment-out to not ignore labels when checking
               'categ'
               ]
for field in dir(param):
    if field.startswith("__"):
        ignore.append(field)
fields = set(dir(param)).difference(ignore)

mismatches = []
for compName in sorted(allComp):
    comp = allComp[compName](parentName='x', exp=exp)

    order = '%s.order:%s' % (compName, eval("comp.order"))
    out = [order]
    if '--out' in sys.argv:
        outfile.write(order+'\n')
    elif not order+'\n' in target:
        tag = order.split(':', 1)[0]
        try:
            err = order + ' <== ' + targetTag[tag]
        except IndexError:  # missing
            err = order + ' <==> NEW (no matching param in original)'
        print(err)
        mismatches.append(err)
    for parName in sorted(comp.params):
        # default is what you get from param.__str__, which returns its value
        if not constants.PY3:
            if isinstance(comp.params[parName].val, unicode):
                comp.params[parName].val = comp.params[parName].val.encode('utf8')
        default = '%s.%s.default:%s' % (compName, parName, comp.params[parName])
        out.append(default)
        lineFields = []
        for field in sorted(fields):
            if parName == 'name' and field == 'updates':
                continue
                # ignore: never want to change the name *during an experiment*
                # the default name.updates value varies across components
            f = '%s.%s.%s:%s' % (compName, parName, field,
                                 eval("comp.params[parName].%s" % field))
            lineFields.append(f)

        for line in [default] + lineFields:
            if '--out' in sys.argv:
                if not ignoreObjectAttribs:
                    outfile.write(line+'\n')
                else:
                    if (not ":<built-in method __" in line and
                            not ":<method-wrapper '__" in line):
                        outfile.write(line+'\n')
            elif not line+'\n' in target:
                # mismatch, so report on the tag from orig file
                # match checks tag + multi-line
                # because line is multi-line and target is whole file
                tag = line.split(':', 1)[0]
                try:
                    err = line + ' <== ' + targetTag[tag]
                except KeyError:  # missing
                    err = line + ' <==> NEW (no matching param in original)'
                print(err)
                mismatches.append(err)

# return mismatches

