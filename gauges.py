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
    gauge_list = ["\t%s\t%s" % (item['USGSSiteNumber'], item['GuageName']) for item in response['Items']]
    return lambda_response(None, {
        "text": """
Your Favorite River Guages
--------------------------
%s
""".strip() % "\n".join(gauge_list)
        })


def check_gauge(params, match):
    gauge_no = match.group(1)
    base_url = 'https://waterdata.usgs.gov/tx/nwis/uv'
    query_string = 'cb_00060=on&format=rdb&site_no=%s&period=1' % gauge_no
    full_url = '%s?%s' % (base_url, query_string)
    response = requests.get(full_url)
    last_4_lines = response.text.strip().split("\n")[-4:]
    return lambda_response(None, { "text": "\n".join(last_4_lines) })

def display_help_message():
    return lambda_response(None, {
        "text":  """
/gauges list - list favorite gauges
/gauges add USGS_SITE_NUMBER - add gauge to list of favorite gauges
/gauges check USGS_SITE_NUMBER - display current flow readings for gauge
        """.strip()
    })

def gauges_app(params):
    user = params['user_name'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]
    command_text = params['text'][0]

    commands = {
        r'check (.+)':  check_gauge,
        r'add (.+) (.+)': add_favorite_gauge,
        r'list': list_favorite_gauges,
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
    if token != expected_token:
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
