#!/bin/bash
# Deployment script for Google Cloud Run
# Usage: ./deploy-gcp.sh

set -e

# Configuration
PROJECT_ID="flight-delay-api-483816"
SERVICE_NAME="flight-delay-prediction"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Starting deployment to Google Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo ""

# Set project
echo "Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Build and push Docker image to Google Container Registry
echo "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run with optimized configuration
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10 \
  --port 8080 \
  --set-env-vars WORKERS=2

# Get the service URL
echo ""
echo "Deployment complete!"
echo ""
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)')
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test your API:"
echo "  Health check: curl ${SERVICE_URL}/health"
echo "  Predict: curl -X POST ${SERVICE_URL}/predict -H 'Content-Type: application/json' -d '{\"flights\": [{\"OPERA\": \"Grupo LATAM\", \"TIPOVUELO\": \"N\", \"MES\": 3}]}'"
echo ""
echo "Update your Makefile with:"
echo "  STRESS_URL = ${SERVICE_URL}/"