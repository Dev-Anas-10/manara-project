#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/deploy.sh <github-owner> <github-repo> <codestar-connection-arn> [region]

GITHUB_OWNER="${1:?github owner required}"
GITHUB_REPO="${2:?github repo required}"
CONNECTION_ARN="${3:?codestar connection arn required}"
REGION="${4:-us-east-1}"

deploy() {
  local template="$1" stack="$2"; shift 2
  echo ">>> Deploying $stack"
  aws cloudformation deploy \
    --template-file "$template" \
    --stack-name "$stack" \
    --capabilities CAPABILITY_IAM \
    --region "$REGION" \
    --no-fail-on-empty-changeset "$@"
}

deploy infra/01-network.yaml       ecs-cicd-network
deploy infra/02-storage-db.yaml    ecs-cicd-storage-db
deploy infra/03-ecr-ecs-alb.yaml   ecs-cicd-app
deploy infra/04-pipeline.yaml      ecs-cicd-pipeline \
  --parameter-overrides \
    GitHubOwner="$GITHUB_OWNER" \
    GitHubRepo="$GITHUB_REPO" \
    CodeStarConnectionArn="$CONNECTION_ARN"

echo ">>> ALB URL:"
aws cloudformation describe-stacks \
  --stack-name ecs-cicd-app \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ALBDnsName'].OutputValue" \
  --output text
