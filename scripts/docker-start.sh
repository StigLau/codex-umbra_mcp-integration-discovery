#!/bin/bash

echo "🚀 Starting Codex Umbra with Docker..."

# Clean up any existing containers
docker-compose down

# Build and start services
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 15

# Show container status
echo "📊 Container Status:"
docker-compose ps

# Show logs for any failed containers
echo "📝 Recent logs:"
docker-compose logs --tail=10

# Run health checks
echo "🧪 Running health checks..."

# Test Sentinel
echo -n "Sentinel: "
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo "✅"
else
    echo "❌"
    echo "Sentinel logs:"
    docker-compose logs sentinel --tail=5
fi

# Test Conductor
echo -n "Conductor: "
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅"
else
    echo "❌"
    echo "Conductor logs:"
    docker-compose logs conductor --tail=5
fi

# Test Visage
echo -n "Visage: "
if curl -s http://localhost:5173 >/dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
    echo "Visage logs:"
    docker-compose logs visage --tail=5
fi

echo ""
echo "📋 Services:"
echo "  Sentinel: http://localhost:8001"
echo "  Conductor: http://localhost:8000"
echo "  Visage: http://localhost:5173"
echo ""
echo "📝 View logs: docker-compose logs -f [service-name]"
echo "📊 Check status: docker-compose ps"
echo "🛑 Stop: docker-compose down"
echo ""
echo "🔄 Containers will restart automatically unless stopped manually"
