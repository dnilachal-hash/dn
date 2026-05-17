; ============================================================
; HMC Fee Management System - Inno Setup Installer
; Run AFTER build_exe.bat — packages dist_exe\FeeManagement
; Build: ISCC.exe setup_fee.iss  (from installer\ folder)
; ============================================================

#define MyAppName       "HMC Fee Management System"
#define MyAppVersion    "1.0.0"
#define MyAppPublisher  "Homoeopathic Medical College"
#define MyAppExeName    "FeeManagement.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\HMC-FeeManagement
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=FeeManagementSetup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=admin
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
LicenseFile=assets\LICENSE.txt
InfoBeforeFile=assets\README.txt
MinVersion=10.0.17763

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"
Name: "firewall"; Description: "Add Windows Firewall rule for port 8001"; GroupDescription: "System:"

[Files]
Source: "..\dist_exe\FeeManagement\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\Credentials.txt"; DestDir: "{userdesktop}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""HMC Fee Management"" dir=in action=allow protocol=TCP localport=8001"; \
    Flags: runhidden; Tasks: firewall
Filename: "{app}\{#MyAppExeName}"; Description: "Launch HMC Fee Management System"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""HMC Fee Management"""; Flags: runhidden

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    MsgBox('Installation complete!' + #13#10 + #13#10 +
           'Browser will open to: http://localhost:8001' + #13#10 + #13#10 +
           'Default login: admin / Admin@1234' + #13#10 +
           '(You will be forced to change password on first login)' + #13#10 + #13#10 +
           'Credentials.txt has been placed on your Desktop.',
           mbInformation, MB_OK);
end;
