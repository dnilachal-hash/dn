; ==========================================================================
; HMC Payroll System — Inno Setup Installer Script
; Build with: ISCC.exe setup.iss  (Inno Setup 6+)
; Produces: PayrollSystemSetup_v2.0.0.exe (~300 MB with all bundled assets)
; ==========================================================================

#define MyAppName       "HMC Payroll System"
#define MyAppVersion    "2.0.0"
#define MyAppPublisher  "Homoeopathic Medical College"
#define MyAppURL        "https://hmc.local"
#define MyAppExeName    "start.bat"

[Setup]
AppId={{B7E8C2F4-9D1A-4A8E-9F6D-12345678ABCD}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName=C:\PayrollSystem
DefaultGroupName={#MyAppName}
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=output
OutputBaseFilename=PayrollSystemSetup_v{#MyAppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
LicenseFile=assets\LICENSE.txt
InfoBeforeFile=assets\README.txt
UninstallDisplayIcon={app}\assets\icon.ico
UninstallDisplayName={#MyAppName}
MinVersion=10.0.17763

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"
Name: "firewall"; Description: "Add Windows Firewall rule for port 8000"; GroupDescription: "System:"

[Files]
; Application source code
Source: "..\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\frontend\dist\*"; DestDir: "{app}\frontend\dist"; Flags: ignoreversion recursesubdirs createallsubdirs

; Bundled Python 3.11 embeddable (download from python.org → place in payload/)
Source: "payload\python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs

; Bundled pip wheels for offline install
Source: "payload\wheels\*"; DestDir: "{app}\wheels"; Flags: ignoreversion recursesubdirs

; Bundled PostgreSQL portable (optional — use SQLite if absent)
Source: "payload\postgres\*"; DestDir: "{app}\postgres"; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist

; Assets
Source: "assets\icon.ico"; DestDir: "{app}\assets"
Source: "assets\README.txt"; DestDir: "{app}\assets"
Source: "assets\Credentials.txt"; DestDir: "{userdesktop}"; Flags: ignoreversion

; Launcher scripts
Source: "scripts\start.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "scripts\stop.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "scripts\backup.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "scripts\install_deps.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{group}\Stop Server"; Filename: "{app}\stop.bat"
Name: "{group}\Take Backup"; Filename: "{app}\backup.bat"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Run]
; Install pip dependencies from bundled wheels (offline)
Filename: "{app}\install_deps.bat"; StatusMsg: "Installing Python dependencies..."; Flags: runhidden

; Add firewall rule
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""HMC Payroll System"" dir=in action=allow protocol=TCP localport=8000"; \
    Flags: runhidden; Tasks: firewall

; Launch application
Filename: "{app}\{#MyAppExeName}"; Description: "Launch HMC Payroll System"; Flags: nowait postinstall skipifsilent

; Open browser to login page
Filename: "{cmd}"; Parameters: "/c start http://localhost:8000"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""HMC Payroll System"""; Flags: runhidden

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  MsgBox('HMC Payroll System v{#MyAppVersion} will be installed to C:\PayrollSystem.' + #13#10 + #13#10 +
         'Default credentials (force-change on first login):' + #13#10 +
         '  admin / Admin@1234' + #13#10 + '  hr / Hr@1234' + #13#10 + #13#10 +
         'A Credentials.txt file will be placed on your Desktop.',
         mbInformation, MB_OK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    MsgBox('Installation complete!' + #13#10 + #13#10 +
           'The application will start automatically.' + #13#10 +
           'Browser will open to: http://localhost:8000' + #13#10 + #13#10 +
           'Credentials.txt has been placed on your Desktop.',
           mbInformation, MB_OK);
  end;
end;
