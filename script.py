import argparse
import json
import re
import shutil

import requests
from lxml import html
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask

BASE_URL = "https://www.packtpub.com"
LOGIN_URL = "https://www.packtpub.com/login"
FREE_BOOk_URL = "https://www.packtpub.com/packt/offers/free-learning"
MY_EBOOK_URL = "https://www.packtpub.com/account/my-ebooks"
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
headers = {'User-Agent': USER_AGENT}


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--claim", action="store_true",
                        help="if claim free book on this run")
    parser.add_argument("-n", "--notify", type=str, choices=["ifttt", "mailgun"],
                        help="notify the selected agent")
    parser.add_argument("-d", "--download", type=int,
                        help="number of book to download")
    parser.add_argument("-t", "--type", type=str, choices=["pdf", "epub"], default="pdf",
                        help="type of book to download, default as pdf")
    parser.add_argument("--dir", type=str, default="./",
                        help="direcotry you want to download the book, end with /, default as current directory")
    return parser.parse_args()


def login(s, file='credential.json'):
    """
    login to Packt
        :param s:  session used cross file
        :param file: json file contains username and password
    """
    r = s.get(LOGIN_URL, headers=headers)
    tree = html.fromstring(r.content)

    with open(file) as fd:
        info = json.load(fd)

    try:
        data = {
            'name': info['name'],
            'pass': info['pass'],
            'op': 'Log in',
            'form_build_id': tree.xpath('//form[@id="packt-v3-account-login-form"]//input[@name="form_build_id"]/@value')[0],
            'form_id': tree.xpath('//form[@id="packt-v3-account-login-form"]//input[@name="form_id"]/@value')[0],
        }
    except KeyError:
        print('Check your username and password in "credential.json" file')
    r = s.post(LOGIN_URL, data=data, headers=headers)
    return ('account' in r.url)


def claim_book(s, file='credential.json'):
    """
    claim the free book
        :param s:  session used cross file
    """
    r = s.get(FREE_BOOk_URL, headers=headers)
    tree = html.fromstring(r.content)

    with open(file) as fd:
        data = json.load(fd)
    try:
        api_key = data['anti-captcha']
    except KeyError:
        print('Please add your anti-captcha api key in "credential.json" file')
        return

    key_pattern = re.compile("Packt.offers.onLoadRecaptcha\(\'(.+?)\'\)")
    site_key = re.search(key_pattern, r.text).group(1)
    client = AnticaptchaClient(api_key)
    task = NoCaptchaTaskProxylessTask(FREE_BOOk_URL, site_key)
    job = client.createTask(task)
    job.join()
    link = tree.xpath('//form[@id="free-learning-form"]/@action')[0]

    r = s.post(BASE_URL+link,
               data={'g-recaptcha-response': job.get_solution_response()}, headers=headers)
    return ('account' in r.url)


def download_book(s, n, dtype, ddir):
    """
    Download books
        :param s:  session used cross file
        :param n: max number of books to download
        :param dtype: type of books to download
        :param ddir: directory of books to download
    """
    r = s.get(MY_EBOOK_URL, headers=headers)
    tree = html.fromstring(r.content)

    booklist = tree.xpath('//div[@id="product-account-list"]/div[@nid]')
    n = min(len(booklist), n)
    for book in booklist[:n]:
        nid = book.xpath('./@nid')[0]
        title = book.xpath('./@title')[0]
        print("Downloading Book %s: %s" % (nid, title))
        try:
            link = book.xpath('.//a[contains(@href,"%s")]/@href' % dtype)[0]
        except IndexError:
            print("%s for this book doesn't exsit" % dtype)
            continue
        r = s.get(BASE_URL + link, headers=headers, stream=True)
        filename = ddir + title + "." + dtype
        with open(filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)


def _get_free_book_title():
    """
    get title of today's free book -- used for sent notifications
    """
    r = requests.get(FREE_BOOk_URL, headers={'User-Agent': USER_AGENT})
    t = html.fromstring(r.content)
    return ("".join(t.xpath('//div[@class="dotd-title"]//text()')).strip())


def ifttt_notify(file='credential.json'):
    """
    IFTTT notification
        :param file:  contains ifttt webhook
    """

    with open(file) as fd:
        data = json.load(fd)

    try:
        r = requests.post(data["ifttt"], data={
                          "value1": _get_free_book_title()})
    except KeyError:
        print('Please add your ifttt webhook in "credential.json" file')
    return (r.status_code is 200)


def mailgun_notify(file='credential.json'):
    """
    Mailgun notification
        :param file:  contains mailgup domain, api and email address
    """
    with open(file) as fd:
        data = json.load(fd)

    r = requests.post(
        "https://api.mailgun.net/v3/%s/messages" % data['mailgun']['domain'],
        auth=("api", data['mailgun']['api']),
        data={"from": "PacktPub Notification <packtpub@%s>" % data['mailgun']['domain'],
              "to": "<%s>" % data['mailgun']['to'],
              "subject": "Today's Free book from PacktPub!",
              "text": "Today's free book is %s" % _get_free_book_title()})

    return (r.status_code is 200)


if __name__ == "__main__":
    # parse arguments
    args = parse_arguments()
    # create a requests session using through process
    s = requests.Session()

    # Check if should notify
    if args.notify is not None:
        if args.notify == "ifttt":
            if ifttt_notify():
                print("ifttt successful notified")
            else:
                print("ifttt failed")
        if args.notify == "mailgun":
            if mailgun_notify():
                print("mailgun successful notified")
            else:
                print("mailgun failed")

    if (args.claim or args.download):
        # Login
        if login(s):
            print('Login Successful!!')
        else:
            print('Login Failed.. Check your username and password in "credential.json" file')

        # Check if claim
        if args.claim:
            if claim_book(s):
                print('Claim Successful')
            else:
                print('Claim Failed.. Check your anti-captcha in "credential.json" file')

        # Check if should download
        if args.download is not None:
            download_book(s, args.download, args.type, args.dir)
