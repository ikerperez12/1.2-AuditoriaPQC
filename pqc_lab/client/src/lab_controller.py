import subprocess
import json
import time
import re
import os
import random
from datetime import datetime
import pqc_engine
from pqc_engine import CryptoSuite

# CONFIGURACIÓN DEL OBJETIVO
TARGET_IP = "127.0.0.1" # O la IP de tu contenedor Docker
TARGET_PORT = "4433"    # Puerto expuesto de Nginx PQC
OPENSSL_BIN = "openssl" # Ruta a tu binario OQS-OpenSSL
PCAP_FILE = "captures/handshake.pcap"
REPORT_FILE = "captures/real_scan_results.json"

# Mapeo de nombres Legacy (Dashboard) -> Nombres Técnicos (OpenSSL/Docker)
GROUP_MAPPING = {
    "kyber768": "mlkem768",
    "x25519_kyber768": "X25519MLKEM768",
    "X25519": "X25519"
}

def measure_handshake_real(group_name):
    """
    Ejecuta un handshake real usando Docker (pqc_client -> pqc_server).
    """
    print(f"[*] [DOCKER] Probando Grupo: {group_name}...")
    
    # Resolver nombre técnico para el comando
    technical_name = GROUP_MAPPING.get(group_name, group_name)
    
    # Comando para ejecutar dentro del contenedor cliente
    # openssl s_client -connect pqc_server:4433 -groups ...
    docker_cmd = [
        "docker", "exec", "pqc_client", 
        "openssl", "s_client",
        "-connect", "pqc_server:4433",
        "-groups", technical_name, # Usar nombre exacto (case-sensitive para OQS a veces)
        "-tls1_3"
    ]
    
    start_time = time.perf_counter()
    
    # Retry Logic (Max 3 attempts)
    max_retries = 3
    result = None
    
    for attempt in range(max_retries):
        try:
            # Ejecutamos docker exec
            result = subprocess.run(
                docker_cmd, 
                input=b"Q", 
                capture_output=True, 
                timeout=8 
            )
            
            # Check if successful execution (return code 0)
            # Note: OpenSSL s_client might return non-zero on some handshake failures, 
            # but we check stdout later. Here we care if Docker itself failed.
            if result.returncode == 0:
                break # Success, exit loop
            
            # If we are here, it might be a transient error
            time.sleep(1)
            
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed, return None
                return None
            time.sleep(1)
            
    if not result:
        return None

    end_time = time.perf_counter()
        
    output = result.stdout.decode('utf-8', errors='ignore')
    error_output = result.stderr.decode('utf-8', errors='ignore')
    
    # Combinar outputs para debug si falla
    full_output = output + "\n[STDERR]\n" + error_output
    
    # Si Docker falla o el contenedor no existe, retornamos None para activar fallback
    if result.returncode != 0 and "Container" in error_output:
        return None

    # 3. Análisis Forense del Output
    match_key = re.search(r"Server Temp Key: ([\w_]+)", output)
    negotiated = match_key.group(1) if match_key else "Failed"
    
    # Métricas Reales
    latency_ms = (end_time - start_time) * 1000
    # NOTA: No restamos overhead para evitar valores cercanos a 0 en redes rápidas.
    # La latencia incluirá el tiempo de 'docker exec', lo cual es aceptable para 'End-to-End'.
    
    success = "Cipher is TLS_AES" in output
        
    if not success and "connect:errno" in full_output:
         return None # Fallback si no conecta

    # Tamaños estimados (OQS standard)
    client_payload = 0
    group_lower = group_name.lower()
    
    if "x25519_kyber768" in group_lower:
        # Hybrid: X25519(32) + Kyber768(1184) + Header(~200)
        client_payload = 32 + 1184 + 200
    elif "kyber768" in group_lower or "mlkem768" in group_lower:
        # Pure: Kyber768(1184) + Header(~200)
        client_payload = 1184 + 200
    elif "dilithium" in group_lower or "mldsa" in group_lower:
         client_payload = 2500 
    else:
        # Classic: X25519(32) + Header(~200)
        client_payload = 32 + 200
        
    return {
        "timestamp": datetime.now().isoformat(),
        "algorithm": group_name,
        "supported": success,
        "negotiated_details": f"Negociado (Docker): {negotiated}",
        "handshake_latency_ms": round(latency_ms, 2),
        "phase1_key_share_bytes": client_payload - 200,
        "phase2_total_bytes": client_payload,
        "phase2_fragmented": client_payload > 1460,
        "phase2_overhead_factor": round(client_payload / 432.0, 2),
        "phase3_throughput_req_s": int(1000 / (client_payload / 432.0)) if client_payload > 0 else 0,
        "source": "REAL_DOCKER",
        "raw_output_snippet": full_output[:500] # Debug info (ampliado)
    }

    # except Exception as e:
    #     # print(f"[!] Error Docker {group_name}: {e}")
    #     return None
    return None # Should be unreachable if logic is correct, but safe fallback

