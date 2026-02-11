# CMR CARE ECS Deployment (CDK)

This CDK app deploys the CMR CARE web UI to AWS ECS Fargate behind an Application Load Balancer.

## Prereqs
- AWS CLI configured (`aws configure`)
- Node.js + CDK CLI (`npm install -g aws-cdk`)
- Docker (for image build)

## Deploy
```bash
/Users/akulkarn/Desktop/Code/UAH/akd-ext/infra/deploy.sh \
  --context openaiApiKey=sk-your-key \
  --context cmrMcpUrl=https://your-mcp-endpoint
```

You can also set `OPENAI_API_KEY` in `/Users/akulkarn/Desktop/Code/UAH/akd-ext/.env` and omit the `openaiApiKey` context flag. The deploy script will pick it up automatically unless you pass `openaiSecretName` or `openaiApiKey`.

If you already have a secret in AWS Secrets Manager, pass it instead:
```bash
/Users/akulkarn/Desktop/Code/UAH/akd-ext/infra/deploy.sh \
  --context openaiSecretName=your/openai/secret \
  --context cmrMcpUrl=https://your-mcp-endpoint
```

### Context options
- `openaiSecretName`: AWS Secrets Manager secret name containing the API key string
- `openaiApiKey`: Plaintext API key. CDK will create a secret named `cmr-care/openai-api-key` with this value.
- `cmrMcpUrl`: Override `CMR_MCP_URL`

## Outputs
- `LoadBalancerURL`: The public URL to the service

## Notes
- The container listens on port `8000`.
- The stack creates a new VPC and public ALB.
- If `openaiSecretName` is not provided, CDK creates `cmr-care/openai-api-key`. If no `openaiApiKey` is provided, the secret value is set to `REPLACE_ME` and must be updated in AWS Secrets Manager.
- If you already have bootstrap resources and see “resource already exists” errors, set `CDK_BOOTSTRAP_QUALIFIER=cmrcare1` and re-run. You can also skip bootstrap with `SKIP_BOOTSTRAP=1` if your `CDKToolkit` stack exists.
