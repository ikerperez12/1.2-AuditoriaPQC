# 📖 QuantumGuard: Documentación Técnica y Manual de Auditoría (v3.0)

**Proyecto:** Auditoría Integral de Migración a Criptografía Post-Cuántica (PQC) en Infraestructuras TLS 1.3
**Versión de Entrega:** 3.0 (Master Release)
**Fecha:** Diciembre 2025

---

## 📑 Índice de Contenidos

1.  **Fundamentos Estratégicos**
    *   La Amenaza Cuántica y el Problema HNDL
    *   Arquitectura "Harvest Now, Decrypt Later"
    *   La Solución NIST (FIPS 203/204)
2.  **Arquitectura del Laboratorio**
    *   Infraestructura Docker (Sonda Real)
    *   Entorno de Simulación (Physics Engine)
    *   Algoritmos Implementados (Kyber, Dilithium, Híbrido)
3.  **Manual de Operación**
    *   Modos de Ejecución (Real vs Physics)
    *   Controles de la Interfaz
4.  **Análisis Forense de Red (Deep Dive)**
    *   Anatomía de Cables y Fragmentación
    *   La Barrera de la MTU y Osificación
    *   Impacto de la Hibridación
    *   KEMTLS: La Arquitectura del Futuro
5.  **Dimensionamiento de Infraestructura (CAPEX/OPEX)**
    *   Sobrecarga del Kernel (Syscalls)
    *   Latencia Real vs Jitter (P99)
    *   Impacto Energético y Costes Cloud
6.  **Guía de Interpretación del Dashboard**
    *   Métricas de Riesgo (Factor de Amplificación)
    *   Indicadores de Rendimiento
7.  **Conclusión Final**

---

## 1. Fundamentos Estratégicos

### 1.1. Contexto: La Crisis Criptográfica
La seguridad actual de Internet (RSA, Curvas Elípticas) basa su robustez en problemas matemáticos (Factorización, Logaritmo Discreto) que los Ordenadores Cuánticos (CRQC) resolverán trivialmente mediante el **Algoritmo de Shor**. Esto implica que toda comunicación cifrada hoy será legible mañana.

### 1.2. Amenaza HNDL (Harvest Now, Decrypt Later)
Aunque los CRQC comerciales pueden tardar una década, el riesgo es inmediato debido a la estrategia adversaria **"Cosechar Ahora, Descifrar Después"**.
*   **Mecánica**: Actores estatales capturan y almacenan tráfico cifrado hoy (2025).
*   **Ejecución**: En el "Día Q" (estimado ~2030), usarán ordenadores cuánticos para descifrar retrospectivamente secretos de larga vida útil (Secretos de Estado, Propiedad Intelectual, Datos Genéticos).
*   **Mitigación**: La única defensa es implementar PQC **ahora** para el intercambio de claves.

### 1.3. Estándares NIST
El proyecto implementa los estándares finalistas del NIST:
*   **ML-KEM (Kyber)**: Para intercambio de claves (Confidencialidad).
*   **ML-DSA (Dilithium)**: Para firmas digitales (Autenticación/Integridad).

---

## 2. Arquitectura del Laboratorio

### 2.1. Infraestructura Docker (Sonda Real)
El núcleo del proyecto es una red virtual aislada (`pqc_lab_net`) gestionada por Docker Compose.
*   **Servidor (`pqc_server`)**: Nginx compilado con **OQS-OpenSSL** (Open Quantum Safe). Emite certificados PQC auto-firmados.
*   **Sonda (`pqc_client`)**: Contenedor Curl/OpenSSL que inyecta tráfico controlado y mide el handshake TLS 1.3 real.

### 2.2. Algoritmos Implementados
Evaluamos tres escenarios de migración:

| Escenario | Composición Técnica | Seguridad | Impacto en Red |
| :--- | :--- | :--- | :--- |
| **Clásico** | X25519 (ECDH) | Tradicional (Vulnerable) | Mínimo (282 Bytes) |
| **Híbrido** | X25519 + ML-KEM-768 | "Cinturón y Tirantes" | Medio (1434 Bytes) |
| **PQC Puro** | ML-KEM + ML-DSA | Post-Cuántica Completa | Crítico (15 KB+) |

---

## 3. Manual de Operación

### 3.1. Modos de Ejecución
El laboratorio opera en dos modos seleccionables desde la interfaz:

1.  **MODO PHYSICS (Simulación)**:
    *   Utiliza un motor matemático en Python (`pqc_engine.py`) con constantes FIPS.
    *   **Uso**: Proyectar escenarios teóricos ideales sin ruido de red ("Clean Room").

2.  **MODO REAL (Laboratorio Docker)**:
    *   Inyecta comandos `openssl s_client` reales.
    *   **Uso**: Validar el comportamiento del software, medir tiempos de negociación reales y detectar incompatibilidades.

