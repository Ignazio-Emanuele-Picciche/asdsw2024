import asyncio
import websockets

connected_clients = {}

chat_history = []

async def send_to_all(message):
    """
    Broadcasts a message to all connected clients.
    """
    if connected_clients:
        await asyncio.wait([client.send(message) for client in connected_clients])

async def send_chat_history(websocket):
    """
    Sends the entire chat history to a newly connected client.
    """
    for message in chat_history:
        await websocket.send(message)

async def send_user_list():
    """
    Broadcasts the list of currently connected users to all clients.
    """
    if connected_clients:
        user_list_message = "USERS:" + "," + ",".join(connected_clients.values())
        await asyncio.wait([client.send(user_list_message) for client in connected_clients])

async def chat_server(websocket, path):
    """
    Handles incoming WebSocket connections and chat messages.
    """
    try:
        await websocket.send("Please enter your username:")
        username = await websocket.recv()

        connected_clients[websocket] = username
        await send_chat_history(websocket) # delego l'invio della chat history al nuovo utente che si è collegato
        join_message = f"System: {username} has joined the chat."
        await send_to_all(join_message) # invia il nuovo messaggio 
        chat_history.append(join_message)

        await send_user_list()

        # programmazione asincrona
        async for message in websocket:
            chat_message = f"{username}: {message}"
            chat_history.append(chat_message)
            await send_to_all(chat_message)

    except websockets.ConnectionClosed:
        pass

    finally:
        leave_message = f"System: {username} has left the chat."
        connected_clients.pop(websocket, None)
        await send_to_all(leave_message)
        chat_history.append(leave_message)

        await send_user_list()

start_server = websockets.serve(chat_server, '0.0.0.0', 7000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

