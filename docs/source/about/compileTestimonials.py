from __future__ import print_function
from builtins import next
import csv, codecs
from psychopy import gui

filename = gui.fileOpenDlg('.', allowed='*.csv')[0]
        
#use csv from python (not from numpy) due to handling newlines within quote char
with open(filename, 'rU') as csvFile:
    spamreader = csv.reader(csvFile, delimiter=',', quotechar='"', dialect=csv.excel)
    headers = next(spamreader)
    print('headers:', type(headers), headers)
    entries=[]
    for thisRow in spamreader:
        print(thisRow)
        thisEntry = {}
        for fieldN, thisFieldName in enumerate(headers):
            thisEntry[thisFieldName] = thisRow[fieldN]
        entries.append(thisEntry)

companHead="Your Company or Institution"
nameHead='Your name (or anon, but a name is nicer)'
testimHead='Your thoughts on PsychoPy'
posnHead = 'Your position'


with open('testimonialsText.html', 'wb') as outFile:
    for thisEntry in entries:
        outFile.write('    <hr>%s <p>\n' %(thisEntry[testimHead].replace('\n', '<br>')))
        nameStr = '    - <em>%s' %thisEntry[nameHead]
        if thisEntry[posnHead]:
            nameStr += ', %s' %thisEntry[posnHead]
        if thisEntry[companHead]:
            nameStr += ', %s' %thisEntry[companHead]
        nameStr += ' </em><br>\n'
        outFile.write(nameStr)

