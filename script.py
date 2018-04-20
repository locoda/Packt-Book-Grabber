import json

import mechanicalsoup
import requests
from lxml import html

BASE_URL = "https://www.packtpub.com"
LOGIN_URL = "https://www.packtpub.com/login"
FREE_BOOk_URL = "https://www.packtpub.com/packt/offers/free-learning"
MY_EBOOK_URL = "https://www.packtpub.com/account/my-ebooks"
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'

def login(browser, file='credential.json'):
    """
    login to Packt
        :param file: json file contains username and password
        :param browser:  browser used cross file
    """
    with open(file) as fd:
        data = json.load(fd)
    browser.open(LOGIN_URL)
    browser.select_form('form[id="packt-v3-account-login-form"]')
    browser['name'] = data['name']
    browser['pass'] = data['pass']
    resp = browser.submit_selected()
    return ('account' in browser.get_url())


def claim_book(browser):
    """
    claim the free book
        :param browser:  browser used cross file
    """
    browser.open(FREE_BOOk_URL)
    browser.select_form('form[id="free-learning-form"]')
    resp = browser.submit_selected()
    return ('account' in browser.get_url())


def ifttt_notify(file='credential.json'):
    r = requests.get(FREE_BOOk_URL, headers={'User-Agent': USER_AGENT})
    t = html.fromstring(r.content)
    with open(file) as fd:
        data = json.load(fd)
    title = "".join(t.xpath('//div[@class="dotd-title"]//text()')).strip()
    r = requests.post(data["ifttt"], data = { "value1" : title})


browser = mechanicalsoup.StatefulBrowser(
    soup_config={'features': 'lxml'},
    user_agent=USER_AGENT
)

if not login(browser):
    print('Login Failed.. Check your "credential.json" file')
if not claim_book(browser):
    print('Claim Failed.. Not sure Why')
# ifttt_notify()