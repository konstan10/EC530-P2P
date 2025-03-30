import asyncio
import sys
import sqlite3
from datetime import datetime

conn = False    # True if connected to server, false if not
reader = None   # Holds async reader
writer = None   # Holds async writer

"""Function to initialize database"""
def init_db():
    con = sqlite3.connect("messages.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS unsent_messages (
            username TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    con.commit()
    con.close()

"""Function to store message in database"""
def store_message(username, message, timestamp):
    con = sqlite3.connect("messages.db")
    cur = con.cursor()
    cur.execute("INSERT INTO unsent_messages (username, message, timestamp) VALUES (?, ?, ?)", (username, message, timestamp))
    con.commit()
    con.close()

"""Function to get all stored messages by username"""
def get_stored_messages(username):
    con = sqlite3.connect("messages.db")
    cur = con.cursor()
    cur.execute("SELECT username, message, timestamp FROM unsent_messages WHERE username = ?", (username,))
    messages = cur.fetchall()
    con.close()
    return messages

"""Function to delete all stored messages by username"""
def delete_stored_messages(username):
    con = sqlite3.connect("messages.db")
    cur = con.cursor()
    cur.execute("DELETE FROM unsent_messages WHERE username = ?", (username,))
    con.commit()
    con.close()

"""Function which attempts to connect to the server, retrying until successful"""
async def connect_with_retry(host, port, username, first_try):
    global reader, writer, conn
    if first_try:
        for _ in range(0, 3):
            try:
                reader, writer = await asyncio.open_connection(host, port)
                conn = True
                print(f"{username} connected to server.")
                return
            except (asyncio.TimeoutError, ConnectionRefusedError):
                print(f"{username} failed to connect to server. Retrying in 3 seconds...")
                await asyncio.sleep(3)
    else:
        while True:
            try:
                reader, writer = await asyncio.open_connection(host, port)
                print(f"\r{username} connected to server.\n> ", end="", flush=True)
                conn = True
                # Send messages stored in database, if there are any
                messages = get_stored_messages(username)
                if messages:
                    for _, unsent_message, unsent_timestamp in messages:
                        writer.write(f"[{unsent_timestamp}] {username}: {unsent_message}\n".encode("utf-8"))
                        await writer.drain()
                    delete_stored_messages(username)
                return
            except (asyncio.TimeoutError, ConnectionRefusedError):
                await asyncio.sleep(3)

async def client(host, port, username):
    global conn
    await connect_with_retry(host, port, username, first_try=True) # Connect to server

    """Send message to server if connected, store in database otherwise"""
    async def send_messages():
        global writer
        while True:
            message = await asyncio.to_thread(input, "> ")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if message.lower() == 'exit':
                writer.close()
                await writer.wait_closed()
                return
            if conn:
                writer.write(f"[{timestamp}] {username}: {message}".encode("utf-8"))
                await writer.drain()
            else:
                store_message(username, message, timestamp)

    """Receive message from server if connected, sleep otherwise"""
    async def receive_messages():
        global reader
        while True:
            if not conn:
                await asyncio.sleep(3)
            else:
                try:
                    response = await reader.read(1024)
                    if not response:
                        print("Disconnected from server.")
                        break
                    print(f"\r{response.decode('utf-8')}\n> ", end="", flush=True)
                except Exception:
                    break
    
    asyncio.create_task(receive_messages()) # Receive messages in background
    if not conn:
        print("Connection failed! Messages will be stored in a database.\n")
        asyncio.create_task(connect_with_retry(host, port, username, first_try=False))  # Try to connect to server in background

    await send_messages()

async def main(host, port, username):
    await client(host, port, username)

if __name__ == "__main__":
    host, port = sys.argv[1], int(sys.argv[2])
    username = input("Enter your username: ")
    init_db()
    asyncio.run(main(host, port, username))
