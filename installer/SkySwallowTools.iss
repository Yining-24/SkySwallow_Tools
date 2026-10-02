#define AppName "SkySwallow Tools"
#define AppVersion "0.1.1-preview"

[Setup]
AppId={{4B3B8204-E522-4B8F-BE1C-7B90150BBE46}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=SkySwallow
DefaultDirName={autopf}\SkySwallow Tools
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\SkySwallowServer.exe
OutputDir=..\dist
OutputBaseFilename=SkySwallowTools-Setup-windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\SkySwallowTools\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Start SkySwallow Tools"; Filename: "{app}\SkySwallowServer.exe"; WorkingDir: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  ConfigPath: String;
begin
  if (CurStep <> ssPostInstall) or WizardSilent then
    Exit;

  ConfigPath := ExpandConstant('{commonappdata}\SkySwallowTools\config.py');
  if FileExists(ConfigPath) then
    Exit;

  if not Exec(
    ExpandConstant('{app}\SkySwallowServer.exe'),
    '--configure',
    ExpandConstant('{app}'),
    SW_SHOW,
    ewWaitUntilTerminated,
    ResultCode
  ) or (ResultCode <> 0) then
    MsgBox(
      'The application files were installed, but first-time password setup ' +
      'did not finish. Run SkySwallowServer.exe --configure as an ' +
      'administrator before starting the server.',
      mbError,
      MB_OK
    );
end;
