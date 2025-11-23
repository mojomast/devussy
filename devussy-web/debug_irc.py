import subprocess
import sys
import json
import time
import socket

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.stderr.strip()}"

def check_container_status(container_name):
    print(f"Checking status of {container_name}...")
    status = run_command(f"sudo docker inspect -f '{{{{.State.Status}}}}' {container_name}")
    print(f"  Status: {status}")
    return status == "running"

def get_container_ip(container_name):
    ip = run_command(f"sudo docker inspect -f '{{{{range .NetworkSettings.Networks}}}}{{{{.IPAddress}}}}{{{{end}}}}' {container_name}")
    print(f"  IP: {ip}")
    return ip

def test_connectivity_from_nginx(target_host, target_port):
    print(f"Testing connectivity from Nginx to {target_host}:{target_port}...")
    cmd = f"sudo docker-compose exec nginx nc -zv {target_host} {target_port}"
    output = run_command(f"cd ~/devussy/devussy/devussy-web && {cmd}")
    print(f"  Result: {output}")

def test_dns_resolution_from_nginx(hostname):
    print(f"Testing DNS resolution for {hostname} from Nginx...")
    cmd = f"sudo docker-compose exec nginx getent hosts {hostname}"
    output = run_command(f"cd ~/devussy/devussy/devussy-web && {cmd}")
    print(f"  Result: {output}")

def test_websocket_handshake(ip, port):
    print(f"Testing WebSocket handshake to {ip}:{port} (from Host)...")
    # Simple manual HTTP request to simulate upgrade
    request = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {ip}:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"Origin: https://dev.ussy.host\r\n"
        f"\r\n"
    )
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, int(port)))
        s.sendall(request.encode())
        response = s.recv(4096).decode()
        s.close()
        print("  Response Headers:")
        print(response)
        if "101 Switching Protocols" in response:
            print("  SUCCESS: WebSocket handshake accepted!")
        else:
            print("  FAILURE: WebSocket handshake rejected.")
    except Exception as e:
        print(f"  ERROR: {e}")

def main():
    print("=== Devussy IRC Debugger ===")
    
    # 1. Check Containers
    if not check_container_status("devussy-ircd"):
        print("FATAL: IRCd container is not running.")
        return
    if not check_container_status("devussy-web-nginx-1"):
        print("FATAL: Nginx container is not running.")
        return

    # 2. Get IPs
    ircd_ip = get_container_ip("devussy-ircd")
    
    # 3. Test Nginx -> IRCd (Hostname)
    test_dns_resolution_from_nginx("devussy-ircd")
    test_connectivity_from_nginx("devussy-ircd", "8080")
    
    # 4. Test Nginx -> IRCd (IP)
    test_connectivity_from_nginx(ircd_ip, "8080")

    # 5. Test Host -> IRCd (Port 8080 mapped?)
    # Check if port is exposed
    ports = run_command("sudo docker port devussy-ircd 8080")
    print(f"  Host Port Mapping: {ports}")
    
    if ports and "0.0.0.0:8080" in ports:
        test_websocket_handshake("127.0.0.1", "8080")
    else:
        print("  Skipping Host handshake test (port 8080 not mapped to host)")

    print("\n=== End of Debug ===")

if __name__ == "__main__":
    main()