def measure_handshake_physics(group_name, suite):
    """
    Fallback al Motor de Física si no hay servidor real.
    """
    print(f"[*] [PHYSICS] Simulando Grupo: {group_name}...")
    link_rtt = random.uniform(20, 40)
    result = pqc_engine.run_network_simulation(suite, link_rtt)
    
    overhead_factor = result["metrics"]["server_payload_size"] / 432.0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "algorithm": group_name,
        "supported": True,
        "negotiated_details": f"Simulado: {group_name}",
        "handshake_latency_ms": round(result["total_latency_ms"], 2),
        "phase1_key_share_bytes": result["metrics"]["key_share_size"],
        "phase2_total_bytes": result["metrics"]["client_payload_size"],
        "phase2_fragmented": result["fragmentation_risk"],
        "phase2_overhead_factor": round(overhead_factor, 2),
        "phase3_throughput_req_s": int(1000 / overhead_factor) if overhead_factor > 0 else 0,
        "source": "PHYSICS_ENGINE"
    }

def main():
    # Asegurar directorio
    os.makedirs("captures", exist_ok=True)
    
    # Grupos a probar
    # NOTA: Usamos los nombres estándar de OQS para asegurar compatibilidad con la imagen Docker
    TARGET_GROUPS = [
        ("X25519", CryptoSuite.CLASSIC),          # Clásico
        ("x25519_kyber768", CryptoSuite.HYBRID),  # Híbrido (Nombre Legacy para Dashboard)
        ("kyber768", CryptoSuite.PURE)            # PQC Puro (Nombre Legacy para Dashboard)
    ]

    print("--- INICIANDO CONTROLADOR DE LABORATORIO REAL (HÍBRIDO) ---")
    
    CONFIG_FILE = "lab_config.json"
    
    # Inicialización de estado
    current_mode = "PHYSICS"
    is_paused = False
    last_mode = "PHYSICS"
    
    while True:
        # 1. Leer Configuración (Modo Estricto y Pausa)
        # Intentar leer varias veces para evitar condiciones de carrera
        for _ in range(5):
            try:
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r') as f:
                        content = f.read()
                        if content.strip():
                            config = json.loads(content)
                            new_mode = config.get("mode")
                            if new_mode in ["REAL", "PHYSICS"]:
                                current_mode = new_mode
                            is_paused = config.get("paused", is_paused)
                            break 
            except Exception:
                time.sleep(0.1)
        
        # Detectar cambio de modo y reiniciar estado
        if current_mode != last_mode:
            print(f"[*] Cambio de modo detectado: {last_mode} -> {current_mode}. Reiniciando estado...")
            results = [] # Limpiar memoria
            last_mode = current_mode
            # Opcional: Esperar un momento para asegurar que el dashboard haya limpiado el archivo
            time.sleep(1) 
            continue # Reiniciar bucle con nuevo modo limpio
        
        if is_paused:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Simulación PAUSADA...")
            time.sleep(2)
            continue
        
        results = []
        # Cargar histórico
        if os.path.exists(REPORT_FILE):
            try:
                with open(REPORT_FILE, 'r') as f:
                    content = f.read()
                    if content:
                        results = json.loads(content)
            except: pass

        # Ejecutar ronda de pruebas
        active_scenarios = random.sample(TARGET_GROUPS, k=random.randint(1, len(TARGET_GROUPS)))
        
        for group_name, suite in active_scenarios:
            data = None
            
            if current_mode == "REAL":
                # MODO REAL ESTRICTO: Solo Docker
                data = measure_handshake_real(group_name)
                if not data:
                    # Si falla, registramos el error explícitamente
                    data = {
                        "timestamp": datetime.now().isoformat(),
                        "algorithm": group_name,
                        "supported": False,
                        "negotiated_details": "ERROR: Conexión Docker Fallida",
                        "handshake_latency_ms": 0,
                        "phase1_key_share_bytes": 0,
                        "phase2_total_bytes": 0,
                        "phase2_fragmented": False,
                        "phase2_overhead_factor": 0,
                        "phase3_throughput_req_s": 0,
                        "source": "REAL_DOCKER_FAILED"
                    }
            else:
                # MODO FÍSICA ESTRICTO: Solo Motor
                data = measure_handshake_physics(group_name, suite)
            
            if data:
                results.append(data)
        
        # Mantener solo los últimos 2000 registros
        results = results[-2000:]
        
        # Mantener solo los últimos 2000 registros
        results = results[-2000:]
        
        # Guardar para que el Frontend lo lea
        try:
            with open(REPORT_FILE, 'w') as f:
                json.dump(results, f, indent=4)
                
            # DEBUG DUMP: Guardar copia cruda para el usuario
            with open("captures/debug_data_dump.json", "w") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "total_records": len(results),
                    "last_5_records": results[-5:]
                }, f, indent=4)
                
        except Exception as e:
            print(f"Error escribiendo JSON: {e}")
            
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo completado. Registros: {len(results)}")
        time.sleep(5) # Muestreo cada 5s

if __name__ == "__main__":
    main()
