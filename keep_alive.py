import os
from aiohttp import web
import socketio

# Create an instance of Socket.IO server
sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

# Serve the HTML page at the root route
async def index(request):
    with open("templates/index.html", "r") as file:
        return web.Response(text=file.read(), content_type="text/html")

# Define the WebSocket event to send status updates
@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")
    await sio.emit('status', {'status': 'Online'}, to=sid)  # Send initial status

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

# Function to update status
async def update_status(status):
    # Emit the new status to all connected clients
    await sio.emit('status', {'status': status})

# Run the keep-alive server
async def keep_alive():
    # Serving HTML and static files (you can add more routes if needed)
    app.router.add_get('/', index)

    # Start the server on a specific port
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Server started on port {port}")

# Function to simulate status changes (e.g., Online, Offline, Pinging)
async def simulate_status_changes():
    # Simulate some status changes
    await update_status('Pinging...')
    await asyncio.sleep(2)  # Wait for 2 seconds
    await update_status('Online')
    await asyncio.sleep(10)  # Wait for 10 seconds
    await update_status('Offline')

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()

    # Start the keep-alive server
    loop.create_task(keep_alive())

    # Simulate status changes
    loop.create_task(simulate_status_changes())

    loop.run_forever()
