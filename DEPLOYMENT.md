# Deployment Guide

This document provides guidance on deploying the Market Data Pipeline across different environments and orchestration platforms.

## Deployment Options

### 1. Local Development
Use the native Python setup with `uv` for rapid development.

```bash
uv sync
uv run uvicorn src.server:app --reload
```

### 2. Docker (Single Host)
Best for testing and small-scale deployments.

See [README.md](./README.md#using-docker) for Docker commands.

### 3. Docker Compose (Multi-Container)
Recommended for production on a single host or VM.

**Prerequisites:**
- Docker and Docker Compose installed
- Images built locally or pulled from registry

**Quick Deploy:**
```bash
# Start infrastructure
docker-compose up -d

# Run initial data load
docker-compose run --rm market-data-ingestion

# Scale API if needed
docker-compose up -d --scale market-data-api=3
```

See [docker-compose.md](./docker-compose.md) for detailed usage.

### 4. Kubernetes
For scalable, resilient deployments across multiple nodes.

**Prerequisites:**
- Kubernetes cluster (v1.21+)
- kubectl configured
- Container registry access
- Persistent storage class available

**Deployment Steps:**

1. **Update Secrets** (critical for production):
```bash
kubectl create secret generic market-data-secrets \
  --namespace=market-data \
  --from-literal=POSTGRES_PASSWORD=<secure-password> \
  --from-literal=DATABASE_URL=postgresql://postgres:<password>@postgres:5432/stocks_db
```

2. **Build and Push Images:**
```bash
# Tag images for your registry
docker tag market-data-api:001 your-registry/market-data-api:001
docker push your-registry/market-data-api:001
```

3. **Deploy with Kustomize:**
```bash
kubectl apply -k k8s/
```

4. **Verify Deployment:**
```bash
kubectl get all -n market-data
kubectl get pods -n market-data -w
```

4. **Verify API DATA:**
```bash
curl -k -H "Host: market-data.example.com" https://172.16.0.2:31668/prices/AAPL | jq
```

**Key Manifests:**
- `k8s/namespace.yaml` - Isolated namespace
- `k8s/postgres-deployment.yaml` - Database with PVC
- `k8s/api-deployment.yaml` - API with 2 replicas
- `k8s/ingestion-job.yaml` - CronJob for daily updates
- `k8s/ingress.yaml` - External access configuration

## Environment-Specific Configurations

### Development
- Use SQLite for testing (see conftest.py)
- Enable debug logging
- Disable replicas (set to 1)

### Staging
- Mirror production topology at reduced scale
- Use test datasets
- Enable monitoring but reduce retention

### Production
- Enable resource limits and requests
- Configure proper logging aggregation
- Set up monitoring and alerting
- Enable TLS/SSL for all communications
- Implement backup strategies for PostgreSQL
- Configure network policies for security

## Data Migration

### Initial Setup
1. Apply Kubernetes manifests or run docker-compose
2. Execute ingestion job to populate historical data
3. Verify data integrity with API queries

### Updates
- Database schema changes require migration scripts
- API version bumps need rolling updates
- Maintain backward compatibility during transitions

## Monitoring and Observability

### Health Checks
- `/health` endpoint for liveness/readiness
- PostgreSQL connection monitoring
- Ingestion job success tracking

### Metrics to Track
- API response times and error rates
- Database connection pool usage
- Data freshness (last ingestion timestamp)
- Resource utilization (CPU, memory)

### Logging
- Structured logging recommended
- Separate logs for API, ingestion, and database
- Centralized logging with ELK/EFK stack

## Backup and Recovery

### PostgreSQL Backups
```bash
# Manual backup
kubectl exec -it postgres-xxx -n market-data -- \
  pg_dump -U postgres stocks_db > backup.sql

# Automated with Velero or similar
```

### Disaster Recovery
1. Restore from latest backup
2. Re-run ingestion for missing data
3. Verify data consistency

## Security Considerations

1. **Secrets Management**
   - Never commit secrets to git
   - Use SealedSecrets or external secret operators
   - Rotate passwords regularly

2. **Network Security**
   - Restrict database access to application pods only
   - Use network policies
   - Enable TLS for external access

3. **Container Security**
   - Run as non-root user
   - Use read-only root filesystem where possible
   - Regular image vulnerability scanning

## Troubleshooting

### Common Issues

**Database Connection Failures**
- Verify service names in connection strings
- Check network policies and DNS resolution
- Confirm secrets are correctly mounted

**Ingestion Job Failures**
- Check yfinance API availability
- Verify database connectivity from job pods
- Review job logs: `kubectl logs job/<job-name> -n market-data`

**High Memory Usage**
- Adjust resource limits in deployments
- Consider implementing data retention policies
- Monitor DataFrame sizes in ingestion

### Debug Commands
```bash
# Pod logs
kubectl logs -f deployment/market-data-api -n market-data

# Database access
kubectl exec -it deployment/postgres -n market-data -- psql -U postgres

# API testing
kubectl port-forward svc/market-data-api 8000:80 -n market-data
curl http://localhost:8000/health
```

## Scaling Strategies

### Horizontal Scaling
- Increase API replicas based on load
- Consider read replicas for PostgreSQL
- Distribute ingestion across multiple tickers

### Vertical Scaling
- Adjust resource requests/limits based on metrics
- Monitor and right-size regularly

## CI/CD Integration

### Build Pipeline
1. Run tests in CI
2. Build Docker images
3. Security scanning
4. Push to registry
5. Update deployment manifests

### Deployment Pipeline
1. Apply manifests with kustomize
2. Wait for rollout completion
3. Run smoke tests
4. Update ingress if needed

## Support

For issues or questions:
- Review logs first
- Check this document for common scenarios
- Open issues in the project repository