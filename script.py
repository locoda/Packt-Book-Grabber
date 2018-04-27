import argparse
import json
import shutil

import requests
from lxml import html

BASE_URL = "https://www.packtpub.com"
LOGIN_URL = "https://www.packtpub.com/login"
FREE_BOOk_URL = "https://www.packtpub.com/packt/offers/free-learning"
MY_EBOOK_URL = "https://www.packtpub.com/account/my-ebooks"
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
headers = {'User-Agent': USER_AGENT}


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

    data = {
        'name': info['name'],
        'pass': info['pass'],
        'op': 'Log in',
        'form_build_id': [],
        'form_id': [],
    }
    data['op'] = "Log in"
    data['form_build_id'] = tree.xpath(
        '//form[@id="packt-v3-account-login-form"]//input[@name="form_build_id"]/@value')[0]
    data['form_id'] = tree.xpath(
        '//form[@id="packt-v3-account-login-form"]//input[@name="form_id"]/@value')[0]
    r = s.post(LOGIN_URL, data=data, headers=headers)
    return ('account' in r.url)


def claim_book(s):
    """
    claim the free book
        :param s:  session used cross file
    """

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
        print("Downloading Book " + nid + ": " + title )
        try:
            link = book.xpath('.//a[contains(@href,"' + dtype + '")]/@href')[0]
        except IndexError:
            print(dtype + " for this book doesn't exsit")
            continue
        print(link)
        r = s.get(BASE_URL + link, headers=headers, stream=True)
        filename = ddir + title + "." + dtype
        with open(filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

def ifttt_notify(file='credential.json'):
    """
    IFTTT notification
        :param file:  contains ifttt webhook
    """
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
parser.add_argument("-n", "--notify", type=str, choices=["ifttt"],
                    help="notify the selected agent")
parser.add_argument("-d", "--download", type=int,
                    help="number of book to download")
parser.add_argument("-t", "--type", type=str, choices=["pdf", "epub"], default="pdf",
                    help="type of book to download, default as pdf")
parser.add_argument("--dir", type=str, default="./",
                    help="direcotry you want to download the book, end with /")
args = parser.parse_args()

s = requests.Session()
# Login
if not login(s):
    print('Login Failed.. Check your "credential.json" file')

# Check if should notify 
if args.notify is not None:
    if args.notify == "ifttt":
        ifttt_notify()

# Check if should download
if args.download is not None:
    download_book(s, args.download, args.type, args.dir)
