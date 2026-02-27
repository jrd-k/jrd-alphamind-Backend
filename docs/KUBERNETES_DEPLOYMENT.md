# Kubernetes Deployment Guide

Complete step-by-step instructions for deploying AlphaMind to Kubernetes with secure WebSocket authentication, AI dashboard analytics, automatic backups, and monitoring.

## Prerequisites

- A Kubernetes cluster (EKS, GKE, AKS, or self-hosted 1.20+)
- `kubectl` configured and connected to your cluster
- `helm` 3.x installed
- Domain name with DNS control
- ~50GB storage available for databases and backups
- At least 3 worker nodes with 2 CPU and 4GB RAM each

## Quick Start (5 minutes)

```bash
# Clone and navigate to the repository
git clone https://github.com/jrd-k/jrd-alphamind-Backend.git
cd jrd-alphamind-Backend

# Run the automated deployment script
export DOMAIN=alphamind.yourdomain.com
export REGION=us-east-1
bash scripts/deploy-k8s.sh

# Monitor the deployment
kubectl get pods -n alphamind -w
```

## Manual Deployment (Detailed)

### Step 1: Create Namespace

```bash
kubectl create namespace alphamind
kubectl label namespace alphamind name=alphamind
```

### Step 2: Install Required Infrastructure

#### Install cert-manager (for SSL certificates):
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
```

#### Install ingress-nginx:
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

### Step 3: Create Storage

```bash
kubectl apply -f k8s/05-storage.yaml

# Verify PVCs are created
kubectl get pvc -n alphamind
```

### Step 4: Configure Secrets

```bash
# Create PostgreSQL credentials
kubectl create secret generic postgres-credentials \
  --from-literal=username=postgres \
  --from-literal=password=YOUR_STRONG_PASSWORD \
  --from-literal=database=alphamind \
  -n alphamind

# Create application secrets
kubectl create secret generic alphamind-secrets \
  --from-literal=JWT_SECRET=$(openssl rand -hex 32) \
  --from-literal=DATABASE_URL="postgresql://alphamind:YOUR_PASSWORD@postgres:5432/alphamind" \
  --from-literal=REDIS_URL="redis://redis:6379/0" \
  --from-literal=DEEPSEEK_API_KEY=your_api_key \
  --from-literal=OPENAI_API_KEY=your_api_key \
  --from-literal=EXNESS_API_KEY=your_api_key \
  -n alphamind
```

### Step 5: Deploy Stateful Services

#### Deploy PostgreSQL HA:
```bash
kubectl apply -f k8s/01-postgres-ha.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n alphamind --timeout=600s
```

#### Deploy Redis:
```bash
kubectl apply -f k8s/03-redis.yaml
kubectl wait --for=condition=ready pod -l app=redis -n alphamind --timeout=300s
```

### Step 6: Deploy Application

```bash
kubectl apply -f k8s/02-backend-deployment.yaml
kubectl wait --for=condition=ready pod -l app=backend -n alphamind --timeout=300s

# Check logs
kubectl logs -n alphamind -l app=backend -f
```

### Step 7: Deploy Monitoring

```bash
kubectl apply -f k8s/04-monitoring.yaml
```

### Step 8: Configure Networking & SSL

```bash
# Apply ingress, network policies, and secrets management
kubectl apply -f k8s/07-ingress-and-networking.yaml
kubectl apply -f k8s/08-secrets-management.yaml

# Update ingress domain
kubectl patch ingress alphamind-ingress -n alphamind --type='json' \
  -p='[{"op": "replace", "path": "/spec/rules/0/host", "value":"api.alphamind.yourdomain.com"}]'
```

### Step 9: Schedule Backups

```bash
kubectl apply -f k8s/06-backup-cronjobs.yaml

# Check backup jobs
kubectl get cronjob -n alphamind
kubectl get jobs -n alphamind
```

## Verification

### Check All Services

```bash
# Pods
kubectl get pods -n alphamind

# Services
kubectl get svc -n alphamind

# Ingress
kubectl get ingress -n alphamind

# Get LoadBalancer IP
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

### Test Application Health

```bash
# Get backend pod name
POD=$(kubectl get pods -n alphamind -l app=backend -o jsonpath='{.items[0].metadata.name}')

# Test health endpoint
kubectl exec -it $POD -n alphamind -- curl http://localhost:8000/health

# View logs
kubectl logs $POD -n alphamind -f
```

### Access Monitoring

Once the LoadBalancer gets an external IP:

- **Prometheus**: https://prometheus.alphamind.yourdomain.com
- **Grafana**: https://grafana.alphamind.yourdomain.com (default password: admin)
- **API**: https://api.alphamind.yourdomain.com
- **WebSocket**: wss://api.alphamind.yourdomain.com/ws/trades

## Configuration

### Environment Variables

Edit ConfigMap in `k8s/00-namespace.yaml`:

