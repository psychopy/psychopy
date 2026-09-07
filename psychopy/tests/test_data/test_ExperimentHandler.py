# -*- coding: utf-8 -*-

from packaging.version import Version
import pandas as pd
import pytest
from psychopy import data, logging
import numpy as np
import os, glob, shutil
import re
from tempfile import mkdtemp
from pathlib import Path
from datetime import datetime
from psychopy.tools.filetools import openOutputFile

logging.console.setLevel(logging.DEBUG)


class TestExperimentHandler():
    def setup_class(self):
        self.tmpDir = mkdtemp(prefix='psychopy-tests-testExp')
        self.random_seed = 100

    def teardown_class(self):
        shutil.rmtree(self.tmpDir)
        # for a while (until 1.74.00) files were being left in the tests folder by mistake
        for f in glob.glob('testExp*.psyexp'):
            os.remove(f)
        for f in glob.glob('testExp*.csv'):
            os.remove(f)

    def test_default(self):
        exp = data.ExperimentHandler(
            name='testExp',
            version='0.1',
            extraInfo={'participant': 'jwp', 'ori': 45},
            runtimeInfo=None,
            originPath=None,
            savePickle=True,
            saveWideText=True,
            dataFileName=self.tmpDir + 'default'
        )

        # First loop: Training.
        conds = data.createFactorialTrialList(
            {'faceExpression': ['happy', 'sad'], 'presTime': [0.2, 0.3]}
        )
        training = data.TrialHandler(
            trialList=conds, nReps=3, name='train',
            method='random',
            seed=self.random_seed)
        exp.addLoop(training)

        rng = np.random.RandomState(seed=self.random_seed)

        for trial in training:
            training.addData('training.rt', rng.rand() * 0.5 + 0.5)
            if rng.rand() > 0.5:
                training.addData('training.key', 'left')
            else:
                training.addData('training.key', 'right')
            exp.nextEntry()

        # Then run 3 repeats of a staircase.
        outerLoop = data.TrialHandler(
            trialList=[], nReps=3,name='stairBlock', method='random'
        )
        exp.addLoop(outerLoop)

        for thisRep in outerLoop:  # The outer loop doesn't save any data.
            staircase = data.StairHandler(
                startVal=10, name='staircase', nTrials=5
            )
            exp.addLoop(staircase)

            for thisTrial in staircase:
                id = rng.rand()
                if rng.rand() > 0.5:
                    staircase.addData(1)
                else:
                    staircase.addData(0)
                exp.addData('id', id)
                exp.nextEntry()

    def test_comparison_equals(self):
        e1 = data.ExperimentHandler()
        e2 = data.ExperimentHandler()
        assert e1 == e2

    def test_comparison_not_equal(self):
        e1 = data.ExperimentHandler()
        e2 = data.ExperimentHandler(name='foo')
        assert e1 != e2

    def test_comparison_equals_with_same_TrialHandler_attached(self):
        e1 = data.ExperimentHandler()
        e2 = data.ExperimentHandler()
        t = data.TrialHandler([dict(foo=1)], 2)

        e1.addLoop(t)
        e2.addLoop(t)

        assert e1 == e2


