#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Chatbot Application - Docker Container${NC}"
echo -e "${GREEN}================================================${NC}"

# Function to handle shutdown
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill -TERM "$OLLAMA_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
    wait "$OLLAMA_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
    echo -e "${GREEN}Shutdown complete${NC}"
    exit 0
}

trap cleanup SIGTERM SIGINT

# ================================
# 1. Start Ollama Service
# ================================
echo -e "${GREEN}[1/4] Starting Ollama service...${NC}"
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo -e "${YELLOW}Waiting for Ollama to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Ollama failed to start${NC}"
        exit 1
    fi
    sleep 1
done

# ================================
# 2. Pull/Check Ollama Model
# ================================
echo -e "${GREEN}[2/4] Checking Ollama model...${NC}"
MODEL_NAME="qwen2.5:7b-instruct"

if ollama list | grep -q "$MODEL_NAME"; then
    echo -e "${GREEN}✓ Model '$MODEL_NAME' is already available${NC}"
else
    echo -e "${YELLOW}Model '$MODEL_NAME' not found. Pulling model...${NC}"
    echo -e "${YELLOW}This may take several minutes (model size: ~4.7GB)${NC}"
    ollama pull "$MODEL_NAME"
    echo -e "${GREEN}✓ Model '$MODEL_NAME' pulled successfully${NC}"
fi

# ================================
# 3. Start Backend (FastAPI)
# ================================
echo -e "${GREEN}[3/4] Starting FastAPI backend...${NC}"
cd /app/backend
python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info &
BACKEND_PID=$!

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
for i in {1..20}; do
    if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 20 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        exit 1
    fi
    sleep 1
done

# ================================
# 4. Start Nginx (Frontend)
# ================================
echo -e "${GREEN}[4/4] Starting Nginx frontend...${NC}"
nginx -g "daemon off;" &
NGINX_PID=$!

# Wait for nginx to be ready
sleep 2
if curl -s http://localhost:80/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Nginx is ready${NC}"
else
    echo -e "${YELLOW}⚠ Nginx health check failed, but continuing...${NC}"
fi

# ================================
# All services started
# ================================
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  All services started successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Frontend:  http://localhost:80${NC}"
echo -e "${GREEN}  Backend:   http://localhost:8000${NC}"
echo -e "${GREEN}  Ollama:    http://localhost:11434${NC}"
echo -e "${GREEN}================================================${NC}"

# Keep container running and wait for any process to exit
wait -n "$OLLAMA_PID" "$BACKEND_PID" "$NGINX_PID"

# If any process exits, trigger cleanup
cleanup
