#!/bin/bash
# FusionEMS Self-Hosted AI Installation
# Run this on your existing DigitalOcean backend droplet
# Installs Ollama + models without affecting your FastAPI backend

set -e

echo "=========================================="
echo "FusionEMS Self-Hosted AI Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${BLUE}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo -e "${GREEN}✓ Docker already installed${NC}"
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${BLUE}Starting Docker daemon...${NC}"
    systemctl start docker
    systemctl enable docker
fi

# Create persistent volume for Ollama models
echo -e "${BLUE}Creating Docker volume for Ollama models...${NC}"
docker volume create ollama-models || echo "Volume already exists"

# Pull Ollama image (lightweight)
echo -e "${BLUE}Pulling Ollama Docker image...${NC}"
docker pull ollama/ollama:latest

# Run Ollama container
# - Port 11434: Ollama API (internal only, not exposed to internet for security)
# - Volume: persistent storage for downloaded models
# - Memory limit: 6GB (leaves room for your FastAPI backend)
echo -e "${BLUE}Starting Ollama container...${NC}"
docker run -d \
  --name ollama \
  --restart always \
  -p 127.0.0.1:11434:11434 \
  -e OLLAMA_HOST=0.0.0.0:11434 \
  -v ollama-models:/root/.ollama \
  --memory="6g" \
  --cpus="3" \
  ollama/ollama

echo -e "${GREEN}✓ Ollama container started${NC}"

# Wait for Ollama to be ready
echo -e "${BLUE}Waiting for Ollama to be ready...${NC}"
sleep 5

# Check if Ollama is responding
max_attempts=10
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://127.0.0.1:11434/api/status > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama API is responding${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "Waiting for Ollama... ($attempt/$max_attempts)"
    sleep 2
done

# Download models (in background, can take a while)
echo -e "${BLUE}Downloading AI models (this may take 10-20 minutes)...${NC}"
echo "Models will be stored in: /var/lib/docker/volumes/ollama-models/_data"
echo ""

# Model 1: Mistral (4GB) - Best for narrative generation
echo -e "${BLUE}[1/3] Downloading Mistral (narrative generation)...${NC}"
docker exec ollama ollama pull mistral

# Model 2: Neural-Chat (3.3GB) - Fast, real-time suggestions
echo -e "${BLUE}[2/3] Downloading Neural-Chat (field suggestions)...${NC}"
docker exec ollama ollama pull neural-chat

# Model 3: Dolphin-Mixtral (13GB) - Advanced medical coding
echo -e "${BLUE}[3/3] Downloading Dolphin-Mixtral (complex reasoning)...${NC}"
docker exec ollama ollama pull dolphin-mixtral

echo ""
echo -e "${GREEN}=========================================="
echo "✓ Ollama Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Models installed:"
docker exec ollama ollama list
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Ollama API URL: http://127.0.0.1:11434"
echo "  Memory allocated: 6GB"
echo "  CPU cores allocated: 3"
echo "  Storage location: /var/lib/docker/volumes/ollama-models/_data"
echo ""
echo -e "${BLUE}Update your FusionEMS config:${NC}"
echo ""
echo "  # In /root/fusonems-quantum-v2/backend/services/ai/self_hosted_ai.py"
echo "  class SelfHostedAIConfig:"
echo "      OLLAMA_SERVER_URL = \"http://127.0.0.1:11434\"  # Local only"
echo ""
echo -e "${BLUE}Test the connection:${NC}"
echo "  curl http://127.0.0.1:11434/api/tags"
echo ""
echo -e "${BLUE}Monitor Ollama:${NC}"
echo "  docker logs -f ollama"
echo "  docker stats ollama"
echo ""
echo -e "${GREEN}✓ Ready to use!${NC}"
