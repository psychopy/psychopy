
; HM NIS Edit Wizard helper defines
!define PRODUCT_PUBLISHER "Open Science Tools Ltd"
!define PRODUCT_WEB_SITE "https://www.psychopy.org"
;!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\AppMainExe.exe"

!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define FORMER_PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}3"
!define PRODUCT_UNINST_ROOT_KEY "SHELL_CONTEXT"
!define PRODUCT_STARTMENU_REGVAL "NSIS:StartMenuDir"

!include "building\fileassoc.nsh"
; !include "Library.nsh"  ; for installing avbin
!include LogicLib.nsh

; Allow choosing between multiuser and current user (no admin rights) installs
!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_MUI
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!define MULTIUSER_INSTALLMODE_INSTDIR "PsychoPy"
!if ${ARCH} == "win64"
  !define MULTIUSER_USE_PROGRAMFILES64  ; this is a 64bit app
!endif
!include MultiUser.nsh
!include MUI2.nsh


; MULTIUSER Settings
; !define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY 

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
; !insertmacro MUI_UNPAGE_DIRECTORY  ; allow the user to change the uninstall dir?
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION} ${ARCH}"
OutFile "Standalone${PRODUCT_NAME}-${PRODUCT_VERSION}-${ARCH}.exe"

; We set InstallDir inside .onInit instead so it can be dynamic
var InstalledPrevDir

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
  ; NB this function occurs BEFORE the MULTIUSER_PAGE_INSTALLMODE 
  ; so doesn't yet know whether we're single or multi-user
  StrCpy $ICONS_GROUP "${PRODUCT_NAME}-${PRODUCT_VERSION}"
  !insertmacro MULTIUSER_INIT
FunctionEnd

Function un.onInit
  !insertmacro MULTIUSER_UNINIT
FunctionEnd

Section "PsychoPy" SEC01
  SectionIn RO
  SetOutPath "$INSTDIR"
  SetOverwrite on
  ; DetailPrint "Target is $INSTDIR"

  ;if previous version (PsychoPy) installed then remove
  ReadRegStr $InstalledPrevDir SHELL_CONTEXT "${PRODUCT_UNINST_KEY}" "UninstallDir"
  StrCmp $InstalledPrevDir "" continue_inst uninst_query ; if an existing installation check for uninstall
  ; DetailPrint "SHELL_CONTEXT returned $InstalledPrevDir"
  ; ReadRegStr $InstalledPrevDir HKLM "${PRODUCT_UNINST_KEY}" "UninstallDir"
  ; DetailPrint "HKLM returned $InstalledPrevDir"
  ; StrCmp $InstalledPrevDir $InstDir uninst_query  ; if $R0 is empty no need to continue
  ; ReadRegStr $InstalledPrevDir HKCU "${PRODUCT_UNINST_KEY}" "UninstallDir"
  ; DetailPrint "HKCU returned $InstalledPrevDir"
  ; StrCmp $InstalledPrevDir $InstDir uninst_query  ; if $R0 is empty no need to continue

  uninstall_first:
    ExecWait '"$InstalledPrevDir\uninst.exe" _?=$InstalledPrevDir'
    Goto continue_inst
    ; Abort "Install of files has been cancelled. Wise choice. Run the application uninstaller and come back :-)"

  uninst_query:
    IfSilent +3
    MessageBox MB_YESNO|MB_ICONEXCLAMATION \
    "A version of ${PRODUCT_NAME} is already installed. $\r$\n $\r$\n\
    Having 2 copies installed at the same time can cause 'surprising' \
    results. Do you prefer your software not to do surprising things?$\r$\n $\r$\n\
    Press $\r$\n\
    - YES to remove the existing installation$\r$\n\
    - NO to install without removing anything" \
    IDYES uninstall_first \
    IDNO continue_inst

  continue_inst:
    ;AppDir is the path to the psychopy app folder
    Var /GLOBAL AppDir
    StrCpy $AppDir "$InstDir\Lib\site-packages\psychopy\app"

    File /r /x *.pyo /x *.chm /x Editra /x doc "${PYPATH}\*.*"
    ;File "C:\Program Files\ffmpeg.exe"  ; useful alternative just to run a test file

    ; Shortcuts
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\$ICONS_GROUP"
    CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME}-${PRODUCT_VERSION}.lnk" \
        "$INSTDIR\pythonw.exe" "$\"$AppDir\psychopyApp.py$\"" "$AppDir\Resources\psychopy.ico"
    CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME}-${PRODUCT_VERSION} Runner.lnk" \
        "$INSTDIR\pythonw.exe" "$\"$AppDir\psychopyApp.py$\" --runner" "$AppDir\Resources\runner.ico"
    CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME}-${PRODUCT_VERSION} Builder.lnk" \
        "$INSTDIR\pythonw.exe" "$\"$AppDir\psychopyApp.py$\" --builder" "$AppDir\Resources\builder.ico"
    CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\${PRODUCT_NAME}-${PRODUCT_VERSION} Coder.lnk" \
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
    EnVar::AddValue "PATH" "$INSTDIR"
    EnVar::AddValue "PATH" "$INSTDIR\DLLs"

SectionEnd

; Section descriptions - ONLY USE IF USING COMPONENTS
; !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
;   !insertmacro MUI_DESCRIPTION_TEXT ${SEC01} "PsychoPy itself, including python"
; !insertmacro MUI_FUNCTION_DESCRIPTION_END

Section -AdditionalIcons
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\www.psychopy.org.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Uninstall ${PRODUCT_NAME}-${PRODUCT_VERSION}.lnk" "$INSTDIR\uninst.exe"
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section -Post

  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallDir" "$INSTDIR"
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
  ; remove from PATH variable
  EnVar::DeleteValue "PATH" "$INSTDIR"
  EnVar::DeleteValue "PATH" "$INSTDIR\DLLs"

  SetAutoClose true
SectionEnd
