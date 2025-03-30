import asyncio
import sys

clients = set() # Set to store clients

"""Function to handle connected clients"""
async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"Accepted connection from {addr}")
    clients.add(writer)

    try:
        # If only one client connected, sleep and wait for more clients to connect
        while True:
            if len(clients) > 1:
                message = await reader.read(1024)
                if not message:
                    print(f"Closing connection to {addr}")
                    break

                decoded_message = message.decode('utf-8')
                print(f"Broadcasting: {decoded_message}")

                # Send message to all clients except sender
                for client in list(clients):
                    if client != writer:
                        try:
                            client.write(message)
                            await client.drain()
                        except Exception:
                            clients.remove(client)
            else:
                await asyncio.sleep(2)

    except asyncio.CancelledError:
        print(f"Connection to {addr} cancelled")

    finally:
        writer.close()
        await writer.wait_closed()
        clients.discard(writer)

async def main(host, port):
    server = await asyncio.start_server(handle_client, host, port)
    print(f"Listening on ('{host}', {port})")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    host, port = sys.argv[1], int(sys.argv[2])
    try:
        asyncio.run(main(host, port))
    except KeyboardInterrupt:
        print("Server shut down")
