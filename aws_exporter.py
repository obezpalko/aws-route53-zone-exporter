#!/usr/bin/env python3
"""
get route53 counts and limits for all zones
"""
import http.server
import json
import os
import threading
import time
import logging

import boto3
import prometheus_client


REGISTRY = prometheus_client.CollectorRegistry()
FAVICON = open('/static/favicon.ico', 'rb').read()
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


class MyHTTPHandler(http.server.BaseHTTPRequestHandler):

    # def log_request(self, code='-', size='-'):
    #     pass

    def do_GET(self):
        content_type = 'text/plain'
        if self.path == '/health/is_alive':
            response = 'Alive\n'.encode('utf-8')
        elif self.path == '/metrics':
            response = prometheus_client.generate_latest(registry=REGISTRY)
        elif self.path == '/favicon.ico':
            response = FAVICON
            content_type = 'image/x-icon'
        else:
            response = json.dumps(dict(os.environ)).encode('utf-8')
            content_type = 'application/json'
        self.send_response(200)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self):
        pass
    #
    # def do_HEAD(self):
    #     pass


def start_http_server():
    """
    start additional http server for health checks
    """
    treads = {}
    for port in [8080, 8084]:
        logging.info(f'starting server or {port}')
        server_address = ('', port)
        server = http.server.HTTPServer(server_address, MyHTTPHandler)
        treads[port] = threading.Thread(
            target=server.serve_forever, daemon=True,
        )
        treads[port].start()
        logging.info(f'server on {port} started')


if __name__ == '__main__':
    logging.info('starting app')

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
    start_http_server()
    while True:
        main(g, g_l)
        time.sleep(3600)
