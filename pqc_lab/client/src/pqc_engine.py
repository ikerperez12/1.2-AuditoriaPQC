import time
import math

# --- CONSTANTS ---
MAX_MSS = 1460
IW10_LIMIT = 14600

class FIPS_SPECS:
    class X25519:
        pk = 32
        sig = 64 # EdDSA signature size approx
    
    class ML_KEM_768:
        pk = 1184
        ct = 1088
    
    class ML_DSA_65:
        pk = 1952
        sig = 3293
    
    CERT_OVERHEAD = 800 # Metadata overhead per cert

class CryptoSuite:
    CLASSIC = "CLASSIC"
    HYBRID = "HYBRID"
    PURE = "PURE"

# --- CRYPTO ENGINE ---

def compute_workload(complexity):
    """
    Simulates CPU cost by running real mathematical operations.
    Returns the time taken in milliseconds.
    """
    start = time.perf_counter()
    result = 0.0
    # Iterations scaled for Python (slower than JS V8, so we adjust factor)
    # JS factor was 10000. Python is ~10-50x slower for raw loops.
    # We'll use 500 to get comparable millisecond delays without freezing too long.
    iterations = int(complexity * 500) 
    
    for i in range(iterations):
        # Math operations to consume CPU cycles
        result = (result + math.sqrt(i) * math.tan(i)) % 123456
        
    end = time.perf_counter()
    return (end - start) * 1000 # Convert to ms

def run_crypto_engine(suite):
    keygen_time = 0
    encaps_time = 0
    verify_time = 0
    
    client_key_share_size = 0
    server_key_share_size = 0
    signature_size = 0
    cert_chain_size = 0
    
    if suite == CryptoSuite.CLASSIC:
        # X25519
        keygen_time = compute_workload(0.5)
        encaps_time = compute_workload(0.5)
        verify_time = compute_workload(1.0)
        
        client_key_share_size = FIPS_SPECS.X25519.pk
        server_key_share_size = FIPS_SPECS.X25519.pk
        signature_size = FIPS_SPECS.X25519.sig
        cert_chain_size = 2500
        
    elif suite == CryptoSuite.HYBRID:
        # X25519 + ML-KEM-768
        keygen_time = compute_workload(0.5 + 2.0)
        encaps_time = compute_workload(0.5 + 2.0)
        verify_time = compute_workload(1.0)
        
        client_key_share_size = FIPS_SPECS.X25519.pk + FIPS_SPECS.ML_KEM_768.pk
        server_key_share_size = FIPS_SPECS.X25519.pk + FIPS_SPECS.ML_KEM_768.ct
        signature_size = FIPS_SPECS.X25519.sig
        cert_chain_size = 2500
        
    else: # PURE
        # ML-KEM-768 + ML-DSA-65
        keygen_time = compute_workload(2.0)
        encaps_time = compute_workload(2.0)
        verify_time = compute_workload(5.0)
        
        client_key_share_size = FIPS_SPECS.ML_KEM_768.pk
        server_key_share_size = FIPS_SPECS.ML_KEM_768.ct
        signature_size = FIPS_SPECS.ML_DSA_65.sig
        
        single_cert_size = FIPS_SPECS.ML_DSA_65.pk + FIPS_SPECS.ML_DSA_65.sig + FIPS_SPECS.CERT_OVERHEAD
        cert_chain_size = single_cert_size * 3
        
    # Protocol Overhead
    client_payload = 200 + client_key_share_size
    server_payload = 250 + server_key_share_size + cert_chain_size + signature_size
    
    return {
        "keygen_time_ms": keygen_time,
        "encaps_time_ms": encaps_time,
        "verify_time_ms": verify_time,
        "client_payload_size": client_payload,
        "server_payload_size": server_payload,
        "key_share_size": client_key_share_size # For dashboard Phase 1
    }

# --- NETWORK PHYSICS ENGINE ---

def run_network_simulation(suite, rtt_ms, bandwidth_mbps=100):
    crypto = run_crypto_engine(suite)
    
    # Segmentation
    client_segments = math.ceil(crypto["client_payload_size"] / MAX_MSS)
    server_segments = math.ceil(crypto["server_payload_size"] / MAX_MSS)
    
    # Congestion Window Analysis (RFC 6928)
    exceeds_iw10 = crypto["server_payload_size"] > IW10_LIMIT
    
    # Deterministic RTT Calculation
    required_rtts = 1 # TCP Handshake
    
    # TLS Handshake usually 1-RTT, but if server flight > IW10, add 1 RTT (Stop-and-Wait)
    if exceeds_iw10:
        required_rtts += 1
        
    # Transmission Time
    total_bytes = crypto["client_payload_size"] + crypto["server_payload_size"]
    transmission_time_ms = (total_bytes * 8) / (bandwidth_mbps * 1_000_000) * 1000
    
    # Total Latency
    # Base RTT (TCP) + Handshake RTTs + CPU + Transmission
    total_latency_ms = rtt_ms + (required_rtts * rtt_ms) + \
                       (crypto["keygen_time_ms"] + crypto["encaps_time_ms"] + crypto["verify_time_ms"]) + \
                       transmission_time_ms
                       
    return {
        "suite": suite,
        "metrics": crypto,
        "mtu": 1500,
        "mss": MAX_MSS,
        "client_segments": client_segments,
        "server_segments": server_segments,
        "server_flight_bytes": crypto["server_payload_size"],
        "iw10_limit": IW10_LIMIT,
        "exceeds_iw10": exceeds_iw10,
        "required_rtts": required_rtts,
        "total_latency_ms": total_latency_ms,
        "fragmentation_risk": client_segments > 1,
        "amplification_factor": round(crypto["server_payload_size"] / crypto["client_payload_size"], 1)
    }
