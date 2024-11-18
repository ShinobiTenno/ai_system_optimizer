#define MyAppName "AI System Optimizer"
#define MyAppVersion "1.0"
#define MyAppPublisher "HighP Software"
#define MyAppExeName "ai_system_optimizer.exe"
#define MyAppDeveloper "Shinobi_Tenno (Laurens S.)"

[Setup]
AppId={{B91C8E72-3F69-4D97-AE8B-7B789C7E2F89}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppContact={#MyAppDeveloper}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputDir=installer_output
OutputBaseFilename=AiSystemOptimizer_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
SetupMutex={#MyAppName}Setup
WizardStyle=modern
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ChangesAssociations=yes
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp
DisableWelcomePage=no
AlwaysShowDirOnReadyPage=yes
DisableProgramGroupPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Welcome to the {#MyAppName} Setup Wizard
WelcomeLabel2=This will install {#MyAppName} version {#MyAppVersion} on your computer.%n%nThis software helps optimize your system performance for AI and resource-intensive applications.%n%nDeveloped by {#MyAppDeveloper}, this tool is part of a broader mission to support COPD and Alpha-1 research.
LicenseLabel3=Please read the License Agreement and COPD Research Information. Your support in raising awareness for COPD and Alpha-1 research is greatly appreciated.
FinishedLabel=Thank you for installing {#MyAppName}!%n%nTo learn more about COPD Alpha-1 or to support research, please visit:%nwww.alpha1.org

[CustomMessages]
LaunchMessage=Would you like to launch AI System Optimizer now?
DonateMessage=Would you like to visit the Alpha-1 Foundation donation page?
AboutMessage=About the Developer:%nThis software is developed by {#MyAppDeveloper}, who lives with COPD Alpha-1.%n%nYour support for COPD research can make a difference.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\ai_system_optimizer.exe"; DestDir: "{app}"; Flags: ignoreversion signonce
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--admin"
Name: "{group}\License and COPD Information"; Filename: "{app}\LICENSE.txt"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Parameters: "--admin"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runascurrentuser
Filename: "https://www.alpha1.org/get-involved/donate/"; Description: "Support COPD Research"; Flags: postinstall shellexec skipifsilent unchecked
