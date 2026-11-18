#ifndef Payload
  #error Pass /DPayload=path_to_staged_Deckivo
#endif

[Setup]
AppId={{9A825D7B-1E10-44D0-ABBD-7D2A78A726CB}
AppName=Deckivo
AppVersion=0.9.0.5
VersionInfoVersion=0.9.0.5
SetupIconFile=deckivo.ico
AppVerName=Deckivo 0.9.0 Preview (build 5)
DefaultDirName={localappdata}\Programs\Deckivo
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\Deckivo.exe
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputBaseFilename=Deckivo-0.9.0-preview-Windows-x64-Setup
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "{#Payload}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Icons]
Name: "{userprograms}\Deckivo"; Filename: "{app}\Deckivo.exe"; IconFilename: "{app}\deckivo.ico"
Name: "{userdesktop}\Deckivo"; Filename: "{app}\Deckivo.exe"; WorkingDir: "{app}"; IconFilename: "{app}\deckivo.ico"; Tasks: desktopicon
