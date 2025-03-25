import asyncio
import sys

async def handle_client(reader, writer):
    # Get IP addr and port from client
    addr = writer.get_extra_info('peername')
    print(f"Accepted connection from {addr}")

    try:
        while True:
            # Read message from client
            message = await reader.read(1024)
            if not message:
                # Writer closed from client side, break loop to close connection 
                print(f"Closing connection to {addr}")
                break

            print(f"Received {message.decode('utf-8')} from {addr}")
            # Write message back and make sure it's sent completely
            writer.write(message)
            await writer.drain()

    except asyncio.CancelledError:
        print(f"Connection to {addr} cancelled")
    
    finally:
        # Close connection
        writer.close()
        await writer.wait_closed()

async def main(host, port):
    # Start server
    server = await asyncio.start_server(handle_client, host, port)
    print(f"Listening on ('{host}', {port})")

    # Keep server running indefinitely
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    host, port = sys.argv[1], int(sys.argv[2])
    try:
        asyncio.run(main(host, port))
    except KeyboardInterrupt:
        print("Server shut down")