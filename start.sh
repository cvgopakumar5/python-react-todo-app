#!/bin/bash

echo "🚀 Starting Python React Full-Stack App with MySQL..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down

# Build and start all services
echo "📦 Building and starting services..."
docker-compose up --build -d

echo "✅ All services are starting..."
echo "🌐 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🗄️  MySQL: localhost:3309"
echo ""
echo "📊 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
echo ""
echo "Waiting for services to be ready..."

# Wait for services to be ready
sleep 10

# Show logs
echo "📋 Recent logs:"
docker-compose logs --tail=20

echo ""
echo "🎉 Your app is ready! Press Ctrl+C to stop viewing logs"
echo "The app will continue running in the background."

# Follow logs
docker-compose logs -f 