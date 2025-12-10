# Script para lanzar el visualizador localmente en Windows
$ErrorActionPreference = "Stop"

$VENV_DIR = ".venv"
$REQ_FILE = "requirements_local.txt"
$MOCK_GEN = "client/src/lab_controller.py"
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"

Write-Host "--- Configuración de Visualizador Local PQC Lab ---" -ForegroundColor Cyan

# 1. Check Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python no encontrado en el PATH. Por favor instala Python 3.10+ y asegúrate de marcar 'Add Python to PATH' durante la instalación."
}

# 2. Create Venv if not exists
if (-not (Test-Path $VENV_DIR)) {
    Write-Host "Creando entorno virtual en $VENV_DIR..."
    & $PYTHON_CMD -m venv $VENV_DIR
}

# 3. Activate Venv
$PIP = "$VENV_DIR\Scripts\pip.exe"
$PYTHON = "$VENV_DIR\Scripts\python.exe"

# 4. Install Requirements
Write-Host "Instalando dependencias..."
& $PIP install -r $REQ_FILE | Out-Null

# 5. Start Lab Controller (Real Probe)
Write-Host "Iniciando Controlador de Laboratorio (Sonda Real)..."
$PROBE_PROCESS = Start-Process -FilePath $PYTHON -ArgumentList $MOCK_GEN -PassThru -WindowStyle Hidden

# 6. Launch Streamlit Dashboard
Write-Host "Lanzando Panel de Control..." -ForegroundColor Green
try {
    & $PYTHON -m streamlit run client/src/dashboard.py
}
finally {
    # Cleanup background process on exit
    if ($PROBE_PROCESS -and -not $PROBE_PROCESS.HasExited) {
        Write-Host "Deteniendo sonda..."
        Stop-Process -Id $PROBE_PROCESS.Id -Force
    }
}
