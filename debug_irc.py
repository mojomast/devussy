import socket
import sys
import time
import argparse

def debug_irc(host, port):
    print(f"Connecting to {host}:{port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((host, port))
        print("Connected!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Send handshake
    nick = "debug_user"
    user = "debug_user"
    realname = "Debug User"
    
    # Standard IRC handshake
    # PASS is optional, but some servers require it. We'll skip it for now unless needed.
    # s.sendall(b"PASS somepassword\r\n")
    
    print(f"Sending NICK {nick}")
    s.sendall(f"NICK {nick}\r\n".encode('utf-8'))
    
    print(f"Sending USER {user} 0 * :{realname}")
    s.sendall(f"USER {user} 0 * :{realname}\r\n".encode('utf-8'))

    # Listen for response
    buffer = b""
    while True:
        try:
            data = s.recv(4096)
            if not data:
                print("Connection closed by server.")
                break
            
            buffer += data
            while b"\r\n" in buffer:
                line, buffer = buffer.split(b"\r\n", 1)
                decoded_line = line.decode('utf-8', errors='replace')
                print(f"RECV: {decoded_line}")
                
                # Handle PING to keep connection alive if we get that far
                if decoded_line.startswith("PING"):
                    pong_response = decoded_line.replace("PING", "PONG", 1)
                    print(f"SEND: {pong_response}")
                    s.sendall(f"{pong_response}\r\n".encode('utf-8'))
                    
        except socket.timeout:
            print("Timeout waiting for data.")
            break
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            break

    s.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Debug IRC connection.')
    parser.add_argument('host', nargs='?', default='localhost', help='IRC server host')
    parser.add_argument('port', nargs='?', default=6667, type=int, help='IRC server port')
    
    args = parser.parse_args()
    
    debug_irc(args.host, args.port)
