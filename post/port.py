import scapy.all as scapy

# Порт для мониторинга
PORT = 25565

def packet_callback(packet):
    if packet.haslayer(scapy.IP):
        ip_layer = packet.getlayer(scapy.IP)
        src_ip = ip_layer.src
        dst_port = packet.sport if packet.haslayer(scapy.TCP) else packet.dport if packet.haslayer(scapy.UDP) else None
        
        if dst_port == PORT:
            protocol = "TCP" if packet.haslayer(scapy.TCP) else "UDP" if packet.haslayer(scapy.UDP) else "Unknown"
            print(f"Packet: {protocol} from IP: {src_ip}")

# Запуск захвата пакетов
scapy.sniff(filter=f"tcp port {PORT} or udp port {PORT}", prn=packet_callback, store=0)