### 3.2. Controles
*   **Filtro de Alcance**: Permite aislar analíticas por algoritmo (ej. ver solo Híbrido).
*   **Reseteo**: Purga el archivo de capturas `real_scan_results.json` para reiniciar auditorías.

---

## 4. Análisis Forense de Red (WireLab)

Esta sección disecciona el impacto físico de los nuevos tamaños de clave en la infraestructura existente.

### 4.1. Eficiencia Clásica (Línea Base)
Un handshake X25519 ocupa **~282 Bytes**. Cabe holgadamente en un solo segmento TCP, garantizando latencia mínima (1-RTT) y cero riesgo de fragmentación.

### 4.2. El Desafío Híbrido: La Barrera MTU
El escenario Híbrido (1434 Bytes) roza peligrosamente la MTU Ethernet (1500 Bytes).
*   **Riesgo de Osificación**: En redes corporativas, el encapsulamiento extra (VLAN +4B, MPLS +4B, IPsec +50B) puede hacer que el paquete supere los 1500 bytes, provocando fragmentación o descarte por middleboxes antiguos.

### 4.3. PQC Puro: Saturación y Fragmentación
El uso de certificados **Dilithium** (~4KB) dispara el tamaño de respuesta del servidor a **~15 KB**.
*   **Saturación IW10**: Excede la Ventana de Congestión Inicial de TCP (~14KB). El servidor entra en estado *Stop-and-Wait*, esperando ACKs y añadiendo latencia.
*   **Fallo Compuesto (Composite Failure)**: Al depender de ~10 fragmentos, la probabilidad de fallo se dispara.
    $$ P_{total} = 1 - (1 - P_{loss})^N $$
    Con 1% de pérdida de red, un handshake PQC tiene **~10-14%** de probabilidad de fallo, causando retransmisiones masivas.

### 4.4. El Futuro: KEMTLS (Optimización)
Como solución arquitectónica, el laboratorio evalúa **KEMTLS**, un mecanismo experimental que elimina las firmas digitales (Dilithium) del handshake.
*   **Impacto**: Reduce el tamaño de ~15KB a **~4KB**.
*   **Resultado**: Elimina la fragmentación crítica, volviendo a valores seguros para redes IoT/Edge.

---

## 5. Dimensionamiento de Infraestructura (Negocio)

Migrar a PQC no es solo una actualización de software; tiene costes físicos y financieros.

### 5.1. Sobrecarga del Kernel (Syscalls)
La fragmentación obliga al Kernel (Linux) a realizar más trabajo de ensamblado.
*   **Syscalls**: Aumentan de 2 a **8 llamadas de E/S** por conexión.
*   **Densidad**: Un servidor que soportaba 2,500 conn/s en Clásico, cae a **450 conn/s** en PQC Puro. Esto implica la necesidad de escalar la flota de servidores **x5**.

### 5.2. Estabilidad y Jitter (P99)
Aunque la latencia media suba poco, la **Latencia de Cola (P99)** se dispara de 40ms a **250ms** debido a las retransmisiones TCP, degradando la experiencia de usuario (UX) en redes móviles.

### 5.3. Costes Financieros (OPEX)
*   **Cloud Egress**: El coste de ancho de banda se multiplica por **~24x** (un aumento del 2400%).
*   **Energía**: El consumo energético por millón de conexiones sube un **+75%** debido al coste computacional de verificar retículos.
*   **Memoria (OOM)**: Los buffers de recepción crecen de 40KB a **180KB** por socket, aumentando el riesgo de agotar la RAM bajo carga.

---

## 6. Guía de Interpretación del Dashboard

El panel principal actúa como un "Single Pane of Glass" para la auditoría.

### 6.1. Factor de Amplificación (Riesgo DDoS)
*   **Definición**: Ratio entre tamaño de respuesta y tamaño de petición.
*   **Valor PQC**: **14.8x** (vs 9.5x Clásico).
*   **Alerta**: Un atacante puede usar servidores PQC para amplificar ataques DDoS, enviando peticiones pequeñas que generan respuestas gigantescas hacia la víctima.

### 6.2. Gráfico de Latencia Temporal
Permite visualizar la estabilidad de la red. Una línea PQC con muchos "picos" indica problemas de congestión TCP o pérdida de paquetes, validando la teoría de la fragmentación.

---

## 7. Conclusión Final

El laboratorio **QuantumGuard** demuestra empíricamente que la migración a criptografía Post-Cuántica es **técnicamente segura pero operacionalmente costosa**.

**Recomendaciones para el despliegue:**
1.  Adoptar inmediatamente el modelo **Híbrido** (X25519+Kyber) para mitigar HNDL con impacto mínimo.
2.  Preparar la infraestructura (escalado x5, presupuesto de red) antes de activar PQC Puro (Autenticación).
3.  Monitorizar de cerca el **Jitter** y la **Fragmentación** en los firewalls corporativos.
