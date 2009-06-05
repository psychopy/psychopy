;NSIS Modern User Interface
;Start Menu Folder Selection Example Script
;Written by Joost Verburg

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"

;--------------------------------
;General

  ;Name and file
  Name "PsychoPy"
  OutFile "StandalonePsychoPy-x.xx.xx-win32.exe"
  InstallDir "$PROGRAMFILES\PsychoPy"
  Icon "C:\USERS\jwp\Code\PsychoPy\svn\trunk\PsychoPyIDE\psychopy.ico"
  
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

  !insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
  ;!insertmacro MUI_PAGE_COMPONENTS;we only have component so don't need this
  !insertmacro MUI_PAGE_DIRECTORY
  
  ;Start Menu Folder Page Configuration
  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM" 
  !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\PsychoPy Standalone" 
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "PsychoPy Standalone"
  !define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\
\PsychoPy1"

  !insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
  
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"
  
;--------------------------------
;Installer Sections

Section "PsychoPy" PsychoPy

  SetOutPath "$INSTDIR"
  
  ;ADD YOUR OWN FILES HERE...
  file /r "C:\USERS\jwp\Code\PsychoPy\svn\trunk\PsychoPyIDE\dist\*.*"
  
  ;Store installation folder
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayName" "PsychoPy1 (Standalone)"  
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayVersion" "1.0"   
  WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayIcon" "$INSTDIR\PsychoPyIDE.exe" 
  WriteRegStr HKLM "${REG_UNINSTALL}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    
    ;Create shortcuts
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\PsychoPyIDE.lnk" "$INSTDIR\PsychoPyIDE.exe"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\PsychoPy homepage.lnk" "http://www.psychopy.org"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\PsychoPy reference.lnk" "http://www.psychopy.org/reference"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\PsychoPy tutorials.lnk" "http://www.psychopy.org/home.php/Docs/Tutorials"
  
  !insertmacro MUI_STARTMENU_WRITE_END

SectionEnd

 
;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...
  RMDir /r "$INSTDIR"
  
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    
  Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\PsychoPyIDE.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\PsychoPy homepage.lnk" 
  Delete "$SMPROGRAMS\$StartMenuFolder\PsychoPy reference.lnk" 
  Delete "$SMPROGRAMS\$StartMenuFolder\PsychoPy tutorials.lnk" 
  RMDir "$SMPROGRAMS\$StartMenuFolder"
  
  DeleteRegKey HKLM "${REG_UNINSTALL}"
  DeleteRegKey HKCU "Software\PsychoPy Standalone" ;may have been installed by prev version

SectionEnd