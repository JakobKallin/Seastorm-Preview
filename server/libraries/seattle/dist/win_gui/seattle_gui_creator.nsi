;NSIS Modern User Interface for Seattle
;Written by Zachary Boka

;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"
  
;Include files necessary for creating custom installer pages
  !include "nsDialogs.nsh"
  !include "LogicLib.nsh"

;--------------------------------
;General

  ;Name and file
  Name "Seattle"
  OutFile "seattle_win_gui.exe"
  
  XPStyle on
  
  ;Default installation folder
  InstallDir "$PROGRAMFILES"
  
  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\seattle" ""

  ;Request application privileges for Windows Vista
  RequestExecutionLevel user

;--------------------------------
;Variables

  Var StartMenuFolder
  Var Dialog
  Var Label

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  ;Installer pages
  !insertmacro MUI_PAGE_LICENSE "seattle\LICENSE.txt"
  !insertmacro MUI_PAGE_DIRECTORY

  ;Start Menu Folder Page Configuration
  !define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU" 
  !define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\seattle_nsis" 
  !define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
  
  !insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

  Page custom SeattleInstallNotice ;Custom page
  !insertmacro MUI_PAGE_INSTFILES
  


  ;Uninstaller pages
  !insertmacro MUI_UNPAGE_CONFIRM

  UninstPage custom un.SeattleUninstallNotice ;Custom page

  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Functions

LangString SeattleInstallNoticeHeader ${LANG_ENGLISH} "Installation Notice"
LangString SeattleInstallNoticeSubtitle ${LANG_ENGLISH} " "
LangString SeattleUninstallNoticeHeader ${LANG_ENGLISH} "Uninstall Notice"
LangString SeattleUninstallNoticeSubtitle ${LANG_ENGLISH} " "


;--------------------------------
Function SeattleInstallNotice
  !insertmacro MUI_HEADER_TEXT $(SeattleInstallNoticeHeader) $(SeattleInstallNoticeSubtitle)

  nsDialogs::Create 1018
  Pop $Dialog
  
  ${If} $Dialog == error
  	Abort
  ${EndIf}
  
  ${NSD_CreateLabel} 0 0 100% 24u "After clicking the install button below, a separate window will pop up displaying the installer's progress, and it will close automatically when the installation has completed."
  Pop $Label
  
  nsDialogs::Show

FunctionEnd


Function un.SeattleUninstallNotice
  !insertmacro MUI_HEADER_TEXT $(SeattleUninstallNoticeHeader) $(SeattleUninstallNoticeSubtitle)
  
  nsDialogs::Create 1018
  Pop $Dialog
  
  ${If} $Dialog == error
  	Abort
  ${EndIf}
  
  ${NSD_CreateLabel} 0 0 100% 24u "After clicking the uninstall button below, a separate window will pop up momentarily displaying the uninstaller's progress, and it will close automatically when the uninstall process has completed."
  Pop $Label
  
  nsDialogs::Show

FunctionEnd  



;Installer Sections

Section "Install Section" SecInst

  SetOutPath "$INSTDIR"
  
  ;Package all Seattle files
  File /r seattle

  ;Execute the extract_custom_info.py script that creates the vesselinfo file
  ExecWait '"$INSTDIR\seattle\seattle_repy\extract_custom_info.py"'
  
  ;Execute the install.bat batch file
  ExecWait '"$INSTDIR\seattle\install.bat"'
  
  ;Store installation folder in the registry
  WriteRegStr HKCU "Software\seattle" "" $INSTDIR
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\seattle\Uninstall_seattle.exe"

  ;Create Start menu folder / icons  
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall_seattle.lnk" "$INSTDIR\seattle\Uninstall_seattle.exe"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Start_seattle.lnk" "$INSTDIR\seattle\start_seattle.bat"  
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Stop_seattle.lnk" "$INSTDIR\seattle\stop_seattle.bat"  
  !insertmacro MUI_STARTMENU_WRITE_END

SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall" SecUninst

  ;Execute the uninstall.bat batch file
  ExecWait '"$INSTDIR\seattle_repy\uninstall.bat"'

  ;Remove Seattle from the start menu
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall_seattle.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Start_seattle.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Stop_seattle.lnk"
  RMDir "$SMPROGRAMS\$StartMenuFolder"
  
  ;Remove Seattle from the registry
  DeleteRegKey /ifempty HKCU "Software\seattle_nsis"

  ;Remove all Seattle files from the system
  RMDir /r "$INSTDIR"
  
SectionEnd