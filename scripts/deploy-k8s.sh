#!/bin/bash
# Complete Kubernetes deployment guide for AlphaMind

set -e

# Configuration
CLUSTER_NAME=${CLUSTER_NAME:-"alphamind"}
DOMAIN=${DOMAIN:-"alphamind.yourdomain.com"}
REGION=${REGION:-"us-east-1"}
NAMESPACE="alphamind"

echo "════════════════════════════════════════════════════════════════════════════════"
echo "        AlphaMind Kubernetes Deployment Script"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Domain: $DOMAIN"
echo "Region: $REGION"
echo "Namespace: $NAMESPACE"
echo ""

# Step 1: Verify kubectl access
echo "[1/12] Verifying kubectl access..."
if ! kubectl cluster-info &>/dev/null; then
    echo "ERROR: kubectl not configured or cluster not accessible"
    exit 1
fi
echo "✓ kubectl access verified"
echo ""

# Step 2: Create namespace
echo "[2/12] Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace $NAMESPACE name=$NAMESPACE --overwrite
echo "✓ Namespace created: $NAMESPACE"
echo ""

# Step 3: Install cert-manager
echo "[3/12] Installing cert-manager (if not already installed)..."
if ! kubectl get crd certificaterequests.cert-manager.io &>/dev/null; then
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    echo "  Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
fi
echo "✓ cert-manager is ready"
echo ""

# Step 4: Install ingress-nginx
echo "[4/12] Installing ingress-nginx (if not already installed)..."
if ! kubectl get ingressclass nginx &>/dev/null; then
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update
    helm install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.service.type=LoadBalancer
    echo "  Waiting for ingress-nginx to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx --timeout=300s
fi
echo "✓ ingress-nginx is ready"
echo ""

# Step 5: Create storage class and PVCs
echo "[5/12] Creating storage class and persistent volumes..."
kubectl apply -f k8s/05-storage.yaml
echo "✓ Storage class and PVCs created"
echo ""

# Step 6: Create secrets
echo "[6/12] Creating secrets..."
read -sp "Enter PostgreSQL password: " PG_PASSWORD
echo ""
read -sp "Enter JWT secret (or press Enter for random): " JWT_SECRET
if [ -z "$JWT_SECRET" ]; then
    JWT_SECRET=$(openssl rand -hex 32)
    echo ""
    echo "Generated JWT_SECRET: $JWT_SECRET"
fi
echo ""

kubectl create secret generic postgres-credentials \
    --from-literal=username=postgres \
    --from-literal=password=$PG_PASSWORD \
    --from-literal=database=alphamind \
    -n $NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic alphamind-secrets \
    --from-literal=JWT_SECRET=$JWT_SECRET \
    --from-literal=DATABASE_URL="postgresql://alphamind:$PG_PASSWORD@postgres:5432/alphamind" \
    --from-literal=REDIS_URL="redis://redis:6379/0" \
    --from-literal=DEEPSEEK_API_KEY="" \
    --from-literal=OPENAI_API_KEY="" \
    --from-literal=EXNESS_API_KEY="" \
    -n $NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

echo "✓ Secrets created"
echo ""

# Step 7: Apply namespace configuration
echo "[7/12] Applying namespace configuration..."
kubectl apply -f k8s/00-namespace.yaml
echo "✓ Namespace configuration applied"
echo ""

# Step 8: Deploy PostgreSQL HA
echo "[8/12] Deploying PostgreSQL HA cluster..."
kubectl apply -f k8s/01-postgres-ha.yaml
echo "  Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=600s || true
echo "✓ PostgreSQL deployed"
echo ""

# Step 9: Deploy Redis
echo "[9/12] Deploying Redis..."
kubectl apply -f k8s/03-redis.yaml
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s || true
echo "✓ Redis deployed"
echo ""

# Step 10: Deploy backend
echo "[10/12] Deploying backend application..."
kubectl apply -f k8s/02-backend-deployment.yaml
kubectl wait --for=condition=ready pod -l app=backend -n $NAMESPACE --timeout=300s || true
echo "✓ Backend deployed"
echo ""

# Step 11: Deploy monitoring
echo "[11/12] Deploying monitoring stack..."
kubectl apply -f k8s/04-monitoring.yaml
echo "✓ Monitoring deployed"
echo ""

# Step 12: Apply ingress and backup jobs
echo "[12/12] Applying ingress, networking, and backup jobs..."
kubectl apply -f k8s/07-ingress-and-networking.yaml
kubectl apply -f k8s/08-secrets-management.yaml
kubectl apply -f k8s/06-backup-cronjobs.yaml

# Replace domain in ingress
echo ""
echo "Updating ingress with domain: $DOMAIN..."
kubectl patch ingress alphamind-ingress -n $NAMESPACE --type='json' \
    -p="[{\"op\": \"replace\", \"path\": \"/spec/rules/0/host\", \"value\":\"api.$DOMAIN\"}]" || true

echo "✓ Ingress and networking configured"
echo ""

# Final checks
echo "════════════════════════════════════════════════════════════════════════════════"
echo "                    Deployment Complete!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Checking pod status..."
kubectl get pods -n $NAMESPACE
echo ""
echo "Checking services..."
kubectl get svc -n $NAMESPACE
echo ""
echo "Checking ingress..."
kubectl get ingress -n $NAMESPACE
echo ""
echo "Next steps:"
echo ""
echo "1. Wait for all pods to be Ready:"
echo "   kubectl get pods -n $NAMESPACE -w"
echo ""
echo "2. Get the ingress IP/hostname (this may take a few minutes):"
echo "   kubectl get ingress -n $NAMESPACE"
echo ""
echo "3. Configure DNS to point to the ingress IP:"
echo "   *.${DOMAIN} → <INGRESS_IP>"
echo ""
echo "4. View logs:"
echo "   kubectl logs -n $NAMESPACE -f deployment/backend"
echo ""
echo "5. Check backup status:"
echo "   kubectl get cronjob -n $NAMESPACE"
echo ""
echo "6. Access services:"
echo "   API: https://api.${DOMAIN}"
echo "   Grafana: https://grafana.${DOMAIN}"
echo "   Prometheus: https://prometheus.${DOMAIN}"
echo ""