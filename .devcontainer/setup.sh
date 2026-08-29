#!/usr/bin/env bash
set -e

echo "=================================================================="
echo "🚀 Initializing K8s Sentinel Cloud Environment (Codespaces)"
echo "=================================================================="

# 1. Install Kind if missing
if ! command -v kind &> /dev/null; then
    echo "• Installing Kind (Kubernetes in Docker)..."
    ARCH=$(dpkg --print-architecture)
    curl -Lo ./kind "https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-${ARCH}"
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
fi

# 2. Install kubernetes-mcp-server if missing
if ! command -v kubernetes-mcp-server &> /dev/null; then
    echo "• Installing Kubernetes MCP Server binary..."
    ARCH=$(dpkg --print-architecture)
    curl -Lo ./kubernetes-mcp-server "https://github.com/containers/kubernetes-mcp-server/releases/download/v0.0.66/kubernetes-mcp-server-linux-${ARCH}"
    chmod +x ./kubernetes-mcp-server
    sudo mv ./kubernetes-mcp-server /usr/local/bin/kubernetes-mcp-server
fi

# 3. Install Python dependencies
echo "• Installing Python dependencies..."
pip install requests pyyaml

# 4. Spin up real Kind cluster
if ! kind get clusters | grep -q "sentinel-demo"; then
    echo "• Booting real single-node Kind Kubernetes cluster (sentinel-demo)..."
    kind create cluster --name sentinel-demo --config infra/kind-config.yaml
else
    echo "• Kind cluster sentinel-demo already running."
fi

# 5. Deploy baseline demo app and CRD
echo "• Deploying fragile payments-api workload..."
kubectl apply -f infra/demo-app/base.yaml
kubectl -n demo rollout status deploy/payments-api --timeout=120s

echo "• Applying Sentinel IncidentRemediation CRD..."
kubectl apply -f infra/crd/incident-remediation-crd.yaml

# 6. Pre-seed SQLite incident memory
echo "• Pre-seeding SQLite FTS5 incident memory..."
python3 sentinel/memory_rag.py seed

# 7. Start background MCP server
if ! pgrep -f "kubernetes-mcp-server" > /dev/null; then
    echo "• Starting background Kubernetes MCP Server on port 9236..."
    nohup kubernetes-mcp-server --port 9236 --bind-address 0.0.0.0 --kubeconfig ~/.kube/config --disable-destructive > /tmp/mcp-server.log 2>&1 &
fi

echo ""
echo "=================================================================="
echo "✅ K8S SENTINEL REAL CLUSTER IS LIVE & READY!"
echo "=================================================================="
echo "  • Cluster:       Kind (sentinel-demo) - Kubernetes v1.32"
echo "  • Workload:      demo/payments-api (3/3 replicas running)"
echo "  • MCP Server:    Listening on http://localhost:9236/mcp"
echo "  • Quickstart:    Run: python3 sentinel/cli.py simulator"
echo "=================================================================="
echo ""
