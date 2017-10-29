import requests
from pprint import pprint

def check_guage(guage_no):
    base_url = 'https://waterdata.usgs.gov/tx/nwis/uv'
    query_string = 'cb_00060=on&format=rdb&site_no=%s&period=1' % guage_no
    full_url = '%s?%s' % (base_url, query_string)
    print "GET %s" % full_url
    return requests.get(full_url)

if __name__ == '__main__':
    response = check_guage('08061540')
    print "HTTP Status: %s" % response.status_code
    last_4_lines = response.text.strip().split("\n")[-4:]
    print "\n".join(last_4_lines)
