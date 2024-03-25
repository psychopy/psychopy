from psychopy.gui import Dlg, util


class BaseDlgTest:
    def base_setup_method(self):
        self.basicDict = {
            'participant': "OST",
            'session': 0,
            'consent*': False,
            'cond|cfg': ["red", "blue"],
            'date|hid': "2024-03-25T10:00:35"
        }

    def test_title(self):
        cases = [
            "Experiment",
            "实验",  # non-ascii characters
            "ٱلْحَمْدُ لِلَّهِ",  # arabic harkaat

        ]
        for case in cases:
            dlg = Dlg.fromDict(self.basicDict, title=case, show=False)
            assert dlg.windowTitle() == case
            del dlg

    def test_copy_dict(self):
        cases = [
            True,
            False
        ]
        for case in cases:
            dictionary = self.basicDict.copy()
            dlg = Dlg.fromDict(dictionary, copyDict=case, show=False)
            assert (dictionary is dlg.dictionary )!= case

    def test_get_dict(self):
        cases = [
            True,
            False
        ]
        for case in cases:
            inDict = self.basicDict.copy()
            dlg = Dlg.fromDict(inDict, copyDict=True, show=False)
            outDict = dlg.getDict(removeTags=case)
            for field in self.basicDict:
                # if removing tags, remove them for this check too
                if case:
                    key, flags = util.parsePipeSyntax(field)
                else:
                    key = field
                # make sure value is the same
                assert (
                    outDict[key] == inDict[field]
                    or outDict[key] in inDict[field]
                ), (
                    f"Different value for {key} ({outDict[key]}) in retrieved dictionary than "
                    f"for {field} ({inDict[field]}) in initial dictionary"
                )