#!/usr/bin/env python3
"""
geat route53 counts and limits for all zones
"""
import http.server
import json
import os
import threading
import time

import boto3
from prometheus_client import CollectorRegistry
from prometheus_client import Gauge
from prometheus_client import start_http_server


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
        print('An error occurred getting source zone records:')
        print(str(error))
        raise
    print(f'{len(all_records)} zones have been collected')


class MyHTTPHandler(http.server.BaseHTTPRequestHandler):

    def log_request(self, code='-', size='-'):
        pass

    def do_GET(self):
        self.send_response(200)
        content_type = 'text/plain'
        if self.path == '/health/is_alive':
            response = 'Alive\n'
        else:
            response = json.dumps(dict(os.environ))
            content_type = 'application/json'

        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def do_POST(self):
        pass


def http_server():
    """
    start additional http server for health checks
    """
    server = http.server.HTTPServer(('', 8084), MyHTTPHandler)
    health_server_thread = threading.Thread(
        target=server.serve_forever, daemon=True,
    )
    health_server_thread.start()


if __name__ == '__main__':
    http_server()
    registry = CollectorRegistry()
    g = Gauge(
        'aws_route53_zone_rr_count',
        'number of records in aws zone',
        ['name', 'private', 'id'],
        registry=registry,
    )
    g_l = Gauge(
        'aws_route53_zone_rr_limit',
        'max records in aws_zone',
        ['name', 'private', 'id'],
        registry=registry,
    )
    start_http_server(8080, registry=registry)  # prometheus server
    while True:
        main(g, g_l)
        time.sleep(300)
