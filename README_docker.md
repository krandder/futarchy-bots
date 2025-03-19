# Docker Setup for Futarchy Bots

This repository includes Docker configuration for running both the Python application and the Uniswap V3 JavaScript bridge in containers.

## Prerequisites

- Docker
- Docker Compose

## Files

- `docker-compose.yml` - Defines the services and their configuration
- `Dockerfile.python` - Dockerfile for the Python application
- `js-bridges/uniswap-v3-bridge/Dockerfile` - Dockerfile for the Uniswap V3 JavaScript bridge

## Environment Variables

### Python Application

Environment variables for the Python application are defined in:
- `.env` file (for local development)
- `Dockerfile.python` (for Docker)

Key variables:
- `UNISWAP_V3_BRIDGE_URL`: URL to connect to the Uniswap V3 bridge service
- `RPC_URL`: RPC URL for connecting to the Gnosis Chain
- `PRIVATE_KEY`: Private key for signing transactions (optional)

### Uniswap V3 Bridge

Environment variables for the Uniswap V3 bridge are defined in:
- `js-bridges/uniswap-v3-bridge/.env` file (for local development)
- Docker Compose environment section (for Docker)

Key variables:
- `RPC_URL`: RPC URL for connecting to the Gnosis Chain
- `PORT`: Port on which the bridge API will run (default: 3001)

## Building and Running

### Build the Images

```bash
docker-compose build
```

### Start the Services

```bash
docker-compose up
```

To run in detached mode:

```bash
docker-compose up -d
```

### Stop the Services

```bash
docker-compose down
```

## Accessing the Services

- Python Application: Runs in interactive mode by default
- Uniswap V3 Bridge: API accessible at http://localhost:3001

## Running Specific Commands

To run a specific command in the Python application:

```bash
docker-compose run python-app python main.py monitor --iterations 10 --interval 30
```

Available commands:
- `interactive`: Run in interactive mode (default)
- `monitor`: Run monitoring strategy
- `probability`: Run probability threshold strategy
- `arbitrage`: Run arbitrage strategy

## Logs

To view logs:

```bash
docker-compose logs
```

To follow logs:

```bash
docker-compose logs -f
```

To view logs for a specific service:

```bash
docker-compose logs python-app
docker-compose logs uniswap-v3-bridge
``` 