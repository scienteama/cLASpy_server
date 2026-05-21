[Setup]
AppName=cLASpy_T Server
AppVersion=0.1.0
AppPublisher=Scienteama
DefaultDirName={autopf}\cLASpy_T_server
DefaultGroupName=cLASpy_T
OutputBaseFilename=cLASpy_T_installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\launcher.exe
UninstallDisplayName=cLASpy_T Server

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le bureau"
Name: "startmenu"; Description: "Créer un raccourci dans le menu Démarrer"

[Files]
Source: "dist\launcher.dist\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\cLASpy_T Server"; Filename: "{app}\launcher.exe"; Tasks: startmenu
Name: "{commondesktop}\cLASpy_T Server"; Filename: "{app}\launcher.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\launcher.exe"; Description: "Lancer cLASpy_T Server"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"