from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import urllib3
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
}

img_link = 'https://iiif.lib.harvard.edu/manifests/view/drs:21158960$5i'

r = ''

try:
    r = requests.get(img_link, stream=False, headers=headers, verify=False)
except requests.exceptions.RequestException as e:
    print(e)
    print('img requests error')

try:
    if r != '':
        with open('./save2.html', 'wb') as f:
            f.write(r.content)
except Exception as e:
    print(repr(e))
    print('img save error')

