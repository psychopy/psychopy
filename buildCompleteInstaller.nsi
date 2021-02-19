
; HM NIS Edit Wizard helper defines
!define PRODUCT_PUBLISHER "Jon Peirce"
!define PRODUCT_WEB_SITE "https://www.psychopy.org"
;!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\AppMainExe.exe"

!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "SHELL_CONTEXT"
var PRODUCT_REGISTRY_ROOT

!define PRODUCT_STARTMENU_REGVAL "NSIS:StartMenuDir"


; Modern User Interface v2 ------

; Allow choosing between multiuser and current user (no admin rights) installs
!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_MUI
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!include MultiUser.nsh

!include "MUI2.nsh"
!include "building\fileassoc.nsh"
!include "building\EnvVarUpdate.nsh"
!include "Library.nsh"
!include LogicLib.nsh

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; License page
!insertmacro MUI_PAGE_LICENSE "psychopy/LICENSE.txt"
; Components page NB having multiple components was annoying with uninstall
;!insertmacro MUI_PAGE_COMPONENTS
; Choice for multiuser or single user install - note that this page only 
; displays if the user has privileges to do the AllUsers
!define MUI_PAGE_CUSTOMFUNCTION_PRE multiuser_pre_func
!insertmacro MULTIUSER_PAGE_INSTALLMODE
; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; Start menu page
var ICONS_GROUP
!define MUI_STARTMENUPAGE_NODISABLE
!define MUI_STARTMENUPAGE_DEFAULTFOLDER "${PRODUCT_NAME}"
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "${PRODUCT_UNINST_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "${PRODUCT_STARTMENU_REGVAL}"
!insertmacro MUI_PAGE_STARTMENU Application $ICONS_GROUP

; Instfiles page
!insertmacro MUI_PAGE_INSTFILES

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION} ${ARCH}"
OutFile "Standalone${PRODUCT_NAME}-${PRODUCT_VERSION}-${ARCH}.exe"

; We set InstallDir inside .onInit instead so it can be dynamic
InstallDir ""

ShowInstDetails show
ShowUnInstDetails show

;pre-multiuser detection
Function multiuser_pre_func

       ClearErrors
       ReadRegStr $R1 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "InstallDir"
       ${Unless} ${Errors}
           Abort
       ${EndUnless}

FunctionEnd

Function .onInit
  !insertmacro MULTIUSER_INIT

  ${If} $MultiUser.InstallMode == "CurrentUser"
    SetShellVarContext current
    StrCpy $InstDir "$LOCALAPPDATA\${PRODUCT_NAME}"
    StrCpy $PRODUCT_REGISTRY_ROOT "HKCU"
    IfFileExists $SYSDIR\avbin.dll continue_init 0
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "You do not have admin privileges, which are needed to install AVBin. \
    $\n$\nPlease cancel the install and run with admin \
    privileges, or manually install AVBin later." \
    IDOK continue_init
    Abort
  ${Else}
    SetShellVarContext all
    ${If} ${ARCH} == "win64"
      StrCpy $InstDir "$PROGRAMFILES64\${PRODUCT_NAME}"
    ${Else}
      StrCpy $InstDir "$PROGRAMFILES\${PRODUCT_NAME}"
    ${EndIf}
    StrCpy $PRODUCT_REGISTRY_ROOT "HKLM"
  ${EndIf}

  continue_init:

  ;if previous version installed then remove
  ReadRegStr $R0 SHELL_CONTEXT \
  "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" \
  "UninstallString"
  StrCmp $R0 "" done

  IfSilent +3
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
  "A version of ${PRODUCT_NAME} is already installed. $\n$\nClick `OK` to remove the \
  previous version or `Cancel` to cancel this upgrade." \
  IDOK uninst
  Abort

  ;Run the uninstaller
  uninst:
    ClearErrors
    ExecWait '"$INSTDIR\uninst.exe" _?=$INSTDIR'
  done:
FunctionEnd

Function un.onInit
  !insertmacro MULTIUSER_UNINIT
  ${If} $MultiUser.InstallMode == "CurrentUser"
    SetShellVarContext current
    StrCpy $InstDir "$LOCALAPPDATA\${PRODUCT_NAME}"
    StrCpy $PRODUCT_REGISTRY_ROOT "HKCU"
  ${Else}
    SetShellVarContext all
    ${If} ${ARCH} == "win64"
      StrCpy $InstDir "$PROGRAMFILES64\${PRODUCT_NAME}"
    ${Else}
      StrCpy $InstDir "$PROGRAMFILES\${PRODUCT_NAME}"
    ${EndIf}
    StrCpy $PRODUCT_REGISTRY_ROOT "HKLM"
  ${EndIf}

