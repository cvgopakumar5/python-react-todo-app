# Python React Full-Stack App

A simple full-stack application with Python FastAPI backend and React frontend.

## Project Structure

```
python_react/
├── backend/          # Python FastAPI backend
├── frontend/         # React frontend
├── README.md         # This file
└── docker-compose.yml # Docker setup (optional)
```

## Features

- **Backend**: FastAPI with automatic API documentation
- **Frontend**: React with modern UI components
- **Real-time**: WebSocket support for live updates
- **Database**: SQLite for simplicity (can be upgraded to PostgreSQL)

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## API Endpoints

- `GET /` - Health check
- `GET /api/items` - Get all items
- `POST /api/items` - Create new item
- `GET /api/items/{id}` - Get specific item
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item

## Development

The backend runs on `http://localhost:8000` and the frontend on `http://localhost:3000`. 