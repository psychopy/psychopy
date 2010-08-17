;NSIS Modern User Interface

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"
  !include "EnvVarUpdate.nsh"
  !include "fileassoc.nsh"
  !define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
  !define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

;--------------------------------
;General

  ;Name and file
  Name "PsychoPy2"
  !Define Version "1.62.00"
  OutFile "StandalonePsychoPy-${Version}-win32.exe"
  InstallDir "$PROGRAMFILES\PsychoPy2"
  
  ;Request application privileges for Windows Vista
  RequestExecutionLevel admin

;--------------------------------
;Variables

  Var StartMenuFolder

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING
  !define MUI_HEADERIMAGE

;--------------------------------
;Pages
  !insertmacro MUI_PAGE_LICENSE "psychopy\LICENSE.txt"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  
  ;Start Menu Folder Page Configuration
  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM" 
  !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\PsychoPy Standalone" 
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "PsychoPy Standalone"
  !define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\PsychoPy2"

  !insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
  
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  
;--------------------------
;if previous version installed then remove
Function .onInit
  
  ReadRegStr $R0 HKLM \
  "Software\Microsoft\Windows\CurrentVersion\Uninstall\PsychoPy2" \
  "UninstallString"
  StrCmp $R0 "" done
 
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
  "A version of PsychoPy2 is already installed. $\n$\nClick `OK` to remove the \
  previous version or `Cancel` to cancel this upgrade." \
  IDOK uninst
  Abort
  
;Run the uninstaller
uninst:
  ClearErrors
  Exec $INSTDIR\uninst.exe ; instead of the ExecWait line
done: 
FunctionEnd

;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"
  
;--------------------------------
;Installer Sections

Section "PsychoPy2" PsychoPy2

  SetShellVarContext all
  
  SetOutPath "$INSTDIR"
  Var /GLOBAL AppDir
  StrCpy $AppDir "$INSTDIR\Lib\site-packages\PsychoPy-${Version}-py2.5.egg\psychopy\app"
  
  ${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$INSTDIR"
  
  ;ADD YOUR OWN FILES HERE...
  file /r "C:\python25\*.*"
  file /r "windlls\*.dll"
    
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    
    ;Create shortcuts
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\PsychoPy2.lnk" \
      "$INSTDIR\pythonw.exe" "$\"$AppDir\psychopyApp.py$\"" "$AppDir\Resources\psychopy.ico"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Website.lnk" "http://www.psychopy.org"
    Delete "$SMPROGRAMS\$StartMenuFolder\PsychoPy reference.lnk" 
    Delete "$SMPROGRAMS\$StartMenuFolder\PsychoPy tutorials.lnk" 
  
  !insertmacro MUI_STARTMENU_WRITE_END
  
  ;associate .psydat files
  !insertmacro APP_ASSOCIATE "psyexp" "PsychoPy.experiment" "PsychoPy Experiment" "$AppDir\Resources\psychopy.ico,0" \
     "Open with PsychoPy" "$\"$INSTDIR\python.exe$\" $\"$AppDir\psychopyApp.py$\" $\"%1$\""
     

  ;add to path variable
  ${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$INSTDIR"
  
SectionEnd

Section "avbin" avbin
  SetOverwrite off
  File "c:\WINDOWS\system32\avbin.dll"
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${PsychoPy2} "PsychoPy files, including python"
  !insertmacro MUI_DESCRIPTION_TEXT ${avbin} "avbin is required for playing movies, but need only be installed once"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

;--------------------------------
;Uninstaller Section

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  ;Store installation folder
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayName" "PsychoPy2 (Standalone)"  
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayVersion" "${Version}"   
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayIcon" "$AppDir\Resources\psychopy.ico"
  WriteRegStr HKLM "${REG_UNINSTALL}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
  
  WriteRegStr HKLM "${REG_UNINSTALL}" "URLInfoAbout" "http://www.psychppy.org"
  WriteRegStr HKLM "${REG_UNINSTALL}" "Publisher" "Jon Peirce"
SectionEnd

Section "Uninstall"

  SetShellVarContext all
  
  ;ADD YOUR OWN FILES HERE...
  RMDir /r "$INSTDIR"
  
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    
  Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\PsychoPy2.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\PsychoPy homepage.lnk" 
  RMDir "$SMPROGRAMS\$StartMenuFolder"
    
  ;remove from registry
  DeleteRegKey HKLM "${REG_UNINSTALL}"
  DeleteRegKey HKCU "Software\PsychoPy Standalone" ;may have been installed by prev version

  ${un.EnvVarUpdate} $0 "PATH" "R" "HKLM" "$INSTDIR" 

SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd