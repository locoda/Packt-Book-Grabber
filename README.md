# Packt-Book-Grabber

A simple Python script for claim free book from [PacktPub](https://www.packtpub.com/), and also download from your library.

## Installation

First, install all requirements, run following command in root folder:

```shell
pip3 install -r requirements.txt
```

Second, you can check with help of file:

```shell
python3 script.py -h
```



## Basic Usage

### Basic Configration

You must config your `credential.json` before you do everything. You can easily make from sample by:

```shell
cp credential.json.example credential.json
```

Please put your user name after `"name":` and your password after `"pass":`

### Some Sample usage

1. If you just want to claim a free book:

   ```shell
   python3 script.py -c
   ```


2. If you want to notify yourself with ifttt webhook:

   You have to config the `ifttt` field in  `credential.json` file. If you don't know what is a key or what is IFTTT, please check with [IFTTT - Webhook](https://ifttt.com/maker_webhooks).

   ```shell
   python3 script.py -n ifttt
   ```

3. If you just want to download a book (first book in your library):

   ```shell
   python3 script.py -d 1
   ```

4.  If you want to download a book with type epub (default is pdf) to desktop:

   ```Shell
   python3 script.py -d 1 -t epub --dir ~/Desktop/
   ```

5. If you want to claim and then download:

   ```
   python3 script.py -c -d 1
   ```

   ​