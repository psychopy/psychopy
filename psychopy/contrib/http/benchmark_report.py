#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Go from multiple flat raw data files (.pkl) to html page, save .cache.pkl

This script lives on http://upload.psychopy.org to handle new benchmark data files.
New uploads are detected (using inotify) and this script is run, with its output
being visible at http://upload.psychopy.org/benchmark/report.html

Future enhancements:
- v0.2 report on multiple target data columns (same tag-set, different d_col)
- v0.3 support multiple tag-sets per run -- need multiple caches

Author Jeremy Gray
"""
from __future__ import print_function
# from future import standard_library
# standard_library.install_aliases()
from builtins import zip
from builtins import str
from builtins import range
import sys, os, time, glob
import pickle as pickle
import numpy as np

# global file and path names, etc:
if sys.platform == 'darwin':  # for testing & dev
    base = 'benchmark'
    outfile = 'bmreport.html'
else:  # deploy on linux
    base = '/usr/local/psychopy_org/benchmark'
    outfile = '/var/www/html/benchmark/report.html'
cache = os.path.join(base, '.cache.pkl')
rebuild = False
cached_files = []
cachedNames = []
hash_sep = ' || '  # internal usage, should not be present in any tag

# --rebuild if you change the items of interest:
tags = ['platform', 'openGL version', 'internet access']  # categorical
datacols = ['best_dots_square']  # numeric; currently can support only 1 datacol
items = tags + datacols  # currently data column must be last
projectStem = 'bmark'  # needs to match up.php's project stem

def parse(file):
    """unpickle file[1], append contents selectively to file, as float() if possible"""
    # file is a list of [date, filename as path/project-IP-rand-date]
    # add IP and upload time, extract from filename
    IP = file[1].split('-')[1]
    if sys.platform == 'darwin':
        print(IP, file[1])
    file.append(IP)
    f = open(file[1], 'r')
    data = pickle.load(f)
    f.close()
    for field in items:
        try:
            d = data[field]  # or KeyError
            try:
                d = float(d.strip('ms/frame').strip('ms').strip('s').strip())
                # can't do d.split()[0] because, eg, '2.1  NVIDIA-8.0.61'
            except ValueError:
                pass # most are not float
            file.append(d)
        except KeyError:
            file.append('---')
def readCache():
    if os.path.exists(cache):
        f = open(cache, 'r')
        info = pickle.load(f)
        f.close()
    else:
        info = []
    return info
def writeCache(info):
    f = open(cache, 'w+b')
    pickle.dump(info, f)
    f.close()
def writeHtml(f, table_lines):
    # lines = (category, value, note)
    f.write('<a href="http://www.psychopy.org"></a>')
    f.write('<h2><font color=blue>PsychoPy benchmarks</font></h2>')
    f.write('''<font color=gray>Data were contributed anonymously by people who ran
        the PsychoPy "Benchmark wizard" and agreed to share their data (see Builder, Tools menu).</font>''')
        
    f.write('<table cellspacing=8 border=0>')
    f.write('<tr><td>')
    itemsCap = ['<strong>'+i[0].capitalize()+i[1:]+'</strong>' for i in items]
    f.write('</td><td>'.join(itemsCap)+' *</td></tr>')
    
    for tag, val, note in table_lines:
        if sys.platform == 'darwin':
            print(tag, val, note)
        f.write('<tr>')
        f.write('<td><center>' + tag.replace(hash_sep, '</td><td><center>') + '</td>')
        f.write("<td><center><strong><datum title='%s'>" % note + val + "</datum></strong></center></td>")
        f.write('</tr>\n')
    f.write('</table>')
    f.write('''<font color=gray size=-1><p> &nbsp; &nbsp; <em>* Hover the mouse
            over a value for descriptive statistics, if available.</em></font></p><br>''')
    f.write('''<hr><font color=gray><p><strong>Methodology</strong>:<li>Every upload 
        contributes one data point.</li>
        <li>Averages are automatically recomputed for each new upload (within 1
        second or so). (You may need to refresh the page in your browser to see the new values.)</li>
        <li> The next version of the script will display multiple data columns
        (e.g., Best_dots_square, Best_dots_circle, sound latency, microphone latency, ...).</li>
        </font>''')

def squash(tags, datacols, data):
    """data reduction within cells defined by a collection of tags"""
    
    # this is a hack - refactor:
    tags = tags + datacols
    lines = []
    
    noIP = True  # suppress IP address as a tag even if its in tags (as first item in list)
    tcols = list(range(3, len(tags)+2))
    d_col = -1 # data column is last, currently; want to select columns by tag; need header row in data?
    
    # init dictionaries here, later link by common keys
    values = {}
    count = {}
    
    for field in data:
        # hash-keys define categories / cells
        hash = hash_sep.join([str(field[t]) for t in tcols])
        hash = hash[0].capitalize()+hash[1:]
        if hash not in values:
            values[hash] = []
            count[hash] = 0
        values[hash].append(field[d_col])
        count[hash] += 1
    sortedKeys = list(values.keys())
    sortedKeys.sort()
    
    # data reduction & descriptive stats within-cell:
    for key in sortedKeys:
        numKeys = count[key]
        if numKeys == 0:
            # this should never happen ...
            val = note = '(no data)'
        elif numKeys == 1 and type(values[key][0]) == float:
            precision = max(0, 3 - round(np.log10(values[key][0])))
            fmt = "%%.%if" % precision
            val = fmt % float(values[key][0])
            note = '(only one data point)'
        else: 
            # any trailing units should have been removed in parse()
            v = [v for v in values[key] if type(v) == float]
            #v = filter(lambda x: type(x) == float, values[key])
            if not len(v):
                val = '(non-numeric)'
                note = "all values were filtered, n=%d, e.g., %s" % (numKeys, values[key][0])
            else:
                v = np.array(v)
                avg = np.average(v)
                precision = max(0, 3 - round(np.log10(avg)))
                fmt = "%%.%if" % precision
                val = fmt % avg
                note = "mean, n=%d, " % len(v)
                if numKeys != len(v):
                    note += 'filtered %i, ' % (numKeys - len(v))
                fmt = "SD %%.%if, min %%.%if, max %%.%if" % (precision, precision, precision)
                note +=  fmt % (np.std(v), np.min(v), np.max(v))
        lines.append((key, val, note))
        
    return lines

def main():
    """read files / cache, reduce the data, format as html"""
    t0 = t1 = time.time()

    # Retrieve files, cache & parse any new files:
    rebuild = '--rebuild' in sys.argv
    if rebuild or not os.path.exists(cache):
        rebuild = True
        cached_files = []
        cachedNames = []
        try:
            os.unlink(cache)
        except Exception:
            pass
    else:
        cached_files = readCache()
        cachedNames = zip(*cached_files)[1]  # = get full file names from [1]

    dirglob = glob.glob(os.path.join(base, projectStem + '*'))
    if set(cachedNames).difference(dirglob):
        # cache no longer reflects file system (missing files), so rebuild
        rebuild = True
        cached_files = []
        cachedNames = []
        try:
            os.unlink(cache)
        except Exception:
            pass
    files = [[file[-17:], file] for file in dirglob]
    hasNew = False  # new == based on same name, not time-stamp etc
    for file_info in files:
        if file_info[1] not in cachedNames:
            parse(file_info)  # appends desired tag-fields to file
            cached_files.append(file_info)
            hasNew = True
    if hasNew:
        writeCache(cached_files)
    t2 = time.time()

    # Data reduction:
    reduced = squash(tags, datacols, cached_files)
    t3 = time.time()

    # Format html page:
    f = open(outfile, 'w+')
    writeHtml(f, reduced)
    f.write('<hr><em><font color=white>')
    if rebuild:
        f.write('cache rebuild; ')
    t4 = time.time()
    fmt = 'processed %i data files in %.3fs, %.0f%% parsing files</em>'
    f.write(fmt % (len(files), (t4 - t0), 100 * (t2 - t1) / (t4 - t0)) )
    f.close()
    
    return t4 - t0

if __name__ == '__main__':
    script_time = main()
    if sys.platform == 'darwin':
        print("%.3fs " % script_time)
