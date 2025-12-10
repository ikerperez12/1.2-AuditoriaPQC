import subprocess
import sys
import re
import json
import datetime

# Host definido en docker-compose
TARGET_HOST = "pqc_lab_server"
TARGET_PORT = "443"
OPENSSL_BIN = "openssl" # En el contenedor client, este openssl ya es el OQS

# Lista de algoritmos KEM (Key Encapsulation Mechanism) a probar
# Estos nombres deben coincidir con los soportados por liboqs
KEM_ALGORITHMS = [
    "X25519",           # Clásico (Control)
    "kyber768",         # PQC Puro (ML-KEM-768)
    "p256_kyber768",    # Híbrido (NIST Level 3) - Lo más probable en producción
    "p384_kyber768",    # Híbrido Alternativo
    "frodo640aes",      # Otro PQC (Retículos, más pesado)
    "bikel1"            # Otro PQC (Code-based)
]

def check_kem_support(algo):
    """
    Intenta conectar usando un grupo KEM específico mediante openssl s_client.
    """
    cmd = [
        OPENSSL_BIN, "s_client",
        "-connect", f"{TARGET_HOST}:{TARGET_PORT}",
        "-groups", algo,
        "-tls1_3"
    ]
    
    # Ejecutamos s_client y cerramos stdin inmediatamente para terminar la conexión tras el handshake
    try:
        result = subprocess.run(
            cmd,
            input=b"Q", # Enviamos 'Q' para cerrar la conexión limpiamente tras el handshake
            capture_output=True,
            timeout=5
        )
        
        output = result.stdout.decode('utf-8', errors='ignore')
        error_out = result.stderr.decode('utf-8', errors='ignore')
        
        # Análisis de la salida
        # Buscamos "Server Temp Key: <ALGO>" lo que indica negociación exitosa
        match = re.search(r"Server Temp Key: ([\w_]+)", output)
        
        if match:
            negotiated = match.group(1)
            # Verificamos si lo negociado coincide (o contiene) lo que pedimos
            if algo.lower() in negotiated.lower() or negotiated.lower() in algo.lower():
                return True, negotiated
            return False, f"Negociado otro: {negotiated}"
        
        if "handshake failure" in error_out or "no shared cipher" in error_out:
            return False, "Handshake Failure (No soportado por el servidor)"
            
        return False, "Conexión fallida (Sin datos de KEM en output)"

    except subprocess.TimeoutExpired:
        return False, "Timeout (Servidor no responde)"
    except Exception as e:
        return False, str(e)

def main():
    timestamp = datetime.datetime.now().isoformat()
    print(f"--- Iniciando Escaneo PQC contra {TARGET_HOST}:{TARGET_PORT} [{timestamp}] ---")
    print(f"{'Algoritmo (KEM)':<25} | {'Estado':<10} | {'Detalles'}")
    print("-" * 65)
    
    results = {
        "target": TARGET_HOST,
        "timestamp": timestamp,
        "scans": {}
    }

    for algo in KEM_ALGORITHMS:
        supported, details = check_kem_support(algo)
        status = "✅ OK" if supported else "❌ FAIL"
        print(f"{algo:<25} | {status:<10} | {details}")
        results["scans"][algo] = {
            "supported": supported,
            "details": details
        }

    # Exportar resultados para el informe
    report_path = "/captures/scan_results.json"
    try:
        with open(report_path, "w") as f:
            json.dump(results, f, indent=4)
        print(f"\nResultados guardados en {report_path}")
    except IOError as e:
        print(f"\nError guardando reporte: {e}")

if __name__ == "__main__":
    main()