import time
import logging
import subprocess
from pathlib import Path
from scapy.all import Ether, IP, TCP, UDP, Raw, RandShort, sendp
import random
import os

# Import standardized logging
try:
    from .utils.logger import get_benign_logger
except ImportError:
    from utils.logger import get_benign_logger



def run_benign_traffic(net, duration, output_dir, host_ips):
    """
    Generates various types of benign traffic (ICMP, TCP, UDP, Telnet, SSH, FTP, HTTP, HTTPS, DNS)
    between h3 and h5 in the Mininet network.
    """
    # Get standardized logger
    benign_logger = get_benign_logger(Path(output_dir))
    
    benign_logger.info(f"Starting benign traffic for {duration} seconds...")
    h3 = net.get('h3')
    h5 = net.get('h5')
    h3_ip = host_ips["h3"]
    h5_ip = host_ips["h5"]
    h3_intf = h3.intfNames()[0] # Get the interface name of h3
    h5_intf = h5.intfNames()[0] # Get the interface name of h5
    end_time = time.time() + duration

    def generate_random_payload(min_len=50, max_len=1500):
        length = random.randint(min_len, max_len)
        return os.urandom(length) # Generate random bytes

    traffic_count = 0
    session_count = 0
    packet_count = 0
    while time.time() < end_time:
        # ICMP traffic (using Mininet's ping command)
        h3.cmd(f'ping -c 1 {h5_ip} > /dev/null')
        h5.cmd(f'ping -c 1 {h3_ip} > /dev/null')
        # Standard ICMP echo request is 84 bytes
        benign_logger.debug(f"Generated ICMP traffic {traffic_count} [len=84B]")
        packet_count += 2 # For ping and pong

        # Scapy commands to be executed within h3's namespace
        scapy_base_cmd = "from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, Raw, RandShort, sendp, sr1;"

        # TCP traffic (h3 to h5, port 12345) with handshake and random payload/length
        sport_tcp = random.randint(1024, 65535)
        dport_tcp = 12345
        
        # SYN from h3 to h5
        syn_scapy_cmd = f"syn_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_tcp}, dport={dport_tcp}, flags='S', seq=RandShort()); sendp(syn_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{syn_scapy_cmd}"')
        benign_logger.debug(f"Generated TCP SYN from h3:{sport_tcp} -> h5:{dport_tcp} [len=54B]")
        packet_count += 1
        time.sleep(0.01) # Small delay for SYN-ACK

        # SYN-ACK from h5 to h3 (simulated)
        synack_scapy_cmd = f"synack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_tcp}, dport={sport_tcp}, flags='SA', seq=RandShort(), ack=RandShort()); sendp(synack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{synack_scapy_cmd}"')
        benign_logger.debug(f"Generated TCP SYN-ACK from h5:{dport_tcp} <- h3:{sport_tcp} [len=54B]")
        packet_count += 1
        time.sleep(0.01) # Small delay for ACK

        # ACK from h3 to h5
        ack_scapy_cmd = f"ack_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_tcp}, dport={dport_tcp}, flags='A', seq=RandShort(), ack=RandShort()); sendp(ack_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{ack_scapy_cmd}"')
        benign_logger.debug(f"Generated TCP ACK from h3:{sport_tcp} -> h5:{dport_tcp} [len=54B]")
        packet_count += 1
        time.sleep(0.01) # Small delay before data

        # PSH, ACK with random payload
        random_payload_tcp = generate_random_payload()
        payload_len = len(random_payload_tcp)
        tcp_payload_hex = random_payload_tcp.hex()
        packet_len = 54 + payload_len
        tcp_scapy_cmd = f"tcp_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_tcp}, dport={dport_tcp}, flags='PA', seq=RandShort(), ack=RandShort())/Raw(load=bytes.fromhex('{tcp_payload_hex}')); sendp(tcp_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{tcp_scapy_cmd}"')
        benign_logger.debug(f"Generated TCP data traffic from h3:{sport_tcp} -> h5:{dport_tcp} [content='TCP data'] [Session {session_count + 1}] [len={packet_len}B]")
        packet_count += 1

        # Simple ACK reply from h5 to h3 for the data packet
        h5_ack_scapy_cmd = f"h5_ack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_tcp}, dport={sport_tcp}, flags='A', seq=RandShort(), ack=RandShort()); sendp(h5_ack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{h5_ack_scapy_cmd}"')
        benign_logger.debug(f"Generated TCP ACK reply from h5:{dport_tcp} <- h3:{sport_tcp} [len=54B]")
        packet_count += 1
        session_count += 1


        # UDP traffic (h3 to h5, port 12346) with random payload/length
        sport_udp = random.randint(1024, 65535)
        dport_udp = 12346
        random_payload_udp = generate_random_payload()
        payload_len = len(random_payload_udp)
        udp_payload_hex = random_payload_udp.hex()
        packet_len = 42 + payload_len # 14 Ether + 20 IP + 8 UDP
        udp_scapy_cmd = f"udp_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/UDP(sport={sport_udp}, dport={dport_udp})/Raw(load=bytes.fromhex('{udp_payload_hex}')); sendp(udp_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{udp_scapy_cmd}"')
        benign_logger.debug(f"Generated UDP traffic from h3:{sport_udp} -> h5:{dport_udp} [content='{random_payload_udp[:20].hex()}...'] [Session {session_count + 1}] [len={packet_len}B]")
        packet_count += 1
        session_count += 1

        # Telnet traffic (h3 to h5, port 23) with handshake and random payload/length
        sport_telnet = random.randint(1024, 65535)
        dport_telnet = 23
        
        # SYN from h3 to h5
        syn_scapy_cmd = f"syn_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_telnet}, dport={dport_telnet}, flags='S', seq=RandShort()); sendp(syn_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{syn_scapy_cmd}"')
        benign_logger.debug(f"Generated Telnet SYN from h3:{sport_telnet} -> h5:{dport_telnet} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # SYN-ACK from h5 to h3 (simulated)
        synack_scapy_cmd = f"synack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_telnet}, dport={sport_telnet}, flags='SA', seq=RandShort(), ack=RandShort()); sendp(synack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{synack_scapy_cmd}"')
        benign_logger.debug(f"Generated Telnet SYN-ACK from h5:{dport_telnet} <- h3:{sport_telnet} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # ACK from h3 to h5
        ack_scapy_cmd = f"ack_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_telnet}, dport={dport_telnet}, flags='A', seq=RandShort(), ack=RandShort()); sendp(ack_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{ack_scapy_cmd}"')
        benign_logger.debug(f"Generated Telnet ACK from h3:{sport_telnet} -> h5:{dport_telnet} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # PSH, ACK with random payload
        random_payload_telnet = generate_random_payload()
        payload_len = len(random_payload_telnet)
        telnet_payload_hex = random_payload_telnet.hex()
        packet_len = 54 + payload_len
        telnet_scapy_cmd = f"telnet_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_telnet}, dport={dport_telnet}, flags='PA', seq=RandShort(), ack=RandShort())/Raw(load=bytes.fromhex('{telnet_payload_hex}')); sendp(telnet_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{telnet_scapy_cmd}"')
        benign_logger.debug(f"Generated Telnet data traffic from h3:{sport_telnet} -> h5:{dport_telnet} [content='Telnet command'] [Session {session_count + 1}] [len={packet_len}B]")
        packet_count += 1

        # Simple ACK reply from h5 to h3 for the data packet
        h5_ack_scapy_cmd = f"h5_ack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_telnet}, dport={sport_telnet}, flags='A', seq=RandShort(), ack=RandShort()); sendp(h5_ack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{h5_ack_scapy_cmd}"')
        benign_logger.debug(f"Generated Telnet ACK reply from h5:{dport_telnet} <- h3:{sport_telnet} [len=54B]")
        packet_count += 1
        session_count += 1

        # SSH traffic (h3 to h5, port 22) with handshake and random payload/length
        sport_ssh = random.randint(1024, 65535)
        dport_ssh = 22
        
        # SYN from h3 to h5
        syn_scapy_cmd = f"syn_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_ssh}, dport={dport_ssh}, flags='S', seq=RandShort()); sendp(syn_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{syn_scapy_cmd}"')
        benign_logger.debug(f"Generated SSH SYN from h3:{sport_ssh} -> h5:{dport_ssh} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # SYN-ACK from h5 to h3 (simulated)
        synack_scapy_cmd = f"synack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_ssh}, dport={sport_ssh}, flags='SA', seq=RandShort(), ack=RandShort()); sendp(synack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{synack_scapy_cmd}"')
        benign_logger.debug(f"Generated SSH SYN-ACK from h5:{dport_ssh} <- h3:{sport_ssh} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # ACK from h3 to h5
        ack_scapy_cmd = f"ack_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_ssh}, dport={dport_ssh}, flags='A', seq=RandShort(), ack=RandShort()); sendp(ack_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{ack_scapy_cmd}"')
        benign_logger.debug(f"Generated SSH ACK from h3:{sport_ssh} -> h5:{dport_ssh} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # PSH, ACK with random payload
        random_payload_ssh = generate_random_payload()
        payload_len = len(random_payload_ssh)
        ssh_payload_hex = random_payload_ssh.hex()
        packet_len = 54 + payload_len
        ssh_scapy_cmd = f"ssh_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_ssh}, dport={dport_ssh}, flags='PA', seq=RandShort(), ack=RandShort())/Raw(load=bytes.fromhex('{ssh_payload_hex}')); sendp(ssh_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{ssh_scapy_cmd}"')
        benign_logger.debug(f"Generated SSH data traffic from h3:{sport_ssh} -> h5:{dport_ssh} [content='SSH encrypted data'] [Session {session_count + 1}] [len={packet_len}B]")
        packet_count += 1

        # Simple ACK reply from h5 to h3 for the data packet
        h5_ack_scapy_cmd = f"h5_ack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_ssh}, dport={sport_ssh}, flags='A', seq=RandShort(), ack=RandShort()); sendp(h5_ack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{h5_ack_scapy_cmd}"')
        benign_logger.debug(f"Generated SSH ACK reply from h5:{dport_ssh} <- h3:{sport_ssh} [len=54B]")
        packet_count += 1
        session_count += 1

        # FTP traffic (h3 to h5, port 21) with handshake and random payload/length
        sport_ftp = random.randint(1024, 65535)
        dport_ftp = 21
        
        # SYN from h3 to h5
        syn_scapy_cmd = f"syn_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_ftp}, dport={dport_ftp}, flags='S', seq=RandShort()); sendp(syn_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{syn_scapy_cmd}"')
        benign_logger.debug(f"Generated FTP SYN from h3:{sport_ftp} -> h5:{dport_ftp} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # SYN-ACK from h5 to h3 (simulated)
        synack_scapy_cmd = f"synack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_ftp}, dport={sport_ftp}, flags='SA', seq=RandShort(), ack=RandShort()); sendp(synack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{synack_scapy_cmd}"')
        benign_logger.debug(f"Generated FTP SYN-ACK from h5:{dport_ftp} <- h3:{sport_ftp} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # ACK from h3 to h5
        ack_scapy_cmd = f"ack_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_ftp}, dport={dport_ftp}, flags='A', seq=RandShort(), ack=RandShort()); sendp(ack_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{ack_scapy_cmd}"')
        benign_logger.debug(f"Generated FTP ACK from h3:{sport_ftp} -> h5:{dport_ftp} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # PSH, ACK with random payload
        random_payload_ftp = generate_random_payload()
        payload_len = len(random_payload_ftp)
        ftp_payload_hex = random_payload_ftp.hex()
        packet_len = 54 + payload_len
        ftp_scapy_cmd = f"ftp_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_ftp}, dport={dport_ftp}, flags='PA', seq=RandShort(), ack=RandShort())/Raw(load=bytes.fromhex('{ftp_payload_hex}')); sendp(ftp_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{ftp_scapy_cmd}"')
        benign_logger.debug(f"Generated FTP data traffic from h3:{sport_ftp} -> h5:{dport_ftp} [content='FTP file transfer'] [Session {session_count + 1}] [len={packet_len}B]")
        packet_count += 1

        # Simple ACK reply from h5 to h3 for the data packet
        h5_ack_scapy_cmd = f"h5_ack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_ftp}, dport={sport_ftp}, flags='A', seq=RandShort(), ack=RandShort()); sendp(h5_ack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{h5_ack_scapy_cmd}"')
        benign_logger.debug(f"Generated FTP ACK reply from h5:{dport_ftp} <- h3:{sport_ftp} [len=54B]")
        packet_count += 1
        session_count += 1

        # HTTP traffic (h3 to h5, port 80) with handshake and random payload/length
        sport_http = random.randint(1024, 65535)
        dport_http = 80
        
        # SYN from h3 to h5
        syn_scapy_cmd = f"syn_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_http}, dport={dport_http}, flags='S', seq=RandShort()); sendp(syn_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{syn_scapy_cmd}"')
        benign_logger.debug(f"Generated HTTP SYN from h3:{sport_http} -> h5:{dport_http} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # SYN-ACK from h5 to h3 (simulated)
        synack_scapy_cmd = f"synack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_http}, dport={sport_http}, flags='SA', seq=RandShort(), ack=RandShort()); sendp(synack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{synack_scapy_cmd}"')
        benign_logger.debug(f"Generated HTTP SYN-ACK from h5:{dport_http} <- h3:{sport_http} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # ACK from h3 to h5
        ack_scapy_cmd = f"ack_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_http}, dport={dport_http}, flags='A', seq=RandShort(), ack=RandShort()); sendp(ack_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{ack_scapy_cmd}"')
        benign_logger.debug(f"Generated HTTP ACK from h3:{sport_http} -> h5:{dport_http} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # PSH, ACK with random payload
        http_payload = generate_random_payload(min_len=100, max_len=500)
        http_headers = f"GET /index.html HTTP/1.1\r\nHost: {h5_ip}\r\nUser-Agent: ScapyBenignTraffic\r\nContent-Length: {len(http_payload)}\r\n\r\n"
        http_raw_payload = http_headers.encode('utf-8') + http_payload
        http_raw_payload_hex = http_raw_payload.hex()
        packet_len = 54 + len(http_raw_payload)
        http_scapy_cmd = f"http_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_http}, dport={dport_http}, flags='PA', seq=RandShort(), ack=RandShort())/Raw(load=bytes.fromhex('{http_raw_payload_hex}')); sendp(http_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{http_scapy_cmd}"')
        benign_logger.debug(f"Generated HTTP data traffic from h3:{sport_http} -> h5:{dport_http} [content='GET /index.html HTTP/1.1'] [Session {session_count + 1}] [len={packet_len}B]")
        packet_count += 1

        # Simple ACK reply from h5 to h3 for the data packet
        h5_ack_scapy_cmd = f"h5_ack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_http}, dport={dport_http}, flags='A', seq=RandShort(), ack=RandShort()); sendp(h5_ack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{h5_ack_scapy_cmd}"')
        benign_logger.debug(f"Generated HTTP ACK reply from h5:{dport_http} <- h3:{sport_http} [len=54B]")
        packet_count += 1
        session_count += 1

        # HTTPS traffic (h3 to h5, port 443) with handshake and random payload/length
        sport_https = random.randint(1024, 65535)
        dport_https = 443
        
        # SYN from h3 to h5
        syn_scapy_cmd_https = f"syn_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_https}, dport={dport_https}, flags='S', seq=RandShort()); sendp(syn_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{syn_scapy_cmd_https}"')
        benign_logger.debug(f"Generated HTTPS SYN from h3:{sport_https} -> h5:{dport_https} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # SYN-ACK from h5 to h3 (simulated)
        synack_scapy_cmd_https = f"synack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_https}, dport={dport_https}, flags='SA', seq=RandShort(), ack=RandShort()); sendp(synack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{synack_scapy_cmd_https}"')
        benign_logger.debug(f"Generated HTTPS SYN-ACK from h5:{dport_https} <- h3:{sport_https} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # ACK from h3 to h5
        ack_scapy_cmd_https = f"ack_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_https}, dport={dport_https}, flags='A', seq=RandShort(), ack=RandShort()); sendp(ack_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{ack_scapy_cmd_https}"')
        benign_logger.debug(f"Generated HTTPS ACK from h3:{sport_https} -> h5:{dport_https} [len=54B]")
        packet_count += 1
        time.sleep(0.01)

        # PSH, ACK with random payload (simulating encrypted data)
        https_payload = generate_random_payload(min_len=150, max_len=800)
        payload_len = len(https_payload)
        https_payload_hex = https_payload.hex()
        packet_len = 54 + payload_len
        https_scapy_cmd = f'''https_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/TCP(sport={sport_https}, dport={dport_https}, flags='PA', seq=RandShort(), ack=RandShort())/Raw(load=bytes.fromhex('{https_payload_hex}')); sendp(https_packet, iface='{h3_intf}', verbose=0)'''
        h3.cmd(f'python3 -c "{scapy_base_cmd}{https_scapy_cmd}"')
        benign_logger.debug(f"Generated HTTPS data traffic from h3:{sport_https} -> h5:{dport_https} [content='Encrypted Application Data'] [Session {session_count + 1}] [len={packet_len}B]")
        packet_count += 1

        # Simple ACK reply from h5 to h3 for the data packet
        h5_ack_scapy_cmd_https = f"h5_ack_packet = Ether()/IP(src='{h5_ip}', dst='{h3_ip}')/TCP(sport={dport_https}, dport={dport_https}, flags='A', seq=RandShort(), ack=RandShort()); sendp(h5_ack_packet, iface='{h5_intf}', verbose=0)"
        h5.cmd(f'python3 -c "{scapy_base_cmd}{h5_ack_scapy_cmd_https}"')
        benign_logger.debug(f"Generated HTTPS ACK reply from h5:{dport_https} <- h3:{sport_https} [len=54B]")
        packet_count += 1
        session_count += 1

        # DNS query (h3 to h5, port 53)
        sport_dns = random.randint(1024, 65535)
        dport_dns = 53
        qname = 'example.com'
        # Packet length: 14 (Ether) + 20 (IP) + 8 (UDP) + 29 (DNS) = 71 bytes
        packet_len = 71
        dns_scapy_cmd = f"dns_packet = Ether()/IP(src='{h3_ip}', dst='{h5_ip}')/UDP(sport={sport_dns}, dport={dport_dns})/DNS(rd=1, qd=DNSQR(qname='{qname}')); sendp(dns_packet, iface='{h3_intf}', verbose=0)"
        h3.cmd(f'python3 -c "{scapy_base_cmd}{dns_scapy_cmd}"')
        benign_logger.debug(f"Generated DNS query from h3:{sport_dns} -> h5:{dport_dns} [qname='{qname}'] [Session {session_count + 1}] [len={packet_len}B]")
        packet_count += 1
        session_count += 1
        
        traffic_count += 1
        time.sleep(0.1) # Send traffic every 100ms
    
    benign_logger.info("Benign traffic finished.")
    benign_logger.info(f"Summary: {session_count} protocol sessions [ICMP, TCP, UDP, Telnet, SSH, FTP, HTTP, HTTPS, DNS], {packet_count} packets sent.")
