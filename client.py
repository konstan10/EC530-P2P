import asyncio
import sys

messages = [b"Hello", b"World"]

async def client(host, port, connid):
    # Establish connection with server
    reader, writer = await asyncio.open_connection(host, port)
    print(f"Connection {connid} established.")

    for message in messages:
        print(f"Sending {message.decode('utf-8')} from connection {connid}")
        # Write message to server and make sure it's sent completely
        writer.write(message)
        await writer.drain()

        # Read message back from server
        response = await reader.read(1024)
        print(f"Received {response.decode('utf-8')} in connection {connid}")

    print(f"Closing connection {connid}")
    # Close connection
    writer.close()
    await writer.wait_closed()

async def main(host, port, num_conns):
    # Initialize client for each connection and run them concurrently
    conns = []
    for i in range(num_conns):
        conns.append(client(host, port, i + 1))
    await asyncio.gather(*conns)

if __name__ == "__main__":
    host, port, num_conns = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    asyncio.run(main(host, port, num_conns))