FunctionEnd

Section "PsychoPy" SEC01
  SectionIn RO
  SetOutPath "$INSTDIR"
  SetOverwrite on
  ;AppDir is the path to the psychopy app folder
  Var /GLOBAL AppDir
  StrCpy $AppDir "$INSTDIR\Lib\site-packages\psychopy\app"

  File /r /x *.pyo /x *.chm /x Editra /x doc "${PYPATH}*.*"

  ${If} $MultiUser.InstallMode == "AllUsers"
  ; avbin to system32
    !insertmacro InstallLib DLL NOTSHARED NOREBOOT_PROTECTED avbin.dll $SYSDIR\avbin.dll $SYSDIR
  ${EndIf}

; Shortcuts
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
  CreateDirectory "$SMPROGRAMS\$ICONS_GROUP"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME}.lnk" \
      "$INSTDIR\pythonw.exe" "$\"$AppDir\psychopyApp.py$\"" "$AppDir\Resources\psychopy.ico"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME} Runner.lnk" \
      "$INSTDIR\pythonw.exe" "$\"$AppDir\psychopyApp.py$\" --runner" "$AppDir\Resources\runner.ico"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME} Builder.lnk" \
      "$INSTDIR\pythonw.exe" "$\"$AppDir\psychopyApp.py$\" --builder" "$AppDir\Resources\builder.ico"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME} Coder.lnk" \
      "$INSTDIR\pythonw.exe" "$\"$AppDir\psychopyApp.py$\" --coder"  "$AppDir\Resources\coder.ico"
  !insertmacro MUI_STARTMENU_WRITE_END

; File Associations
  !insertmacro APP_ASSOCIATE "psyexp" "PsychoPy.experiment" "PsychoPy Experiment" "$AppDir\Resources\builder.ico,0" \
     "Open with PsychoPy" "$\"$INSTDIR\python.exe$\" $\"$AppDir\psychopyApp.py$\" $\"%1$\""
  ; !insertmacro APP_ASSOCIATE "py" "PsychoPy.script" "PsychoPy Experiment" "$AppDir\Resources\coder.ico,0" \
  ;    "Open with PsychoPy" "$\"$INSTDIR\python.exe$\" $\"$AppDir\psychopyApp.py$\" $\"%1$\""
  !insertmacro APP_ASSOCIATE "psyrun" "PsychoPy.runner" "PsychoPy Runner List" "$AppDir\Resources\runner.ico,0" \
     "Open with PsychoPy" "$\"$INSTDIR\python.exe$\" $\"$AppDir\psychopyApp.py$\" $\"%1$\""

; Update Windows Path
  ;add to path variable
  ${EnvVarUpdate} $0 "PATH" "A" "$PRODUCT_REGISTRY_ROOT" "$INSTDIR"
  ${EnvVarUpdate} $0 "PATH" "A" "$PRODUCT_REGISTRY_ROOT" "$INSTDIR\DLLs"

SectionEnd

; Section descriptions - ONLY USE IF USING COMPONENTS
; !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
;   !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} "PsychoPy itself, including python"
; !insertmacro MUI_FUNCTION_DESCRIPTION_END

Section -AdditionalIcons
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\www.psychopy.org.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Uninstall.lnk" "$INSTDIR\uninst.exe"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  ;WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\AppMainExe.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd


Section Uninstall
  !insertmacro MUI_STARTMENU_GETFOLDER "Application" $ICONS_GROUP

  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  RMDir /r "$INSTDIR"
  ; NB we don't uninstall avbin - it might be used by another python installation

  ;shortcuts
  Delete "$SMPROGRAMS\$ICONS_GROUP\Uninstall.lnk"
  Delete "$SMPROGRAMS\$ICONS_GROUP\www.psychopy.org.lnk"
  Delete "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\$ICONS_GROUP"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  ;DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  ${un.EnvVarUpdate} $0 "PATH" "R" "$PRODUCT_REGISTRY_ROOT" "$INSTDIR"
  ${un.EnvVarUpdate} $0 "PATH" "R" "$PRODUCT_REGISTRY_ROOT" "$INSTDIR\DLLs"

  SetAutoClose true
SectionEnd
