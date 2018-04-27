import argparse
import json

import requests
from lxml import html

BASE_URL = "https://www.packtpub.com"
LOGIN_URL = "https://www.packtpub.com/login"
FREE_BOOk_URL = "https://www.packtpub.com/packt/offers/free-learning"
MY_EBOOK_URL = "https://www.packtpub.com/account/my-ebooks"
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
headers = {'User-Agent': USER_AGENT}


def login(session, file='credential.json'):
    """
    login to Packt
        :param file: json file contains username and password
        :param browser:  browser used cross file
    """
    r = s.get(LOGIN_URL, headers=headers)
    tree = html.fromstring(r.content)

    with open(file) as fd:
        info = json.load(fd)

    data = {
        'name': info['name'],
        'pass': info['pass'],
        'op': 'Log in',
        'form_build_id': [],
        'form_id': [],
    }
    data['op'] = "Log in"
    data['form_build_id'] = tree.xpath(
        '//form[@id="packt-v3-account-login-form"]//input[@name="form_build_id"]/@value')
    data['form_id'] = tree.xpath(
        '//form[@id="packt-v3-account-login-form"]//input[@name="form_id"]/@value')

    r = s.post(LOGIN_URL, data=data, headers=headers)
    return ('account' in r.url)


def claim_book(session):
    """
    claim the free book
        :param browser:  browser used cross file
    """


def ifttt_notify(file='credential.json'):
    r = requests.get(FREE_BOOk_URL, headers={'User-Agent': USER_AGENT})
    t = html.fromstring(r.content)
    with open(file) as fd:
        data = json.load(fd)
    title = "".join(t.xpath('//div[@class="dotd-title"]//text()')).strip()
    print(title)
    try:
        r = requests.post(data["ifttt"], data={"value1": title})
    except KeyError:
        print('Please add your ifttt webhook in "credential.json" file')

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--notify", type=str,
                    help="notify the selected agent: e.g. ifttt")
args = parser.parse_args()
s = requests.Session()

if not login(s):
    print('Login Failed.. Check your "credential.json" file')
print(args.notify)
if args.notify == "ifttt":
    ifttt_notify()
