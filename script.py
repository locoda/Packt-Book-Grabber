#!/usr/bin/env python3

import argparse
import json
import logging
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
    parser.add_argument("--ddir", type=str, default="./",
                        help="direcotry you want to download the book, end with /, default as current directory")
    parser.add_argument("-u", "--upload", type=str, choices=["dropbox", "ftp"],
                        help="upload to cloud drive you selected, only work when you also download")
    parser.add_argument("--udir", type=str, default="/",
                        help="direcotry you want to upload the book, end with /, default as root directory")
    parser.add_argument("--config", type=str, default="credential.json",
                        help="configuration file")
    return parser.parse_args()


def _get_configuration(key):
    try:
        return config[key]
    except KeyError:
        logger.error("%s not founded in Configuration File, Aborted" % key)
        exit()


def login(s):
    """
    login to Packt
        :param s:  session used cross script
    """
    r = s.get(LOGIN_URL, headers=headers)
    tree = html.fromstring(r.content)

    data = {
        'name': _get_configuration("name"),
        'pass': _get_configuration("pass"),
        'op': 'Log in',
        'form_build_id': tree.xpath('//form[@id="packt-v3-account-login-form"]//input[@name="form_build_id"]/@value')[0],
        'form_id': tree.xpath('//form[@id="packt-v3-account-login-form"]//input[@name="form_id"]/@value')[0],
    }
    r = s.post(LOGIN_URL, data=data, headers=headers)
    return ('account' in r.url)


def claim_book(s):
    """
    claim the free book
        :param s:  session used cross script
    """
    r = s.get(FREE_BOOk_URL, headers=headers)
    tree = html.fromstring(r.content)

    key_pattern = re.compile("Packt.offers.onLoadRecaptcha\(\'(.+?)\'\)")
    site_key = re.search(key_pattern, r.text).group(1)
    client = AnticaptchaClient(_get_configuration('anti-captcha'))
    task = NoCaptchaTaskProxylessTask(FREE_BOOk_URL, site_key)
    job = client.createTask(task)
    job.join()
    link = tree.xpath('//form[@id="free-learning-form"]/@action')[0]

    r = s.post(BASE_URL+link,
               data={'g-recaptcha-response': job.get_solution_response()}, headers=headers)
    return ('account' in r.url)


def download_book(s, n, dtype, ddir, dupload, udir):
    """
    Download books
        :param s:  session used cross script
        :param n: max number of books to download
        :param dtype: type of books to download
        :param ddir: directory of books to download
        :param dupload: where to uploaded
    """
    r = s.get(MY_EBOOK_URL, headers=headers)
    tree = html.fromstring(r.content)

    booklist = tree.xpath('//div[@id="product-account-list"]/div[@nid]')
    n = min(len(booklist), n)
    for book in booklist[:n]:
        nid = book.xpath('./@nid')[0]
        title = book.xpath('./@title')[0]
        logger.info("Downloading Book %s: %s" % (nid, title))
        try:
            link = book.xpath('.//a[contains(@href,"%s")]/@href' % dtype)[0]
        except IndexError:
            logger.error("%s for this book doesn't exsit" % dtype)
            continue
        r = s.get(BASE_URL + link, headers=headers, stream=True)
        filename = "%s.%s" % (title, dtype)
        with open(ddir + filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

        # check if upload needed
        if dupload:
            if dupload == "dropbox":
                import dropbox
                dbx = dropbox.Dropbox(_get_configuration("dropbox"))
                with open(ddir + filename, 'rb') as f:
                    dbx.files_upload(f.read(), udir + filename)
            if dupload == "ftp":
                import ftplib
                ftp_config = _get_configuration("ftp")
                ftp = ftplib.FTP(ftp_config['server'])
                ftp.login(ftp_config['user'], ftp_config['pass'])
                ftp.cwd(udir)
                ftp.storbinary("STOR " + filename, open(ddir + filename, 'rb'))


def _get_free_book_title():
    """
    get title of today's free book -- used for sent notifications
    """
    r = requests.get(FREE_BOOk_URL, headers={'User-Agent': USER_AGENT})
    t = html.fromstring(r.content)
    return ("".join(t.xpath('//div[@class="dotd-title"]//text()')).strip())


def ifttt_notify():
    """
    IFTTT notification
    """
    r = requests.post(_get_configuration("ifttt"), data={
        "value1": _get_free_book_title()})
    return (r.status_code is 200)


def mailgun_notify():
    """
    Mailgun notification
    """
    mailgun_config = _get_configuration("mailgun")
    r = requests.post(
        "https://api.mailgun.net/v3/%s/messages" % mailgun_config['domain'],
        auth=("api", mailgun_config['api']),
        data={"from": "PacktPub Notification <packtpub@%s>" % mailgun_config['domain'],
              "to": "<%s>" % mailgun_config['to'],
              "subject": "Today's Free book from PacktPub!",
              "text": "Today's free book is %s" % _get_free_book_title()})
    return (r.status_code is 200)


if __name__ == "__main__":
    # set logger
    logging.basicConfig(level=logging.INFO,
                        format='[%(levelname)s] %(message)s',)
    logger = logging.getLogger()
    # parse arguments
    args = parse_arguments()
    # create a requests session using through process
    s = requests.Session()

    with open(args.config) as fd:
        config = json.load(fd)

    # Check if should notify
    if args.notify is not None:
        if args.notify == "ifttt":
            if ifttt_notify():
                logger.info("IFTTT Notification successful sent")
            else:
                logger.error(
                    "IFTTT failed, Please check with your IFTTT configuration ")
        if args.notify == "mailgun":
            if mailgun_notify():
                logger.info("Mailgun Notification successful sent")
            else:
                logger.error(
                    "Mailgun failed, Please check with your Mailgun configuration ")

    if (args.claim or args.download):
        # Login
        if login(s):
            logger.info('Successfully Login into PacktPub')
        else:
            logger.error(
                'Login Failed. Check with your username and password configuration')

        # Check if claim
        if args.claim:
            if claim_book(s):
                logger.info('Claim Free book Successfully')
            else:
                logger.error(
                    'Claim Failed. Check with your anti-captcha configuration')

        # Check if should download
        if args.download is not None:
            download_book(s, args.download, args.type,
                          args.ddir, args.upload, args.udir)
