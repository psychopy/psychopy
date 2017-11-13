#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function
##-----------------------------
##Windows post install (shortcuts etc...)
##-----------------------------
import sys, glob
def install():
    import os
    try:
        print("Adding shortcuts to >>Start>Programs>PsychoPy")
        progsFolder= get_special_folder_path("CSIDL_COMMON_PROGRAMS")
        sitePackages = os.path.join(sys.prefix , 'lib','site-packages')
        demosFolder = os.path.join(sys.prefix , 'lib','site-packages', 'psychopy', 'demos')
        
        #Psychopy Programs folder
        psychopyShortcuts = os.path.join(progsFolder, 'PsychoPy')
        if not os.path.isdir(psychopyShortcuts):
            os.mkdir(psychopyShortcuts)
            directory_created(psychopyShortcuts)
             
        #PsychoStation center
        PsychoIDELink= os.path.join(psychopyShortcuts, "PsychoPy IDE.lnk")
        if os.path.isfile(PsychoIDELink):    
            os.remove(PsychoIDELink)#we want to make a new one
        psychoIDEloc = os.path.join(sitePackages,'psychopyIDE', "PsychoPyIDE.py")
        pythonLoc = os.path.join(sys.prefix, 'pythonw.exe')
        if os.path.isfile(PsychoIDELink):    
            os.remove(PsychoIDELink)#we want to make a new one
        create_shortcut('"'+pythonLoc+'"',  #target
                        'PsychoPy IDE',   #description
                        PsychoIDELink,  #filename
                        '"' + psychoIDEloc + '"', #args
                        '', #working directory (blank)  os.path.join(sitePackages,'psychopy','PsychoCentral'),
                        os.path.join(sitePackages,'psychopyIDE','psychopy.ico'))    
        file_created(PsychoIDELink)
        
        #monitor center
        #monitorCenterLink= "c://python24//python.exe" + os.path.join(psychopyShortcuts, "MonitorCenter.lnk")
        #if os.path.isfile(monitorCenterLink):    
            #os.remove(monitorCenterLink)#we want to make a new one
        #create_shortcut(os.path.join(sitePackages,'monitors', "MonitorCenter.py"),
                        #'PsychoPy Monitor Center', monitorCenterLink,
                        #'',#args
                        #os.path.join(sitePackages,'monitors'),
                        #os.path.join(sitePackages,'monitors','psychopy.ico'))
        #file_created(monitorCenterLink)
        
        #homepage
        homePageLink = os.path.join(psychopyShortcuts, "PsychoPyHome.lnk")
        if os.path.isfile(homePageLink):    
            os.remove(homePageLink)#we want to make a new one
        create_shortcut(r"http://www.psychopy.org",
                            'PsychoPy HomePage', homePageLink)
        file_created(homePageLink)
        
        print("All done. Enjoy!")
        
        #remove outdated demo files
        oldDemos = glob.glob(demosFolder+"//demo_*")
        for file in oldDemos:
            os.remove(file)
        
    except:
        print("failed to install shortcuts")
        exc = sys.exc_info()
        print(exc[0],exc[1])
    
    print("")
    print("""TOP TIP: It's a good idea to add PsychoPyIDE to your handlers for *.py files.
    To do that, open a windows explorer window, go to >Tools>FoldersOptions>FileTypes.
    Find .py file type, click 'Advanced' and add the command:
        "C:\Python25\pythonw.exe" "C:\Python25\Lib\site-packages\PsychoPyIDE\PsychoPyIDE.py" "%1"
    Now you can right-click files and open them in PsychoPy, ready-to-run :-)
    """)
if len(sys.argv) > 1:
    if sys.argv[1] == '-install':
        install()
    else:
        print("Script was called with option %s" % sys.argv[1])
