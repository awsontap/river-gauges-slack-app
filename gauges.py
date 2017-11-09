import boto3
import json
import logging
import os
import re
import requests
import sys

from base64 import b64decode
from pprint import pprint
from urlparse import parse_qs

ENCRYPTED_EXPECTED_TOKEN = os.environ['kmsEncryptedToken']
FAVORITE_GAUGES_TABLE = os.environ['favoriteGaugesTable']

if ENCRYPTED_EXPECTED_TOKEN != 'local':
    kms = boto3.client('kms')
    expected_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')

def add_favorite_gauge(params, match):
    gauge_no = match.group(1)
    gauge_name = match.group(2)
    table = dynamodb.Table(FAVORITE_GAUGES_TABLE)
    table.put_item(Item={
        'USGSSiteNumber': gauge_no,
        'GuageName': gauge_name
    })
    return lambda_response(None, "added gauge %s %s" % (gauge_no, gauge_name))


def list_favorite_gauges(params, match):
    table = dynamodb.Table(FAVORITE_GAUGES_TABLE)
    response = table.scan()
    # return response['Items']
    gauge_list = ["%12s  %s" % (item['USGSSiteNumber'], item['GuageName']) for item in response['Items']]
    return lambda_response(None, {
        "text": """
Your Favorite River Guages
--------------------------
%s
""".strip() % "\n".join(gauge_list)
        })


def check_gauge(params, match):
    gauge_no = match.group(1)

    stats_url = 'https://waterdata.usgs.gov/nwis/uv?cb_00060=on&format=rdb&site_no=%s&period=1' % gauge_no
    graph_url = 'https://waterdata.usgs.gov/nwisweb/graph?agency_cd=USGS&site_no=%s&parm_cd=00060&period=1&format=gif_stats' % gauge_no

    response = requests.get(stats_url)
    last_measurement = response.text.strip().split("\n")[-1]
    logger.info("stats_url=\"%s\"" % last_measurement)
    logger.info("last_measurement=\"%s\"" % last_measurement)
    _, _, _, mtime, tz, cfs, _ = re.split('\s+', last_measurement)

    return lambda_response(None, {
        "text": "Last measurement: %s cfs @ %s %s" %  (cfs, mtime, tz),
        "attachments": [{ "image_url":  graph_url }]
    })

def display_help_message():
    return lambda_response(None, {
        "text":  """
/gauges list - list favorite gauges
/gauges add USGS_SITE_NUMBER RIVER_DESCRIPTION - add gauge to list of favorite gauges
/gauges check USGS_SITE_NUMBER - display current flow readings for gauge
        """.strip(),
    })

def gauges_app(params):
    user = params['user_name'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]
    command_text = params['text'][0] if 'text' in params else ''

    commands = {
        r'\s*check\s+(.+)':  check_gauge,
        r'\s*add\s+(\d+)\s+(.+)': add_favorite_gauge,
        r'\s*list': list_favorite_gauges,
    }

    for pattern, command in commands.iteritems():
        match = re.match(pattern, command_text)
        if match is not None:
            return command(params, match)

    return display_help_message()

def lambda_response(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    params = parse_qs(event['body'])
    token = params['token'][0]
    if ENCRYPTED_EXPECTED_TOKEN != 'local' and token != expected_token:
        logger.error("Request token (%s) does not match expected", token)
        return lambda_response(Exception('Invalid request token'))

    return gauges_app(params)


# For running in a shell during local development/testing
if __name__ == '__main__':
    params = {
        'user_name': ['jordan'],
        'command': ['/gauges'],
        'channel_name': ['local'],
        'text': [' '.join(sys.argv[1:])]
    }

    resp = gauges_app(params)
    pprint(resp)
