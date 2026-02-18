#!/bin/bash
set -e
cd "$(dirname "$0")"
source ./env

# Generate values file from template
VALUES_TEMPLATE=${BUTTERCUP_K8S_VALUES_TEMPLATE:-k8s/values-aks.template}
envsubst < "$VALUES_TEMPLATE" > k8s/values-overrides.crs-architecture.yaml
echo "Generated k8s/values-overrides.crs-architecture.yaml from $VALUES_TEMPLATE"

# Create secrets
CRS_KEY_BASE64=$(echo -n "$CRS_KEY_TOKEN" | base64)
echo "CRS_KEY_BASE64=$CRS_KEY_BASE64"

# Create TLS cert for registry cache
REGISTRY_CACHE_HOST="registry-cache.crs.svc.cluster.local"
MSYS_NO_PATHCONV=1 openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /tmp/registry-cache.key \
    -out /tmp/registry-cache.crt \
    -subj "/CN=${REGISTRY_CACHE_HOST}" \
    -addext "subjectAltName=DNS:${REGISTRY_CACHE_HOST},DNS:registry-cache,DNS:registry-cache.crs,DNS:ghcr.io" 2>/dev/null

echo "Generated TLS certificates"
echo "DONE"
