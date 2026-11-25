; Inno-Setup-Skript für den Windows-Installer von Tabularium.
; Bauen (nach PyInstaller):  iscc /DVersion=1.1.0 packaging\windows.iss

#ifndef Version
  #define Version "0.0.0"
#endif

[Setup]
AppId={{6E1C2B7A-4F3D-4C1E-9A8B-7D2E5F6A1B3C}
AppName=Tabularium
AppVersion={#Version}
AppVerName=Tabularium {#Version}
AppPublisher=Patrick Baumfalk
AppPublisherURL=https://github.com/PBaumfalk/Tabularium
AppSupportURL=https://github.com/PBaumfalk/Tabularium/blob/main/docs/handbuch/README.md
DefaultDirName={autopf}\Tabularium
DefaultGroupName=Tabularium
DisableProgramGroupPage=yes
; Installation ohne Administratorrechte in das Benutzerprofil, auf Wunsch für alle
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=Tabularium-{#Version}-Windows-Setup
SetupIconFile=Tabularium.ico
UninstallDisplayIcon={app}\Tabularium.exe
UninstallDisplayName=Tabularium
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=force

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\Tabularium\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Tabularium"; Filename: "{app}\Tabularium.exe"
Name: "{group}\Handbuch"; Filename: "https://github.com/PBaumfalk/Tabularium/blob/main/docs/handbuch/README.md"
Name: "{group}\Tabularium deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Tabularium"; Filename: "{app}\Tabularium.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Tabularium.exe"; Description: "Tabularium jetzt starten"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/IM Tabularium.exe /F"; Flags: runhidden; RunOnceId: "TabulariumBeenden"

[Registry]
; Autostart-Eintrag (falls in Tabularium eingeschaltet) beim Deinstallieren entfernen
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "Tabularium"; Flags: uninsdeletevalue dontcreatekey

[Messages]
german.FinishedLabel=Tabularium ist installiert. Ihr Archiv liegt im Ordner „Tabularium“ in Ihrem Benutzerordner und bleibt auch bei einer Deinstallation erhalten.
