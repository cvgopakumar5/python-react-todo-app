from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

# Import database and models
from database import get_db, engine
from models import Base, Item as ItemModel

# Create database tables
Base.metadata.create_all(bind=engine)

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
def item_to_dict(item: ItemModel):
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
async def get_items(db: Session = Depends(get_db)):
    items = db.query(ItemModel).all()
    return items

@app.post("/api/items", response_model=Item)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = ItemModel(
        id=str(uuid.uuid4()),
        title=item.title,
        description=item.description,
        completed=item.completed
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    print(f"Created item: {db_item.id} - '{item.title}'")
    
    # Broadcast to all connected clients
    message = json.dumps({
        "type": "item_created",
        "item": item_to_dict(db_item)
    })
    await manager.broadcast(message)
    
    return db_item

@app.get("/api/items/{item_id}", response_model=Item)
async def get_item(item_id: str, db: Session = Depends(get_db)):
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/api/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db_item.title = item.title
    db_item.description = item.description
    db_item.completed = item.completed
    db_item.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_item)
    
    # Broadcast to all connected clients
    message = json.dumps({
        "type": "item_updated",
        "item": item_to_dict(db_item)
    })
    await manager.broadcast(message)
    
    return db_item

@app.delete("/api/items/{item_id}")
async def delete_item(item_id: str, db: Session = Depends(get_db)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(db_item)
    db.commit()
    
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