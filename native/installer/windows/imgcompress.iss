; Inno Setup script for Imgcompress Windows installer
[Setup]
AppName=Imgcompress
AppVersion=1.0.0
AppPublisher=Imgcompress
DefaultDirName={pf}\Imgcompress
DefaultGroupName=Imgcompress
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=.
OutputBaseFilename=Imgcompress-Setup
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
Compression=lzma2
SolidCompression=yes
LicenseFile=..\..\..\LICENSE
ShowLanguageDialog=yes
LanguageDetectionMethod=locale

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: unchecked

[Files]
Source: "..\..\dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Imgcompress"; Filename: "{app}\ImgcompressNative.exe"
Name: "{userdesktop}\Imgcompress"; Filename: "{app}\ImgcompressNative.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ImgcompressNative.exe"; Description: "安装完成后运行"; Flags: nowait postinstall skipifsilent
