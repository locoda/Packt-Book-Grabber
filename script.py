import json
from lxml import html

import mechanicalsoup

BASE_URL = "https://www.packtpub.com"
LOGIN_URL = "https://www.packtpub.com/login"
FREE_BOOk_URL = "https://www.packtpub.com/packt/offers/free-learning"
MY_EBOOK_URL = "https://www.packtpub.com/account/my-ebooks"


def login(file, browser):
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


browser = mechanicalsoup.StatefulBrowser(
    soup_config={'features': 'lxml'},
    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
)

if not login('credential.json', browser):
    print('Login Failed.. Check your "credential.json" file')
if not claim_book(browser):
    print('Claim Failed.. Not sure Why')
