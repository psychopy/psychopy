
; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME "PsychoPy2"
!define PRODUCT_VERSION "1.85.1"
!define PRODUCT_PUBLISHER "Jon Peirce"
!define PRODUCT_WEB_SITE "http://www.psychopy.org"
;!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\AppMainExe.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"
!define PRODUCT_STARTMENU_REGVAL "NSIS:StartMenuDir"

; Modern User Interface v2 ------
!include "MUI2.nsh"
!include "fileassoc.nsh"
!include "EnvVarUpdate.nsh"
!include "Library.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; License page
!insertmacro MUI_PAGE_LICENSE "psychopy/LICENSE.txt"
; Components page NB having multiple components was annoying with uninstall
;!insertmacro MUI_PAGE_COMPONENTS
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
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "StandalonePsychoPy-${PRODUCT_VERSION}-win32.exe"
InstallDir "$PROGRAMFILES\PsychoPy2"
;InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
;Request application privileges for Windows Vista
RequestExecutionLevel admin

;if previous version installed then remove
Function .onInit

  ReadRegStr $R0 HKLM \
  "Software\Microsoft\Windows\CurrentVersion\Uninstall\PsychoPy2" \
  "UninstallString"
  StrCmp $R0 "" done

  IfSilent +3
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
  "A version of PsychoPy2 is already installed. $\n$\nClick `OK` to remove the \
  previous version or `Cancel` to cancel this upgrade. \
  \
  WAIT UNTIL UNINSTALL COMPLETES BEFORE CONTINUING" \
  IDOK uninst
  Abort

;Run the uninstaller
uninst:
  ClearErrors
  ExecWait '"$INSTDIR\uninst.exe" _?=$INSTDIR'
done:
FunctionEnd

Section "PsychoPy" SEC01
  SectionIn RO
  SetShellVarContext all
  SetOutPath "$INSTDIR"
  SetOverwrite on
  ;AppDir is the path to the psychopy app folder
  Var /GLOBAL AppDir
  StrCpy $AppDir "$INSTDIR\Lib\site-packages\psychopy\app"

  File /r /x *.pyo /x *.chm /x Editra /x doc "C:\python27\*.*"
; avbin to system32
  !insertmacro InstallLib DLL NOTSHARED NOREBOOT_PROTECTED avbin.dll $SYSDIR\avbin.dll $SYSDIR

; Shortcuts
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
  CreateDirectory "$SMPROGRAMS\$ICONS_GROUP"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\PsychoPy2.lnk" \
      "$INSTDIR\pythonw.exe" "$\"$AppDir\psychopyApp.py$\"" "$AppDir\Resources\psychopy.ico"
  !insertmacro MUI_STARTMENU_WRITE_END

; File Associations
  !insertmacro APP_ASSOCIATE "psyexp" "PsychoPy.experiment" "PsychoPy Experiment" "$AppDir\Resources\psychopy.ico,0" \
     "Open with PsychoPy" "$\"$INSTDIR\python.exe$\" $\"$AppDir\psychopyApp.py$\" $\"%1$\""

; Update Windows Path
  ;add to path variable
  ${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$INSTDIR"
  ${EnvVarUpdate} $0 "PATH" "A" "HKLM" "$INSTDIR\DLLs"

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
  Delete "$SMPROGRAMS\$ICONS_GROUP\PsychoPy2.lnk"
  RMDir /r "$SMPROGRAMS\$ICONS_GROUP"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  ;DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  ${un.EnvVarUpdate} $0 "PATH" "R" "HKLM" "$INSTDIR"
  ${un.EnvVarUpdate} $0 "PATH" "R" "HKLM" "$INSTDIR\DLLs"

  SetAutoClose true
SectionEnd
