#!/usr/bin/env python2

"""Scoring script for MSU-PsychoPy version of IAT task.

Authors: Jeremy R. Gray & Nate Pasmanter, 2013
"""

from __future__ import division
import pandas as pd
import glob, os, sys

def scoreIAT(csvfile, write_file=False):
    """Input = csv file; output = D score (or explanation why data are bad).

    Expects column headers of the form Response_#.corr, and Response_#.rt,
    where # is 1-7, for IAT block number.

    Scoring is mostly per GNB 2003:
      Greenwald, A. G., Nosek, B. A., & Banaji, M. R. (2003). Understanding and
      using the implicit association test: I. An improved scoring algorithm.
      Journal of Personality and Social Psychology, 85, 197-216.
    Following Amodio, incorrect responses do not contribute to RT; there's no
    RT penalty for this reason. For computing SDs, unbiased SD is used (N-1).

    If write_file=True, will save score to a file 'Scored_' + csvfile.

    A positive D value from this script indicates a bias in favor of
    "creative bad / practical good". I.e., if RT in blocks with creative+good is
    longer than RT in blocks with creative+bad, people are more conflicted or
    hesitant about creative+good.
    The way the task is set up, when side == 1, creative and bad are paired first.
    If side == -1, the opposite is true. This pairing is handled by the scoring
    script.
    """
    # ------------ Thresholds for excluding trials or subjects: ------------
    rt_FAST = 0.300
    rt_FASTms = int(1000 * rt_FAST)  # 300ms
    rt_SLOW = 10.
    correct = 1
    incorrect = 0
    # GNB 2003 thesholds for why subject should be excluded:
    warn = u''
    threshold = {'ac_prac_blk': 0.50,
                 'ac_prac_all': 0.60, 'rt_prac_all': 0.35,
                 'ac_task_blk': 0.60, 'rt_task_blk': 0.25,
                 'ac_task_all': 0.70, 'rt_task_all': 0.10 }

    # ------------ Read dataframe (df) from .csv file and parse: ------------
    df = pd.read_csv(csvfile)

    # accuracy; mean --> proportion correct
    prac_ac = [df.loc[:, 'Response_1.corr'].dropna(),
               df.loc[:, 'Response_2.corr'].dropna(),
               df.loc[:, 'Response_5.corr'].dropna()]
    task_ac = [df.loc[:, 'Response_3.corr'].dropna(),
               df.loc[:, 'Response_4.corr'].dropna(),
               df.loc[:, 'Response_6.corr'].dropna(),
               df.loc[:, 'Response_7.corr'].dropna()]
    # response time in seconds
    prac_rt = [df.loc[:, 'Response_1.rt'].dropna(),
               df.loc[:, 'Response_2.rt'].dropna(),
               df.loc[:, 'Response_5.rt'].dropna()]
    task_rt = [df.loc[:, 'Response_3.rt'].dropna(),
               df.loc[:, 'Response_4.rt'].dropna(),
               df.loc[:, 'Response_6.rt'].dropna(),
               df.loc[:, 'Response_7.rt'].dropna()]

    assert len(task_ac[0]) == len(task_ac[2]) == len(task_rt[0])  # block 3, 6
    assert len(task_ac[1]) == len(task_ac[3]) == len(task_rt[1])  # block 4, 7
    assert len(task_rt[0]) == len(task_rt[2]) > 1  # require 2+ items in 3, 6
    assert len(task_rt[1]) == len(task_rt[3]) > 1  # equire 2+ items in 4, 7
    assert all([all(task_ac[i].isin([correct, incorrect])) for i in range(4)])
    assert all([all(task_rt[i] > 0) for i in range(4)])  # require positive RTs

    # counterbalanced IAT screen side: +1 or -1; used in calc of D
    side = df.loc[0, 'side']
    assert side in [-1, 1]

    # ------------ Check participant exclusion thresholds ------------
    # check proportion-too-fast in each task block:
    for i, rt in enumerate(task_rt):
        prop_too_fast = len(rt[(rt < rt_FAST)]) / len(rt)
        if prop_too_fast > threshold['rt_task_blk']:
            pct = 100 * prop_too_fast
            warn += "%.0f%% trials with RT < %dms in task block #%d\n" % (
                pct, rt_FASTms, (3, 4, 6, 7)[i])

    # check proportion-too-fast all task trials:
    rt = task_rt[0].append(task_rt[1]).append(task_rt[2]).append(task_rt[3])
    prop_too_fast = len(rt[(rt < rt_FAST)]) / len(rt)
    if prop_too_fast > threshold['rt_task_all']:
        pct = 100 * prop_too_fast
        warn += "%.0f%% trials with RT < %dms across all task blocks\n" % (
            pct, rt_FASTms)

    # check proportion-too-fast in each practice block:
    for i, rt in enumerate(prac_rt):
        prop_too_fast = len(rt[(rt < rt_FAST)]) / len(rt)
        if prop_too_fast > threshold['rt_prac_all']:
            pct = 100 * prop_too_fast
            warn += "%.0f%% trials with RT < %dms in practice block #%d\n" % (
                pct, rt_FASTms, (1, 2, 5)[i])

    # check proportion-error in each practice block:
    for i, prac_blk in enumerate(prac_ac):
        if prac_blk.mean() < threshold['ac_prac_blk']:
            pct = 100 * (1 - prac_blk.mean())
            warn += "%.0f%% errors in practice block #%d\n" %(pct, (1, 2, 5)[i])

    # check proportion-error in all practice trials:
    ac = prac_ac[0].append(prac_ac[1]).append(prac_ac[2]).mean()
    if ac < threshold['ac_prac_all']:
        pct = 100 * (1 - ac.mean())
        warn += "%.0f%% errors across all practice blocks\n" % pct

    # check proportion-error in task blocks:
    for i, ac in enumerate(task_ac):
        if ac.mean() < threshold['ac_task_blk']:
            pct = 100 * (1 - ac.mean())
            warn += "%.0f%% errors in task block #%d\n" % (pct, (3, 4, 6, 7)[i])

    # check proportion-error across all task trials:
    ac = task_ac[0].append(task_ac[1]).append(task_ac[2]).append(task_ac[3])
    if ac.mean() < threshold['ac_task_all']:
        pct = 100 * (1 - ac.mean())
        warn += "%.0f%% errors across all task trials\n" % pct

    # ------------ Filter out bad trials: ------------
    for i, block in enumerate(task_ac):
        # retain trials with correct responses:
        correct_trials = (block == correct)
        task_rt[i] = task_rt[i][correct_trials]
        #task_ac[i] = task_ac[i][correct_trials]
    for i, block in enumerate(task_rt):
        # retain trials where RT is not too fast or too slow:
        rt_ok_trials = (block >= rt_FAST) & (block <= rt_SLOW)
        task_rt[i] = task_rt[i][rt_ok_trials]
        #task_ac[i] = task_ac[i][rt_ok_trials]

    # ------------ Calculate summary stats of the filtered data: ----------
    mean3, mean4, mean6, mean7 = [a.mean() for a in task_rt]
    stdev36 = task_rt[0].append(task_rt[2]).std() # pooled std of blocks 3 & 6
    stdev47 = task_rt[1].append(task_rt[3]).std() # pooled std of blocks 4 & 7
    d36 = side * (mean6 - mean3) / stdev36  # side is +1 or -1
    d47 = side * (mean7 - mean4) / stdev47
    D_IAT = (d36 + d47) / 2

    stats = D_IAT, side, mean3, mean4, mean6, mean7, stdev36, stdev47, warn.strip() or 'None'
    labels = 'D_IAT', 'side', 'mean3', 'mean4', 'mean6', 'mean7', 'sd36', 'sd47', 'warnings'
    if write_file:
        df = pd.DataFrame([stats], columns=labels)
        df.to_csv('Scored_' + csvfile, index=False, index_label=False, encoding='utf-8')

    return warn.strip() or D_IAT

def batchScoreIAT(path='.', write_file=False):
    """Call scoreIAT() on all csv files in path
    """
    files = glob.glob(os.path.join(path, '*.csv'))
    for f in files:
        scoreIAT(f, write_file=write_file)

if __name__ == '__main__':
    for f in sys.argv[1:]:
        print(f, scoreIAT(f))
