#!/usr/bin/env bash
# One-time setup of the local CI/CD lab. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")"

CLUSTER=ci
NAMESPACE=chatbot

# 1. Kubernetes cluster (creates the "kind" Docker network everything else joins)
if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --config kind-config.yaml
fi

# 2. Jenkins, SonarQube, Postgres, registry
docker compose up -d --build

# 3. Point every node's containerd at the registry for localhost:5001 images
for node in $(kind get nodes --name "$CLUSTER"); do
  docker exec "$node" mkdir -p /etc/containerd/certs.d/localhost:5001
  docker exec -i "$node" sh -c 'cat > /etc/containerd/certs.d/localhost:5001/hosts.toml' <<EOF
[host."http://kind-registry:5000"]
EOF
done

# 4. App namespace + secret (keys come from your local .env, never from Git)
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
if [ -f ../.env ]; then
  kubectl -n "$NAMESPACE" create secret generic k8s-rag-chatbot-secrets \
    --from-env-file=../.env --dry-run=client -o yaml | kubectl apply -f -
else
  echo "WARN: ../.env not found — create the secret before the first deploy."
fi

# 5. Kubeconfig Jenkins uses (API server address reachable inside the kind network)
kind get kubeconfig --internal --name "$CLUSTER" > kubeconfig-jenkins.yaml
echo
echo "Done. Upload ci/kubeconfig-jenkins.yaml to Jenkins as a 'Secret file' credential with ID: kind-kubeconfig"
echo "Jenkins:   http://localhost:8080   (initial password: docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword)"
echo "SonarQube: http://localhost:9000   (admin / admin on first login)"
