import boto3
import requests
import sys

from pprint import pprint

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
