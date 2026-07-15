# Docker Compose Guide

This document provides detailed instructions for using Docker Compose with the Market Data Pipeline.

## Overview

Docker Compose manages the multi-container setup including PostgreSQL database and the API service. Test and ingestion tasks run as one-off containers rather than persistent services.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- Images built with version tags (see Quick Start below)

## Quick Start Commands

### 1. Build All Images
```bash
docker build --target tester -t market-data-test:001 .
docker build --target server -t market-data-api:001 .
docker build --target ingestion -t market-data-ingestion:001 .
```

### 2. Start Infrastructure
```bash
docker-compose up -d
```

This command:
- Creates the `market-data-network` network
- Starts PostgreSQL with persistent volume
- Starts the market-data-api service
- Waits for health checks to pass

### 3. Run One-off Tasks

#### Data Ingestion
```bash
docker-compose run --rm market-data-ingestion
```

The `--rm` flag ensures the container is removed after completion.

#### Run Tests
```bash
docker-compose run --rm market-data-test
```

Test output will be streamed to the console.

### 4. Monitor and Debug

#### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f market-data-api

# Last 100 lines
docker-compose logs --tail=100
```

#### Check Service Status
```bash
docker-compose ps
```

#### Execute Commands in Running Container
```bash
docker-compose exec postgres psql -U postgres -d stocks_db
```

### 5. Stop Services

#### Stop but Keep Containers
```bash
docker-compose stop
```

#### Stop and Remove Containers
```bash
docker-compose down
```

#### Remove Everything Including Volumes
```bash
docker-compose down -v
```

**Warning:** This will delete all market data in PostgreSQL.

## Configuration

### Environment Variables

Override defaults in `docker-compose.yml`:
```yaml
environment:
  - DATABASE_URL=postgresql://user:pass@host:5432/db
```

Or use an `.env` file:
```bash
# .env file
DATABASE_URL=postgresql://postgres:mysecretpassword@postgres:5432/stocks_db
```

### Network Configuration

All services join the `market-data-network` bridge network:
- `postgres:5432` - Database accessible by service name
- `market-data-api:8000` - API accessible on host port 8000

### Volume Persistence

- `pgdata`: PostgreSQL data directory
- Location: Docker-managed volume (inspect with `docker volume inspect`)

## Service Health Checks

PostgreSQL includes health checks ensuring dependent services wait for database readiness:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 5s
  timeout: 5s
  retries: 5
```

## Common Issues

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Or change port in docker-compose.yml
ports:
  - "8080:8000"  # Map host 8080 to container 8000
```

### Database Connection Errors
Ensure the DATABASE_URL uses the service name `postgres` not `localhost`.

### Permission Issues on Volume
Docker manages volume permissions. If issues persist:
```bash
docker-compose down -v
docker-compose up -d
```

## Production Considerations

For production deployments:
1. Use `docker-compose.prod.yml` with resource limits
2. Add reverse proxy (nginx/traefik)
3. Configure proper logging drivers
4. Set restart policies
5. Use secrets management for passwords

Example production override:
```yaml
# docker-compose.prod.yml
services:
  postgres:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  market-data-api:
    restart: always
    deploy:
      replicas: 3
```