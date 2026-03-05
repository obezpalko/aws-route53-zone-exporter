#!/usr/bin/env python3
"""
get route53 counts and limits for all zones
"""
from flask import Flask, Response, send_file, jsonify
import json
import os
import time
import logging
import io

import boto3
import prometheus_client

app = Flask(__name__)
REGISTRY = prometheus_client.CollectorRegistry()
FAVICON_PATH = os.path.join(os.path.dirname(__file__), 'static', 'favicon.ico')
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
# logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

def main(g, g_l):
    """
    man function
    """
    client = boto3.client('route53')
    all_records = {}
    paginator = client.get_paginator('list_hosted_zones')
    try:
        response_iterator = paginator.paginate(
            PaginationConfig={
                'PageSize': 100,
                # 'MaxItems': 200,
            },
        )
        for response in response_iterator:
            for zone in response['HostedZones']:
                limit_response = client.get_hosted_zone_limit(
                    Type='MAX_RRSETS_BY_ZONE',
                    HostedZoneId=zone['Id'],
                )
                all_records[zone['Id'].replace('/hostedzone/', '')] = {
                    'Name': zone['Name'],
                    'ResourceRecordSetCount': zone['ResourceRecordSetCount'],
                    'Count': limit_response['Count'],
                    'LimitRRSets': limit_response['Limit']['Value'],
                    'LimitRatio': limit_response['Count']/limit_response['Limit']['Value'],
                }
                g.labels(
                    zone['Name'][:-1],
                    zone['Config']['PrivateZone'],
                    zone['Id'].replace('/hostedzone/', ''),
                ).set(zone['ResourceRecordSetCount'])

                g_l.labels(
                    zone['Name'][:-1],
                    zone['Config']['PrivateZone'],
                    zone['Id'].replace('/hostedzone/', ''),
                ).set(limit_response['Limit']['Value'])
    except Exception as error:
        logging.error('An error occurred getting source zone records:')
        logging.critical(str(error))
        raise
    logging.info(f'{len(all_records)} zones have been collected')




@app.route('/')
def root():
    return 'Exporter for AWS Route53 zones. See /metrics.'

@app.before_first_request
def populate_metrics():
    main(g, g_l)

@app.route('/metrics')
def metrics():
    return Response(prometheus_client.generate_latest(REGISTRY), mimetype='text/plain; version=0.0.4; charset=utf-8')

@app.route('/favicon.ico')
def favicon():
    return send_file(FAVICON_PATH, mimetype='image/x-icon')

@app.route('/healthz')
def healthz():
    return jsonify({'status': 'ok', 'message': 'app is running'})

g = prometheus_client.Gauge(
    'aws_route53_zone_rr_count',
    'number of records in aws zone',
    ['name', 'private', 'id'],
    registry=REGISTRY,
)
g_l = prometheus_client.Gauge(
    'aws_route53_zone_rr_limit',
    'max records in aws_zone',
    ['name', 'private', 'id'],
    registry=REGISTRY,
)

if __name__ == '__main__':
    logging.info('starting app')
    app.run(host='0.0.0.0', port=8080)
    # For production, use: gunicorn -w 4 -b 0.0.0.0:8080 aws_exporter:app
