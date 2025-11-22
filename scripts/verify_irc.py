import asyncio
import websockets
import sys

async def test_irc_connection():
    uri = "ws://localhost:8080"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket Gateway!")
            
            # Send IRC handshake
            nick = "DevussyTester"
            print(f"Sending NICK {nick}...")
            await websocket.send(f"NICK {nick}\r\n")
            await websocket.send(f"USER {nick} 0 * :Devussy Tester\r\n")
            
            # Wait for response
            print("Waiting for response...")
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"Received: {message.strip()}")
                    
                    # Check for welcome message (001) or any sign of life
                    if "001" in message:
                        print("\nSUCCESS: Received Welcome Message (RPL_WELCOME)!")
                        return True
                    if "433" in message:
                         print("\nSUCCESS: Server responded (Nickname in use), connection is working.")
                         return True
                    if "PING" in message:
                         await websocket.send(f"PONG {message.split()[1]}\r\n")
            except asyncio.TimeoutError:
                print("\nTimed out waiting for welcome message. Server might be slow or misconfigured.")
                return False
                
    except ConnectionRefusedError:
        print("\nERROR: Connection Refused. Is the Docker container running?")
        print("Run: docker-compose up -d irc-server irc-gateway")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_irc_connection())
    sys.exit(0 if success else 1)
