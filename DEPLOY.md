# Lobby Server Deployment Guide

## Quick Start (Local Testing)

```bash
# Run the lobby server locally
python lobby_server.py

# The game connects to http://localhost:8080 by default
# Test with curl:
curl http://localhost:8080/health
curl http://localhost:8080/rooms
```

## Deploy to Render (Free)

1. Push your code to GitHub
2. Go to https://render.com and sign up (free)
3. Click "New" → "Web Service"
4. Connect your GitHub repo
5. Settings:
   - **Name**: `world11-lobby`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements-server.txt`
   - **Start Command**: `python lobby_server.py`
   - **Port**: 8080 (or leave default)
6. Click "Create Web Service"
7. Note your URL: `https://world11-lobby.onrender.com`

## Deploy to Railway (Free Trial)

1. Go to https://railway.app and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repo
4. Railway auto-detects Python and runs `python lobby_server.py`
5. Go to Settings → Networking → Generate Domain
6. Note your URL: `https://your-project.up.railway.app`

## Deploy to Fly.io (Free)

1. Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
2. In your project root, create `fly.toml`:

```toml
app = "world11-lobby"
primary_region = "iad"

[build]

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[checks]
  [checks.health]
    port = 8080
    type = "http"
    interval = "10s"
    timeout = "2s"
    path = "/health"
```

3. Run:
```bash
fly auth login
fly launch
fly deploy
```

4. Note your URL: `https://world11-lobby.fly.dev`

## Configure the Game to Use Your Server

### Option 1: Environment Variable
```bash
set WORLD11_LOBBY_URL=https://your-server.onrender.com
python main.py
```

### Option 2: Edit main.py
In `online_lobby()`, change the default:
```python
LOBBY_URL = os.environ.get("WORLD11_LOBBY_URL", "https://your-server.onrender.com")
```

## NAT / Port Forwarding Notes

**Important**: The lobby server only handles room discovery. The actual game
traffic is peer-to-peer. For this to work:

1. **The host** must have port 5150 (default) forwarded to their machine
2. **The joiner** connects directly to the host's public IP

### Port Forwarding Setup
1. Find your router's admin page (usually 192.168.1.1)
2. Add a port forwarding rule:
   - External port: 5150
   - Internal IP: your PC's local IP
   - Internal port: 5150
   - Protocol: TCP

### Testing
- Use https://www.yougetsignal.com/tools/open-ports/ to check if port 5150 is open
- If not open, port forwarding isn't configured correctly

## Architecture

```
Player A (Host)                Lobby Server              Player B (Joiner)
     |                              |                           |
     |--- POST /rooms ------------->|                           |
     |<-- {id, host_ip, port} ------|                           |
     |                              |                           |
     |                              |<--- GET /rooms -----------|
     |                              |---- [{room A}, ...] ----->|
     |                              |                           |
     |                              |<--- POST /rooms/.../join -|
     |                              |                           |
     |<--- TCP connect ---------------------------- -----------|
     |                              |                           |
     |<===== P2P Game Traffic (TCP) ===========================>|
```
