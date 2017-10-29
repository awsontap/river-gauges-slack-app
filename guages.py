import boto3
import json
import logging
import os
import requests
import sys

from base64 import b64decode
from pprint import pprint
from urlparse import parse_qs

ENCRYPTED_EXPECTED_TOKEN = os.environ['kmsEncryptedToken']

kms = boto3.client('kms')
expected_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
favorite_gauges_table = 'river-guages-app-FavoriteGauges-1AY0P6LELBSWG'

def add_favorite_gauge(gauge_no, gauge_name):
    table = dynamodb.Table(favorite_gauges_table)
    table.put_item(Item={
        'USGSSiteNumber': gauge_no,
        'GuageName': gauge_name
    })


def list_favorite_gauges(consistent_read=False):
    table = dynamodb.Table(favorite_gauges_table)
    response = table.scan(ConsistentRead=consistent_read)
    return response['Items']


def check_gauge(gauge_no):
    base_url = 'https://waterdata.usgs.gov/tx/nwis/uv'
    query_string = 'cb_00060=on&format=rdb&site_no=%s&period=1' % gauge_no
    full_url = '%s?%s' % (base_url, query_string)
    print "GET %s" % full_url
    return requests.get(full_url)


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

    user = params['user_name'][0]
    command = params['command'][0]
    channel = params['channel_name'][0]
    command_text = params['text'][0]

    return lambda_response(None, "%s invoked %s in %s with the following text: %s" % (user, command, channel, command_text))


# For running in a shell during local development/testing
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "usage: python gauges.py <add|check>"
        sys.exit(1)

    if sys.argv[1] == 'check':
        response = check_gauge('08061540')
        print "HTTP Status: %s" % response.status_code
        last_4_lines = response.text.strip().split("\n")[-4:]
        print "\n".join(last_4_lines)
    elif sys.argv[1] == 'add':
        add_favorite_gauge('08061540', 'Rowlett Creek')
        items = list_favorite_gauges(consistent_read=True)
        pprint(items)
