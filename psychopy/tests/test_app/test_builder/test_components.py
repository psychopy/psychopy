
import sys, os
import pytest

from psychopy.app import builder
from psychopy.app.builder.components import getAllComponents

# use "python genComponsTemplate.py --out" to generate a new profile to test against
#   = analogous to a baseline image to compare screenshots
# motivation: catch deviations introduced during refactoring

# what reference to use?
profile = 'componsTemplate.txt'

# always ignore hints, labels, and categories. other options:
# should it be ok or an error if the param[field] order differs from the profile?
ignoreOrder = True

# profile is not platform specific, which can trigger false positives.
# allowedVals can differ across platforms or with prefs:
ignoreParallelOutAddresses = True

@pytest.mark.components
class TestComponents():

    @classmethod
    def setup_class(cls):
        cls.exp = builder.experiment.Experiment() # create once, not every test
        cls.here = os.path.abspath(os.path.dirname(__file__))
        cls.baselineProfile = os.path.join(cls.here, profile)

        # should not need a wx.App with fetchIcons=False
        try:
            cls.allComp = getAllComponents(fetchIcons=False)
        except:
            import wx
            if wx.version() < '2.9':
                tmpApp = wx.PySimpleApp()
            else:
                tmpApp = wx.App(False)
            try: from psychopy.app import localization
            except: pass  # not needed if can't import it
            cls.allComp = getAllComponents(fetchIcons=False)

    def setup(self):
        """This setup is done for each test individually
        """
        pass
    def teardown(self):
        pass

    def test_component_attribs(self):

        target = open(self.baselineProfile, 'rU').read()
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

        param = builder.experiment.Param('', '')  # want its namespace
        ignore = ['__doc__', '__init__', '__module__', '__str__']

        # these are for display only (cosmetic) and can end up being localized
        # so typically do not want to check during automated testing, at least
        # not when things are still new-ish and subject to change:
        ignore += ['hint',
                   'label',  # comment-out to compare labels when checking
                   'categ'
                   ]
        fields = set(dir(param)).difference(ignore)

        err = []
        for compName in sorted(self.allComp):
            comp = self.allComp[compName](parentName='x', exp=self.exp)
            order = '%s.order:%s' % (compName, eval("comp.order"))
            if not order+'\n' in target:
                tag = order.split(':',1)[0]
                try:
                    mismatch = order + ' <== ' + targetTag[tag]
                except IndexError: # missing
                    mismatch = order + ' <==> NEW (no matching param in the reference profile)'
                print mismatch.encode('utf8')
                if not ignoreOrder:
                    err.append(mismatch)
            for parName in comp.params.keys():
                # default is what you get from param.__str__, which returns its value
                default = '%s.%s.default:%s' % (compName, parName, comp.params[parName])
                lineFields = []
                for field in fields:
                    if parName == 'name' and field == 'updates':
                        continue
                        # ignore b/c never want to change the name *during a running experiment*
                        # the default name.updates varies across components: need to ignore or standardize
                    f = '%s.%s.%s:%s' % (compName, parName, field, eval("comp.params[parName].%s" % field))
                    lineFields.append(f)

                for line in [default] + lineFields:
                    if line.startswith('ParallelOutComponent.address') and ignoreParallelOutAddresses:
                        continue
                    if not line+'\n' in target:
                        # mismatch, so report on the tag from orig file
                        # match checks tag + multi-line, because line is multi-line and target is whole file
                        tag = line.split(':',1)[0]
                        try:
                            mismatch = line + ' <== ' + targetTag[tag]
                        except KeyError: # missing
                            mismatch = line + ' <==> NEW (no matching param in the reference profile)'
                        print mismatch.encode('utf8')
                        err.append(mismatch)
        assert not err
