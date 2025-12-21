; NSIS Installer Script for XLTickers
; This script creates a Windows installer for XLTickers

!include "MUI2.nsh"
!include "x64.nsh"

; Name and file
Name "XLTickers"
OutFile "dist\XLTickers-Installer.exe"

; Default installation folder
InstallDir "$PROGRAMFILES\XLTickers"

; Get installation folder from registry if available
InstallDirRegKey HKCU "Software\XLTickers" ""

; Request application privileges for Windows Vista and higher
RequestExecutionLevel admin

; ========================================
; MUI Settings
; ========================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; ========================================
; Installer Sections
; ========================================

Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Copy all files from dist\XLTickers
  File /r "dist\XLTickers\*.*"
  
  ; Create start menu shortcuts
  CreateDirectory "$SMPROGRAMS\XLTickers"
  CreateShortcut "$SMPROGRAMS\XLTickers\XLTickers.lnk" "$INSTDIR\XLTickers.exe"
  CreateShortcut "$SMPROGRAMS\XLTickers\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  
  ; Create desktop shortcut
  CreateShortcut "$DESKTOP\XLTickers.lnk" "$INSTDIR\XLTickers.exe"
  
  ; Write uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Write registry keys for uninstall
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\XLTickers" "DisplayName" "XLTickers"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\XLTickers" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\XLTickers" "InstallLocation" "$INSTDIR"
  
  ; Store installation folder
  WriteRegStr HKCU "Software\XLTickers" "" $INSTDIR
  
SectionEnd

; ========================================
; Uninstaller Section
; ========================================

Section "Uninstall"
  
  ; Remove files and directories
  RMDir /r "$INSTDIR"
  
  ; Remove Start Menu shortcuts
  RMDir /r "$SMPROGRAMS\XLTickers"
  
  ; Remove Desktop shortcut
  Delete "$DESKTOP\XLTickers.lnk"
  
  ; Remove registry keys
  DeleteRegKey /ifempty HKCU "Software\XLTickers"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\XLTickers"
  
SectionEnd

; ========================================
; Functions
; ========================================

Function .onInstSuccess
  MessageBox MB_OK "XLTickers installed successfully!"
FunctionEnd

Function un.onUninstSuccess
  MessageBox MB_OK "XLTickers uninstalled successfully!"
FunctionEnd
