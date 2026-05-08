; ─────────────────────────────────────────────────────────────────────────────
; finaxis_setup.iss — Script de Inno Setup para el instalador de Finaxis Local
;
; Genera: FinaxisSetup_v1.0.exe
; Requiere: Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
;
; USO: Compilar con Inno Setup Compiler después de tener la carpeta dist/finaxis_local
; ─────────────────────────────────────────────────────────────────────────────

#define MyAppName        "Finaxis Local"
#define MyAppVersion     "1.0"
#define MyAppPublisher   "Finaxis - Soluciones Contables"
#define MyAppURL         "https://finaxis.com.co"
#define MyAppExeName     "FinaxisLocal.exe"
#define MyAppID          "{A3F2B891-7E4D-4C12-9F83-2D5E1A6B7C89}"

[Setup]
; Identificador único del instalador (NO cambiar entre versiones del mismo producto)
AppId={{A3F2B891-7E4D-4C12-9F83-2D5E1A6B7C89}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Directorio de instalación predeterminado
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; Permitir cambiar el directorio de instalación
DisableDirPage=no

; Icono del instalador
SetupIconFile=assets\finaxis.ico

; Archivo de salida
OutputDir=..\dist\instalador
OutputBaseFilename=FinaxisSetup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra64

; Requiere privilegios de administrador para instalar
PrivilegesRequired=admin

; Idioma y visualización
ShowLanguageDialog=no
ShowComponentSizes=yes

; Información de licencia (opcional)
; LicenseFile=licencia_usuario.rtf

; ── Versión mínima de Windows: Windows 10 ────────────────────────────────────
MinVersion=10.0

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
; Opciones que el usuario puede marcar durante la instalación
Name: "desktopicon";   Description: "Crear icono en el Escritorio";      GroupDescription: "Accesos directos:"; Flags: unchecked
Name: "startmenuicon"; Description: "Crear icono en el Menu de Inicio";  GroupDescription: "Accesos directos:"
Name: "autostart";     Description: "Iniciar Finaxis al encender el PC"; GroupDescription: "Opciones:"; Flags: unchecked

[Files]
; 1. Ejecutable principal y sus librerias
Source: "C:\ContaPY2\dist\finaxis_local\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs; \
    Excludes: "frontend\*,node.exe"

; 2. Node.js portable
Source: "C:\ContaPY2\dist\finaxis_local\node.exe"; DestDir: "{app}"; \
    Flags: ignoreversion

; 3. Frontend Next.js standalone
Source: "C:\ContaPY2\dist\finaxis_local\frontend\*"; DestDir: "{app}\frontend"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; 4. Icono (para los accesos directos)
Source: "assets\finaxis.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Acceso en el Menu de Inicio (siempre se crea)
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\finaxis.ico"
; Desinstalador en el Menu de Inicio
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"

; Acceso directo en el Escritorio (siempre se crea)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\finaxis.ico"

[Registry]
; Arranque automático con Windows (solo si el usuario marcó la opción)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "{#MyAppName}"; \
    ValueData: """{app}\{#MyAppExeName}"""; \
    Flags: uninsdeletevalue; Tasks: autostart

[Run]
; Ejecutar la aplicación al finalizar la instalación (opcional)
Filename: "{app}\{#MyAppExeName}"; \
    Description: "Iniciar {#MyAppName} ahora"; \
    Flags: nowait postinstall skipifsilent

[UninstallRun]
; Cerrar FinaxisLocal.exe antes de desinstalar
Filename: "taskkill.exe"; Parameters: "/F /IM FinaxisLocal.exe"; \
    Flags: runhidden skipifdoesntexist
; Cerrar node.exe (servidor Next.js) antes de desinstalar
Filename: "taskkill.exe"; Parameters: "/F /IM node.exe"; \
    Flags: runhidden skipifdoesntexist

[Messages]
; Mensajes personalizados en español
WelcomeLabel1=Bienvenido al instalador de [name]
WelcomeLabel2=Este asistente instalará [name/ver] en su computador.%n%nFinaxis es un sistema contable profesional que funciona completamente sin internet, directamente en su PC.%n%nSe recomienda cerrar todas las demás aplicaciones antes de continuar.
FinishedLabel=La instalación de [name] ha finalizado exitosamente.%n%nPuede iniciar el programa desde el acceso directo creado.%n%nRecuerde: Al iniciar por primera vez, el sistema se configurará automáticamente (puede tomar unos segundos).

[Code]
// ── Verificar que el proceso no esté corriendo antes de instalar ─────────────
function IsAppRunning(): Boolean;
var
  ResultCode: Integer;
begin
  Result := False;
  if Exec('tasklist.exe', '/FI "IMAGENAME eq FinaxisLocal.exe" /NH', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := (ResultCode = 0);
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Verificar Windows 10 o superior
  if not IsWin64 then begin
    MsgBox('Finaxis Local requiere Windows 10 de 64 bits o superior.', mbCriticalError, MB_OK);
    Result := False;
    Exit;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssInstall then begin
    // Cerrar instancias anteriores si estan corriendo
    Exec('taskkill.exe', '/F /IM FinaxisLocal.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('taskkill.exe', '/F /IM node.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Sleep(1500);
  end;
end;
