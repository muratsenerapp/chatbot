# Multi-stage Dockerfile for Chatbot Application
# Includes: Frontend (React) + Backend (FastAPI) + Ollama (LLM Runtime)

# ================================
# Stage 1: Frontend Build
# ================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# ================================
# Stage 2: Final Image
# ================================
FROM ollama/ollama:latest

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    OLLAMA_HOST=0.0.0.0:11434 \
    BACKEND_PORT=8000 \
    FRONTEND_PORT=80

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3-pip \
    python3.12-venv \
    nginx \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# ================================
# Backend Setup
# ================================
WORKDIR /app/backend

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ ./

# ================================
# Frontend Setup
# ================================
# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# ================================
# Entrypoint Setup
# ================================
# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create Ollama data directory
RUN mkdir -p /root/.ollama

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${BACKEND_PORT}/api/health || exit 1

# Expose ports
# 80: Frontend (Nginx)
# 8000: Backend (FastAPI)
# 11434: Ollama API
EXPOSE 80 8000 11434

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
