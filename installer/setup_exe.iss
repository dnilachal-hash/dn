; ============================================================
; HMC Payroll System - Inno Setup Installer
; Wraps the PyInstaller output (dist_exe\PayrollSystem) into
; a single PayrollSystemSetup_v2.0.0.exe
;
; Build with: ISCC.exe setup_exe.iss
; (run from this folder, AFTER build_exe.bat has succeeded)
; ============================================================

#define MyAppName       "HMC Payroll System"
#define MyAppVersion    "2.0.0"
#define MyAppPublisher  "Homoeopathic Medical College"
#define MyAppExeName    "PayrollSystem.exe"

[Setup]
AppId={{B7E8C2F4-9D1A-4A8E-9F6D-12345678ABCD}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\PayrollSystem
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=PayrollSystemSetup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
LicenseFile=assets\LICENSE.txt
InfoBeforeFile=assets\README.txt
UninstallDisplayName={#MyAppName}
MinVersion=10.0.17763

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"
Name: "firewall"; Description: "Add Windows Firewall rule for port 8000"; GroupDescription: "System:"

[Files]
; Entire PyInstaller bundle (PayrollSystem.exe + _internal + frontend_dist + README.txt)
Source: "..\dist_exe\PayrollSystem\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Credentials cheat-sheet on the desktop
Source: "assets\Credentials.txt"; DestDir: "{userdesktop}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Add Windows Firewall rule for port 8000
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""HMC Payroll System"" dir=in action=allow protocol=TCP localport=8000"; \
    Flags: runhidden; Tasks: firewall

; Launch app at the end
Filename: "{app}\{#MyAppExeName}"; Description: "Launch HMC Payroll System"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""HMC Payroll System"""; Flags: runhidden

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    MsgBox('Installation complete!' + #13#10 + #13#10 +
           'The application will start automatically.' + #13#10 +
           'Browser will open to: http://localhost:8000' + #13#10 + #13#10 +
           'Default login: admin / Admin@1234' + #13#10 +
           '(force-change on first login)' + #13#10 + #13#10 +
           'A Credentials.txt has been placed on your Desktop.',
           mbInformation, MB_OK);
  end;
end;
