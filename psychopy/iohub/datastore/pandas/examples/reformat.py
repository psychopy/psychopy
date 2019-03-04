# -*- coding: utf-8 -*-
"""
Created on Fri Nov 01 09:32:29 2013

@author: Sol
"""
from __future__ import print_function

from psychopy.iohub.datastore.pandas import ioHubPandasDataView

file_name = 'io_stroop.hdf5'
event_type = 'all'
output_format = 'xls'

exp_data = ioHubPandasDataView(file_name)

outputformat2pandaswrite = {
    'csv': 'to_csv',
    'xls': 'to_excel',
    'html': 'to_html'}

out_name = file_name + '.' + output_format
sep_index = file_name.rfind(u'.')
if sep_index >= 0:
    out_name = file_name[:sep_index] + '.' + output_format

print('Saving %s to %s....' % (file_name, out_name))
getattr(exp_data.all_events, outputformat2pandaswrite[output_format])(out_name)
print('Conversion complete.')


exp_data.close()