class TestDataSave():
    def setup_class(self):
        # create temp folder
        self.tmp = Path(
            mkdtemp(prefix='psychopy-tests-TestDataSave')
        )

    def teardown_class(self):
        # remove temp folder
        shutil.rmtree(self.tmp)

    def setup_method(self):
        # create a new experiment
        self.exp = data.ExperimentHandler(
            name='TestDataSave',
            savePickle=False,
            saveWideText=False
        )

    def save_csv(self, encoding="utf-8-sig"):
        """
        Save to a temporary CSV file

        Parameters
        ----------
        encoding : str
            File encoding to use when saving
        
        Returns
        ----------
        pathlib.Path
            Path to the temp file
        """
        # generate a random filename
        file = self.tmp / f"{datetime.now().strftime('%Y_%m_%d-%H_%M_%S-%f')}.csv"
        # write csv to a temp file
        self.exp.saveAsWideText(file, delim=',', encoding=encoding)

        return file
    
    def compare_csv(self, exemplar, encoding="utf-8-sig"):
        """
        Compare the csv output of the current experiment against a string

        Parameters
        ----------
        exemplar : str or re.Pattern
            String to compare against (e.g. "thisComp.started,thisComp.stopped\n0.0,1.0"). Can be a 
            simple string or a re.Pattern object (to do regex comparison)
        encoding : str
            File encoding to use when saving/loading
        """
        # save csv
        file = self.save_csv(encoding=encoding)
        # get data file contents:
        contents = file.read_text(encoding=encoding)
        # compare to exemplar 
        if isinstance(exemplar, re.Pattern):
            match = exemplar.match(contents)
        else:
            match = exemplar == contents
        # assert true
        assert match, (
            f"Data file {file} does not match expected values:\n"
            f"{contents}\n"
            f"{exemplar}"
        )

    def test_save_unicode(self):
        """
        Check that a variety of unicode characters can be saved
        """
        # try with different encodings...
        for encoding in ['utf-8', 'utf-16']:
            # try each unicode character...
            for asDecimal in range(143859):
                try:
                    chr(asDecimal).encode(encoding)
                except UnicodeEncodeError:
                    # skip if not a valid unicode
                    continue
                # add to experiment
                self.exp.addData("char", chr(asDecimal))
                self.exp.nextEntry()
            # try to save
            self.save_csv(encoding=encoding)

    def test_save_unicode_conditions(self):
        """
        Check that a variety of unicode characters can appear in the conditions file and be saved
        """
        # try with different encodings...
        for encoding in ['utf-8', 'utf-16']:
            # define conditions with unicode chars in
            conds = [
                {'id': "01", 'name': u"umlauts-öäü"},
                {'id': "02", 'name': u"accents-àáâă"}
            ]
            # construct trial handler from these conds
            trials = data.TrialHandler(
                trialList=conds, nReps=1, method='sequential'
            )
            # add trial handler to experiment
            self.exp.addLoop(trials)
            # run through trial handler
            for trial in trials:
                pass
            # try to save
            self.save_csv(encoding=encoding)

    def test_mutable_values(self):
        """
        Test that mutable values (e.g. a list) can be saved
        """
        # create some mutable elements
        mut_list = [1]
        mut_dict = {'a': 1}
        # add their initial values
        self.exp.addData("mut_list", mut_list)
        self.exp.addData("mut_dict", mut_dict)
        self.exp.nextEntry()
        # mutate them
        mut_list[0] = 9999
        mut_dict['a'] = 9999
        # add their new values
        self.exp.addData("mut_list", mut_list)
        self.exp.addData("mut_dict", mut_dict)
        self.exp.nextEntry()
        # check that csv looks as expected
        self.compare_csv((
            "thisRow.t,notes,mut_list,mut_dict\n"
            ",,[1],{'a': 1}\n"
            ",,[9999],{'a': 9999}\n"
        ))

    def test_escape_quotes(self):
        """
        Test that quotation marks are escaped using Excel standard (" => "")
        """
        # don't run this test with older versions of pandas as it didn't used to handle escaping
        if Version(pd.__version__) < Version("3.0.0"):
            pytest.skip()
        # define some values with quotes in
        cases = {
            'single_quote': {
                'original': "Some 'single quoted' text",
                'saved': "Some 'single quoted' text"
            },
            'double_quote': {
                'original': "Some \"double quoted\" text",
                'saved': "\"Some \"\"double quoted\"\" text\""
            },
            'single_curly': {
                'original': "Some ‘single curly quoted’ text",
                'saved': "Some ‘single curly quoted’ text"
            },
            'double_curly': {
                'original': "Some “double curly quoted” text",
                'saved': "Some “double curly quoted” text"
            },
            'single_escaped': {
                'original': "Some \\\'escaped single quoted\\\' text",
                'saved': "Some \\\'escaped single quoted\\\' text"
            },
            'double_escaped': {
                'original': "Some \\\"escaped double quoted\\\" text",
                'saved': "\"Some \\\"\"escaped double quoted\\\"\" text\""
            },
        }
        # add to exp
        for key, case in cases.items():
            self.exp.addData(key, case['original'])
        # construct exemplar
        exemplar = (
            f"thisRow.t,notes,{','.join(cases.keys())}\n"
            f",,{','.join([case['saved'] for case in cases.values()])}\n"
        )
        # compare
        self.compare_csv(exemplar)


if __name__ == '__main__':
    import pytest
    pytest.main()
