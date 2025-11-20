#!/usr/bin/env bash
set -euo pipefail

# Minimal setup for Ubuntu 22.04
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker "$USER"

# Install Docker Compose (if not using Docker Compose v2 built-in)
if ! command -v docker-compose >/dev/null 2>&1; then
  sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
fi

# Install NGINX
sudo apt-get install -y nginx

echo "setup complete; log out and back in to activate the docker group membership"
