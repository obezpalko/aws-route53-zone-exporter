# aws-route53-zone-exporter

Exports AWS Route53 hosted zone metrics to Prometheus for monitoring.

## Metrics Collected
- `aws_route53_zone_rr_count`: Number of DNS records in each Route53 hosted zone
- `aws_route53_zone_rr_limit`: Maximum allowed DNS records per hosted zone

Both metrics are labeled by zone name, zone type (private/public), and zone ID. These metrics are collected directly from the Route53 API, not from CloudWatch.

## Repository
This codebase is now available as a public repository: https://github.com/obezpalko/aws-route53-zone-exporter
