import socketio
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse
from pathlib import Path
import dataclasses
from typing import Literal
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI and SocketIO
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

sio = socketio.AsyncServer(async_mode='asgi')
app.mount('/ws', socketio.ASGIApp(sio, socketio_path='socket.io'))

# Directory where files will be stored
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@dataclasses.dataclass
class WatchedFile:
    path: str
    state: Literal["playing", "paused"]


watched_file = WatchedFile(path="file.txt", state="paused")


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_location = UPLOAD_DIR / file.filename

    # Save file locally
    with open(file_location, "wb") as f:
        f.write(file.file.read())

    watched_file.path = file_location

    # Return a URL for the uploaded file
    file_url = f"/files/{file.filename}"
    return JSONResponse(content={"file_url": file_url})


@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    return JSONResponse(content={"error": "File not found"}, status_code=404)


@app.post("/change-file/")
async def change_file_state(new_state: str):
    watched_file.state = new_state
    await sio.emit('file_state_changed', {'path': watched_file.path, 'state': watched_file.state})
    return JSONResponse(content={"message": "File state updated"})


@sio.event
async def connect(sid, environ):
    await sio.emit('file_state', {'path': watched_file.path, 'state': watched_file.state}, room=sid)


@sio.event
async def disconnect(sid):
    print('Client disconnected')


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
