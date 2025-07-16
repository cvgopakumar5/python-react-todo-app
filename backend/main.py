from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime
import uuid

app = FastAPI(title="Python React App", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# In-memory storage (replace with database in production)
items_db = {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, exclude_websocket: WebSocket = None):
        print(f"Broadcasting message to {len(self.active_connections)} connections")
        for i, connection in enumerate(self.active_connections):
            if connection != exclude_websocket:
                try:
                    await connection.send_text(message)
                    print(f"Message sent to connection {i+1}")
                except Exception as e:
                    print(f"Error sending to connection {i+1}: {e}")
                    # Remove broken connections
                    self.active_connections.remove(connection)

manager = ConnectionManager()

# Helper function to convert datetime to ISO string for JSON serialization
def item_to_dict(item: Item):
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "completed": item.completed,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat()
    }

# API Routes
@app.get("/")
async def root():
    return {"message": "Python React App Backend", "status": "running"}

@app.get("/api/items", response_model=List[Item])
async def get_items():
    return list(items_db.values())

@app.post("/api/items", response_model=Item)
async def create_item(item: ItemCreate):
    item_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_item = Item(
        id=item_id,
        title=item.title,
        description=item.description,
        completed=item.completed,
        created_at=now,
        updated_at=now
    )
    
    items_db[item_id] = new_item
    print(f"Created item: {item_id} - '{item.title}'")
    
    # Broadcast to all connected clients
    message = json.dumps({
        "type": "item_created",
        "item": item_to_dict(new_item)
    })
    await manager.broadcast(message)
    
    return new_item

@app.get("/api/items/{item_id}", response_model=Item)
async def get_item(item_id: str):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

@app.put("/api/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item: ItemCreate):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    existing_item = items_db[item_id]
    existing_item.title = item.title
    existing_item.description = item.description
    existing_item.completed = item.completed
    existing_item.updated_at = datetime.utcnow()
    
    # Broadcast to all connected clients
    message = json.dumps({
        "type": "item_updated",
        "item": item_to_dict(existing_item)
    })
    await manager.broadcast(message)
    
    return existing_item

@app.delete("/api/items/{item_id}")
async def delete_item(item_id: str):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    deleted_item = items_db.pop(item_id)
    
    # Broadcast to all connected clients
    message = json.dumps({
        "type": "item_deleted",
        "item_id": item_id
    })
    await manager.broadcast(message)
    
    return {"message": "Item deleted successfully"}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back the message (you can add custom logic here)
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 