import uvicorn
import socketio
from fastapi import FastAPI

app = FastAPI()

sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode='asgi')

socket_app = socketio.ASGIApp(sio)
app.mount("/ws", socket_app)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@sio.on("connect")
async def connect(sid, env):
    print("New Client Connected to This id :" + " " + str(sid))


@sio.on("disconnect")
async def disconnect(sid):
    print("Client Disconnected: " + " " + str(sid))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7777, lifespan="on", reload=True)
