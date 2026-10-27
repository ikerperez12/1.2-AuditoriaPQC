
## Prerequisites
- Python 3.x installed (Found at `C:\Users\XXX\AppData\Local\Programs\Python\Python312\python.exe`)

## How to Run
1.  Open PowerShell.
2.  Navigate to the `pqc_lab` directory:
    ```powershell
    cd "1.2-AuditoriaPQC/pqc_lab"
    ```
3.  Run the setup script:
    ```powershell
    .\run_visualizer.ps1
    ```

## Qué hace
1.  Crea un entorno virtual (`.venv`).
2.  Instala dependencias (`streamlit`, `pandas`, `plotly`, `scapy`).
3.  **Inicia el Controlador de Laboratorio (Híbrido)**:
    *   **Modo Real**: Si ejecutas `docker-compose up -d`, el controlador usará contenedores OQS reales para generar tráfico criptográfico genuino.
    *   **Modo Física**: Si no hay Docker, usa el Motor de Física (`pqc_engine.py`) para simular latencias deterministas.
4.  Lanza la **Consola QuantumGuard** en tu navegador.

## Cómo activar el Modo Real (Docker)
1.  Abre una terminal en la carpeta del proyecto.
2.  Ejecuta: `docker-compose up -d`
3.  Espera unos segundos. El dashboard cambiará automáticamente a **🟢 TRÁFICO REAL (DOCKER)**.

## Siguientes Pasos
- La consola se abrirá automáticamente en `http://localhost:8501`.
- **Nuevas Pestañas Avanzadas**:
    - **Amenaza HNDL**: Línea de tiempo de riesgo "Harvest Now, Decrypt Later".
    - **Anatomía de Red**: Visualización de impacto en cable (Key Share vs MTU).
    - **Dimensionamiento**: Comparativa de infraestructura (Clásico vs Híbrido vs Puro).
    - **Forensia Canal Lateral**: Simulador de osciloscopio en tiempo real (60fps).
