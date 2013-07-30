import wx
#create wx event/object IDs
exit=wx.NewId()
#edit menu
cut=wx.NewId()
copy=wx.NewId()
paste=wx.NewId()
showFind=wx.NewId()
findNext=wx.NewId()
comment=wx.NewId()
unComment=wx.NewId()
foldAll=wx.NewId()
unfoldAll=wx.NewId()
dedent=wx.NewId()
indent=wx.NewId()
smartIndent=wx.NewId()

#experiment menu
newRoutine=wx.NewId()
addRoutineToFlow=wx.NewId()
addLoopToFlow=wx.NewId()
remRoutineFromFlow=wx.NewId()
remLoopFromFlow=wx.NewId()
copyRoutine=wx.NewId()
pasteRoutine=wx.NewId()

#view menu
openCoderView = wx.NewId()
openBuilderView = wx.NewId()
openShell = wx.NewId()
openIPythonNotebook = wx.NewId()
toggleReadme = wx.NewId()
toggleOutput=wx.NewId()
toggleSourceAsst=wx.NewId()
toggleIndentGuides=wx.NewId()
toggleWhitespace=wx.NewId()
toggleEOLs=wx.NewId()

#tools menu
analyzeNow=wx.NewId()
analyzeAuto=wx.NewId()
openMonCentre=wx.NewId()
compileScript=wx.NewId()
runFile=wx.NewId()
stopFile=wx.NewId()
monitorCenter=wx.NewId()
openUpdater=wx.NewId()
unitTests=wx.NewId()
benchmarkWizard=wx.NewId()
filePrint=wx.NewId()

#help menu
#these should be assigned to the relevant buttons/menu items in the app
#AND for those with weblinks the relevant URL should be provided at top of psychopyApp.py
about=wx.NewId()
license=wx.NewId()
coderTutorial=wx.NewId()
builderHelp=wx.NewId()
psychopyHome=wx.NewId()
psychopyReference=wx.NewId()
builderDemosUnpack=wx.NewId()
builderDemos=wx.NewId()
#help pages (from help buttons)
docsPrefsDlg=wx.NewId()

#toolbar IDs
tbFileNew=10
tbFileOpen=20
tbFileSave=30
tbFileSaveAs=40
tbUndo= 70
tbRedo= 80
tbRun = 100
tbStop = 110
tbCompile=120
tbPreferences=130#for the app
tbExpSettings=140#for the experiment
tbMonitorCenter=150
tbColorPicker=160

tbIncrFlowSize=170
tbDecrFlowSize=171
tbIncrRoutineSize=180
tbDecrRoutineSize=181