```bash
kubectl edit configmap alphamind-config -n alphamind
```

Variables:
- `BROKER`: paper, exness, justmarkets, mt5
- `JWT_ALGORITHM`: HS256 (default)
- `JWT_EXP_MINUTES`: 60 (default)
- `LOG_LEVEL`: INFO, DEBUG, WARNING
- `FRONTEND_ORIGINS`: comma-separated allowed origins

### Secrets Management

For production, use AWS Secrets Manager or HashiCorp Vault:

1. Install external-secrets operator:
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

2. Configure SecretStore in `k8s/08-secrets-management.yaml`

3. Update secrets:
```bash
kubectl apply -f k8s/08-secrets-management.yaml
```

## Scaling

### Horizontal Pod Autoscaling

Backend autoscales from 3 to 10 replicas based on CPU usage:

```bash
# Check HPA status
kubectl get hpa -n alphamind

# Adjust if needed
kubectl patch hpa backend-hpa -n alphamind -p '{"spec":{"minReplicas":5,"maxReplicas":20}}'
```

### Database Scaling

PostgreSQL is configured as a 3-node Patroni cluster with automatic failover. To add more replicas:

```bash
kubectl patch statefulset postgres -n alphamind -p '{"spec":{"replicas":5}}'
```

## Monitoring & Alerts

### Prometheus Queries

```promql
# Backend request rate
rate(http_requests_total[5m])

# Backend error rate
rate(http_requests_total{status=~"5.."}[5m])

# Database connection pool usage
postgres_sql_db_connections_usage

# Redis memory usage
redis_memory_used_bytes
```

### Setup Alerting

Update `k8s/04-monitoring.yaml` with AlertManager configuration:

```yaml
groups:
- name: alphamind
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
```

## Backup & Recovery

### View Backup Jobs

```bash
kubectl get cronjob -n alphamind
kubectl get jobs -n alphamind

# Check last backup
kubectl logs -n alphamind -l app=postgres-backup -n alphamind | head -20
```

### Manual Backup

```bash
# Trigger immediate backup
kubectl create job --from=cronjob/postgres-backup manual-backup-$(date +%s) -n alphamind

# Copy backup off-cluster (optional, to S3)
AWS_PROFILE=default aws s3 cp \
  /path/to/backup/postgres_*.dump \
  s3://my-backup-bucket/alphamind/
```

### Restore from Backup

```bash
# List available backups
kubectl get pvc backup-data -n alphamind

# Restore database
kubectl exec -it postgres-0 -n alphamind -- pg_restore -d alphamind /backup/postgres_YYYYMMDD.dump
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n alphamind

# View logs
kubectl logs <pod-name> -n alphamind

# Check resource requests
kubectl top pods -n alphamind
```

### Database Connection Issues

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n alphamind -- psql -U postgres -d alphamind

# Check connections
SELECT count(*) FROM pg_stat_activity;
```

### Redis Issues

```bash
# Connect to Redis
kubectl exec -it <redis-pod> -n alphamind -- redis-cli

# Check memory
info memory

# Clear cache if needed
FLUSHALL
```

### WebSocket Connection Issues

1. Verify token in localStorage
2. Check network tab for 401/403 errors
3. Verify `/ws/trades` endpoint is accessible
4. Check backend logs: `kubectl logs -f deployment/backend -n alphamind`

## Production Best Practices

### Security

- [ ] Use network policies (already configured in k8s/07-ingress-and-networking.yaml)
- [ ] Enable pod security policies
- [ ] Use RBAC for service accounts
- [ ] Rotate secrets regularly
- [ ] Use private container registry

### Performance

- [ ] Enable horizontal pod autoscaling
- [ ] Configure pod disruption budgets
- [ ] Use dedicated nodes for stateful services
- [ ] Enable request rate limiting

### Reliability

- [ ] Setup monitoring and alerting
- [ ] Test disaster recovery procedures
- [ ] Use read replicas for databases
- [ ] Enable automatic certificate renewal

### Compliance

- [ ] Audit logging
- [ ] Data encryption at rest
- [ ] Network encryption (TLS)
- [ ] Regular security scans

## Teardown

To remove the entire deployment:

```bash
kubectl delete namespace alphamind
kubectl delete namespace ingress-nginx
kubectl delete clusterissuer letsencrypt-prod
```

## Support

For issues or questions:
1. Check pod logs: `kubectl logs -f <pod-name> -n alphamind`
2. Check events: `kubectl describe node` and `kubectl describe pod`
3. Run diagnostics: `kubectl cluster-info dump`
4. Review Prometheus metrics

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Charts](https://artifacthub.io/)
- [PostgreSQL Patroni](https://patroni.readthedocs.io/)
- [Cert-Manager](https://cert-manager.io/)
- [Ingress-Nginx](https://kubernetes.github.io/ingress-nginx/)
