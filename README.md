# aws-route53-zone-exporter

Exports AWS Route53 hosted zone metrics to Prometheus for monitoring.

## Metrics Collected
- `aws_route53_zone_rr_count`: Number of DNS records in each Route53 hosted zone
- `aws_route53_zone_rr_limit`: Maximum allowed DNS records per hosted zone

Both metrics are labeled by zone name, zone type (private/public), and zone ID. These metrics are collected directly from the Route53 API, not from CloudWatch.

## Repository
This codebase is now available as a public repository: https://github.com/obezpalko/aws-route53-zone-exporter

## Kubernetes AWS Credentials Secret

To run this exporter in Kubernetes, you must provide AWS credentials and environment variables via a Kubernetes Secret. The deployment expects a secret named `<release-name>-aws-creds` (e.g., `aws-route53-zone-exporter-aws-creds`) in the same namespace.

### Required Environment Variables
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`

### Example: Create the Secret

```
kubectl create secret generic aws-route53-zone-exporter-aws-creds \
  --from-literal=AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID \
  --from-literal=AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY \
  --from-literal=AWS_DEFAULT_REGION=us-east-1 \
  --namespace <your-namespace>
```

The deployment will automatically load these environment variables from the secret.

