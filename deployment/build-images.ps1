# Build all ButterCup Docker images inside minikube's Docker daemon
$ErrorActionPreference = "Continue"

# Set minikube Docker env
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

Write-Host "Docker host: $Env:DOCKER_HOST"
Write-Host "Building orchestrator..."
docker build -f "$PSScriptRoot\..\orchestrator\Dockerfile" -t localhost/orchestrator:latest "$PSScriptRoot\.." 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: orchestrator build failed"; exit 1 }

Write-Host "Building fuzzer..."
docker build --build-arg BASE_IMAGE=gcr.io/oss-fuzz-base/base-runner -f "$PSScriptRoot\..\fuzzer\Dockerfile" -t localhost/fuzzer:latest "$PSScriptRoot\.." 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: fuzzer build failed"; exit 1 }

Write-Host "Building seed-gen..."
docker build -f "$PSScriptRoot\..\seed-gen\Dockerfile" -t localhost/seed-gen:latest "$PSScriptRoot\.." 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: seed-gen build failed"; exit 1 }

Write-Host "Building patcher..."
docker build -f "$PSScriptRoot\..\patcher\Dockerfile" -t localhost/patcher:latest "$PSScriptRoot\.." 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: patcher build failed"; exit 1 }

Write-Host "Building program-model..."
docker build -f "$PSScriptRoot\..\program-model\Dockerfile" -t localhost/program-model:latest "$PSScriptRoot\.." 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: program-model build failed"; exit 1 }

Write-Host "All images built successfully!"
docker images localhost/* --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
