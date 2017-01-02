#-*- coding:utf-8 -*-
from urllib.request import urlopen as urlopen
from urllib.request import Request as request
from urllib.parse import urlencode
import json
import hashlib
import time

def buildMySign(params,secretKey):
    sign = ''
    for key in sorted(params.keys()):
        sign += key + '=' + str(params[key]) +'&'
    data = sign+'secret_key='+secretKey
    return  hashlib.md5(data.encode("utf8")).hexdigest().upper()


def httpGet(site, resource, params=None):
    argv = urlencode(params) if params else ''
    url = 'https://' + site + resource + '?' + argv

    while True:
        data = urlopen(url).read()
        if data:break

    return json.loads(data.decode())


def httpPost(site, resource, params=None):
    headers = { "Content-Type" : "application/x-www-form-urlencoded; charset=UTF-8" }
    argv = urlencode(params)
    url = 'https://' + site + resource

    while True:
        req = request(url, headers=headers, data=argv.encode('utf-8'))
        data = urlopen(req).read()
        if data:break

    return json.loads(data.decode())

