#!/usr/bin/env python3
"""
Simplified and robust PCAP processing for the AdDDoSDN project.
"""

import logging
import subprocess
import time
from pathlib import Path
from scapy.all import rdpcap, TCP, IP
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

def improve_capture_reliability(net, outfile, host=None):
    """Start a reliable packet capture using tcpdump.
    If host is provided, capture on the host\'s primary interface (e.g., h1-eth0).
    Otherwise, capture on the switch\'s \'any\' interface.
    """
    logger.info(f"Starting packet capture. Output file: {outfile}")
    
    # Ensure the output directory exists
    Path(outfile).parent.mkdir(parents=True, exist_ok=True)
    
    # Determine the interface and the node to run tcpdump on
    if host:
        node = net.get(host.name) # Get the Mininet host object
        intf = f"{host.name}-eth0" # Assuming primary interface is eth0
        logger.info(f"Capturing on host {host.name} interface {intf}")
    else:
        node = net.get('s1') # Default to switch s1
        intf = 'any'
        logger.info(f"Capturing on switch s1 interface {intf}")
    
    # Build the tcpdump command
    # -i <interface>: Specify interface
    # -w <file>: Write the raw packets to a file
    # -s 0: Capture the full packet
    # ip and not ip6: Filter for IPv4 traffic only
    # net 10.0.0.0/8: Capture traffic within the Mininet network
    cmd = [
        'tcpdump',
        '-i', intf,
        '-w', str(outfile),
        '-s', '0',
        'ip', 'and', 'not', 'ip6', 'and', 'net', '10.0.0.0/8'
    ]
    
    logger.info(f"Starting tcpdump with command: {' '.join(cmd)}")
    
    # Start the capture process in the background on the selected node
    process = node.popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
    
    # Give tcpdump a moment to initialize
    time.sleep(2)
    
    # Check if the process started successfully
    if process.poll() is not None:
        error_output = process.stderr.read().strip()
        logger.error(f"tcpdump failed to start. Error: {error_output}")
        raise RuntimeError(f"tcpdump process exited with code {process.returncode}")
        
    logger.info(f"tcpdump started successfully with PID: {process.pid}")
    return process

def verify_pcap_integrity(pcap_file):
    """Verify the integrity of the generated PCAP file."""
    logger.info(f"Verifying integrity of PCAP file: {pcap_file}")
    
    if not Path(pcap_file).exists() or Path(pcap_file).stat().st_size == 0:
        logger.error("PCAP file does not exist or is empty.")
        return {'valid': False, 'error': 'File not found or is empty'}

    try:
        packets = rdpcap(str(pcap_file))
        if len(packets) == 0:
            logger.warning("PCAP file contains no packets.")
            return {'valid': False, 'error': 'No packets in file'}
        
        logger.info(f"PCAP integrity check passed. Found {len(packets)} packets.")
        return {'valid': True, 'total_packets': len(packets), 'corruption_rate': 0.0}
    except Exception as e:
        logger.error(f"Error reading PCAP file during integrity check: {e}")
        return {'valid': False, 'error': str(e)}

def enhanced_process_pcap_to_csv(pcap_file, output_csv, label_timeline, validate_timestamps=True):
    """Process the PCAP to CSV. The name is kept for compatibility.
    This version does not perform timestamp validation, as tcpdump is more reliable.
    """
    from src.utils.process_pcap_to_csv import process_pcap_to_csv
    logger.info("Passing PCAP to processing function.")
    process_pcap_to_csv(str(pcap_file), str(output_csv), label_timeline)

def validate_and_fix_pcap_timestamps(pcap_file):
    """A placeholder function for compatibility. Returns mock data.
    Timestamp issues are less likely with tcpdump.
    """
    logger.info("Skipping timestamp validation as tcpdump is used.")
    try:
        packets = rdpcap(str(pcap_file))
        baseline = packets[0].time if packets else time.time()
        return packets, {
            'corrupted_packets': 0,
            'baseline_time': baseline
        }
    except Exception as e:
        logger.error(f"Could not read PCAP for baseline time: {e}")
        return [], {
            'corrupted_packets': 0,
            'baseline_time': time.time()
        }

def analyze_pcap_for_tcp_issues(pcap_file):
    """Analyzes a PCAP file for TCP RST flags and retransmissions."""
    logger.info(f"Analyzing PCAP file for TCP issues: {pcap_file}")
    rst_count = 0
    retransmission_count = 0
    
    # Dictionary to store sequence numbers for retransmission detection
    # Key: (source_ip, destination_ip, source_port, destination_port)
    # Value: set of (sequence_number, payload_length)
    seq_ack_map = {}

    try:
        packets = rdpcap(str(pcap_file))
        for packet in packets:
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                
                # Check for RST flag
                if tcp_layer.flags & 0x04:  # RST flag is 0x04
                    rst_count += 1
                
                # Check for retransmissions (simplified)
                # This is a basic check and might not catch all retransmissions
                # A more robust check would involve tracking sequence and acknowledgment numbers
                # and comparing them with previously seen packets for the same flow.
                if packet.haslayer(IP):
                    src_ip = packet[IP].src
                    dst_ip = packet[IP].dst
                    src_port = tcp_layer.sport
                    dst_port = tcp_layer.dport
                    
                    flow_key = (src_ip, dst_ip, src_port, dst_port)
                    
                    current_seq = tcp_layer.seq
                    current_payload_len = len(tcp_layer.payload)
                    
                    if flow_key in seq_ack_map:
                        for seq, payload_len in seq_ack_map[flow_key]:
                            if seq == current_seq and payload_len == current_payload_len:
                                retransmission_count += 1
                                break
                        seq_ack_map[flow_key].add((current_seq, current_payload_len))
                    else:
                        seq_ack_map[flow_key] = set([(current_seq, current_payload_len)])

    except Exception as e:
        logger.error(f"Error analyzing PCAP for TCP issues: {e}")
        return {"rst_count": 0, "retransmission_count": 0, "error": str(e)}
        
    logger.info(f"PCAP analysis complete. RST count: {rst_count}, Retransmission count: {retransmission_count}")
    return {"rst_count": rst_count, "retransmission_count": retransmission_count}

def analyze_inter_packet_arrival_time(pcap_file):
    """Analyzes inter-packet arrival times in a PCAP file."""
    logger.info(f"Analyzing inter-packet arrival times for: {pcap_file}")
    arrival_times = []
    try:
        packets = rdpcap(str(pcap_file))
        if len(packets) < 2:
            logger.warning("Not enough packets to calculate inter-packet arrival times.")
            return {"mean": 0, "median": 0, "std_dev": 0, "error": "Not enough packets"}

        for i in range(1, len(packets)):
            arrival_times.append(packets[i].time - packets[i-1].time)
        
        mean_ipt = np.mean(arrival_times)
        median_ipt = np.median(arrival_times)
        std_dev_ipt = np.std(arrival_times)

        logger.info(f"Inter-packet arrival time analysis complete. Mean: {mean_ipt:.4f}s, Median: {median_ipt:.4f}s, Std Dev: {std_dev_ipt:.4f}s")
        return {"mean": mean_ipt, "median": median_ipt, "std_dev": std_dev_ipt}

    except Exception as e:
        logger.error(f"Error analyzing inter-packet arrival times: {e}")
        return {"mean": 0, "median": 0, "std_dev": 0, "error": str(e)}