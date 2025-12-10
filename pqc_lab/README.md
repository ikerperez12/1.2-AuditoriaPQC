# 🛡️ PQC Lab: Auditoría de Criptografía Post-Cuántica

**Una suite de ingeniería para validar la migración a TLS 1.3 Híbrido (X25519 + Kyber).**

![PQC Lab Dashboard](https://github.com/user-attachments/assets/placeholder-image)

Este proyecto audita el impacto físico y criptográfico de los nuevos algoritmos estándar del NIST (**ML-KEM / Kyber** y **ML-DSA / Dilithium**) en infraestructuras de red reales. Fusiona un motor de simulación física con una sonda de laboratorio basada en **Docker** para medir latencia, fragmentación TCP y riesgos de seguridad (HNDL).

---

## 🚀 Inicio Rápido (Quick Start)

Hemos automatizado todo el despliegue en un solo script de PowerShell.

### Prerrequisitos
1.  **Windows 10/11** (Probado, pero funciona en Linux/Mac adaptando el script).
2.  **Docker Desktop**: Debe estar instalado y corriendo. [Descargar Docker](https://www.docker.com/products/docker-desktop/).
3.  **Python 3.10+**: Debe estar en el PATH.

### Ejecución (One-Click)
Clona el repositorio y haz doble clic en el script `run_visualizer.ps1` o ejecútalo desde terminal:

```powershell
.\run_visualizer.ps1
```

Este script se encarga de todo:
1.  Crea un entorno virtual de Python (`.venv`) seguro.
2.  Instala las dependencias (`requirements_local.txt`).
3.  Levanta los contenedores Docker (`pqc_server` y `pqc_client`).
4.  Lanza el Dashboard interactivo en tu navegador (`http://localhost:8501`).

---

## 🛠️ Arquitectura del Proyecto

El sistema se compone de tres piezas fundamentales:

1.  **El Dashboard (`client/src/dashboard.py`)**: Interfaz visual en Streamlit que actúa como "Single Pane of Glass".
2.  **El Controlador (`client/src/lab_controller.py`)**: Script backend que orquesta las pruebas. Puede inyectar comandos en Docker o simular escenarios.
3.  **La Infraestructura (`docker-compose.yml`)**:
    *   `pqc_server`: Nginx compilado con OQS-OpenSSL (Soporte Post-Cuántica).
    *   `pqc_client`: Curl/OpenSSL modificado para actuar como sonda de red.

---

## ⚙️ Configuración Avanzada

El sistema funciona "Out-of-the-Box" con su configuración por defecto, pero puedes personalizarlo.

### Archivo `lab_config.json`
Este archivo se genera automáticamente al iniciar. No es necesario editarlo manualmente, pero controla el estado:
```json
{
    "mode": "PHYSICS",  // "PHYSICS" (Simulación) o "REAL" (Docker)
    "paused": false     // Pausa/Reanuda la sonda
}
```

### Entorno Virtual (`.venv`)
El script crea una carpeta `.venv` local para aislar las librerías.
*   **Nota de Privacidad**: Esta carpeta contiene rutas locales de tu máquina. **NO la subas a GitHub**. El archivo `.gitignore` incluido ya se encarga de excluirla automáticamente.

---

## 📚 Documentación Técnica

Para un análisis profundo de la ingeniería detrás del proyecto, consulta el documento maestro:
👉 **[EXPLICACIONES.md](./EXPLICACIONES.md)**

Cubre:
*   Análisis de la Amenaza HNDL.
*   Disección de paquetes TLS (WireLab).
*   Dimensionamiento de servidores (CAPEX/OPEX).
*   Comparativa KEMTLS vs PQC Puro.

---

## ⚠️ Solución de Problemas

*   **Error: "Docker no encontrado"**: Asegúrate de que Docker Desktop está corriendo. El icono de la ballena debe estar en la barra de tareas.
*   **Error: "ExecutionPolicy"**: Si PowerShell bloquea el script, ejecútalo como Administrador o usa:
    `powershell -ExecutionPolicy Bypass -File .\run_visualizer.ps1`
*   **Datos no aparecen**: Asegúrate de que el modo en el Dashboard (Barra lateral) esté en "REAL" o "PHYSICS" y no en "PAUSA".

---
**Desarrollado con ❤️ para la asignatura SSI-TT-2526.**
