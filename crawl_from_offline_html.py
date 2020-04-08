import aiohttp
import asyncio
import time
import threading
from bs4 import BeautifulSoup
import re
import multiprocessing as mp
import os
from urllib.parse import urljoin
import random
import urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests
from queue import Queue

import config

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
}


class ThreadOfflineSpider(threading.Thread):
    def __init__(self, threadName, imageQueue):
        super(ThreadOfflineSpider, self).__init__()
        self.threadName = threadName
        self.imageQueue = imageQueue
        self.THREAD_EXIT = False

    def run(self):
        print(self.threadName + ' begin.')
        while not self.THREAD_EXIT or not self.imageQueue.empty():
            try:
                img_link, save_path, url = self.imageQueue.get(block=False)
                self.writeImage(img_link, save_path, url)
            except Exception as e:
                pass
            time.sleep(0.1)
        print(self.threadName + ' finish.')

    def writeImage(self, img_link, save_path, img_id):
        img_link = img_link.replace(',150', ',2400')
        print(img_link)
        filename = os.path.basename(img_link)
        filename = re.sub('[\/:*?"<>|]', '-', filename)
        if len(filename) > 50:
            filename = filename[50:]
        try:
            r = requests.get(img_link, stream=True, headers=headers, verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
            print('img requests error')
            return

        try:
            if len(r.content) / 1024 < config.img_size_threld:
                return
            with open(os.path.join(save_path, str(img_id)+filename), 'wb') as f:
                #print('response size: ', len(r.content)/1024, 'KB')
                for chunk in r.iter_content(1024):   #下载大文件
                    f.write(chunk)
                #f.write(r.content)
        except Exception as e:
            print(repr(e))
            print('img save error:', os.path.join(save_path, filename))
            return
#https://ids.lib.harvard.edu/ids/iiif/21159010/full/2400,/0/default.jpg?download&caption

def main():
    img_queue = Queue()

    thread_list = []
    loadList = []
    for i in range(config.thread_num):
        loadList.append('线程'+str(i))
    for threadName in loadList:
        Ithraad = ThreadOfflineSpider(threadName, img_queue)
        Ithraad.start()
        thread_list.append(Ithraad)


    html = ''
    with open('./iframe_content.html', 'r', encoding='utf-8') as f:
        html = f.read()

    if html == '':
        print('请将html内容存入iframe_content.html文件！')
        for thread in thread_list:
            thread.THREAD_EXIT = True
            thread.join()
        return

    soup = BeautifulSoup(html, 'lxml')

    title = soup.find('title')
    if title:
        title = title.get_text().strip()
    else:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()

    # 找出所有图片url
    url_feature = '^[\s\S]*(' + config.img_url_keyword + ')[\s\S]*$'
    imgs = soup.find_all("img", {"src": re.compile(url_feature)}, recursive=True)
    img_links = []
    for link in imgs:
        link = link['src']
        if len(link) < 2:
            continue
        link = link.replace("\n", "")
        link = link.replace("\r", "")
        img_links.append(link.strip())

    title = re.sub('[\/:*?"<>|]', '-', title)    #创建文件夹时去除非法字符
    if len(title) > 50:
        title = title[:50]              #防止文件夹名称过长
    if not os.path.exists(os.path.join(config.save_path + title)):
        os.makedirs(os.path.join(config.save_path + title))     #一个网页创建一个文件夹

    print('Find img link count: ', len(img_links))
    for i, link in enumerate(img_links):
        img_queue.put((link, os.path.join(config.save_path + title), i))


    print('等待图片下载...')

    for thread in thread_list:
        thread.THREAD_EXIT = True
        thread.join()

    print('结束！')


if __name__ == "__main__":
    main()

#https://ids.lib.harvard.edu/ids/iiif/21159010/full/1200,/0/default.jpg?download&caption
#https://ids.lib.harvard.edu/ids/iiif/21159010/full/300,/0/default.jpg?download&caption
#https://ids.lib.harvard.edu/ids/iiif/21159013/full/,150/0/default.jpg

#https://iiif.lib.harvard.edu/manifests/drs:21158960

# 17 19
# node dezoomify-node.js "https://ids.lib.harvard.edu/ids/iiif/21159013/full/150,/0/default.jpg" "default.jpg"

# https://ids.lib.harvard.edu/ids/iiif/21159013/9216,11264,1024,1024/1024,1024/0/default.jpg

# https://ids.lib.harvard.edu/ids/iiif/21159013/9216,11264,1024,1024/1024,1024/0/default.jpg
#
# https://ids.lib.harvard.edu/ids/iiif/21159013/4096,13312,1024,1024/1024,1024/0/default.jpg
#
# {"profile": ["http://iiif.io/api/image/2/level2.json", {"supports": ["canonicalLinkHeader", "profileLinkHeader", "mirroring", "rotationArbitrary", "regionSquare", "sizeAboveFull"], "qualities": ["default", "bitonal", "gray", "color"], "formats": ["jpg", "tif", "png", "gif", "webp"]}], "tiles": [{"width": 1024, "scaleFactors": [1, 2, 4, 8, 16, 32, 64, 128]}], "protocol": "http://iiif.io/api/image", "maxWidth": 2400, "sizes": [{"width": 86, "height": 127}, {"width": 172, "height": 254}, {"width": 343, "height": 507}, {"width": 686, "height": 1013}, {"width": 1372, "height": 2025}], "maxHeight": 2400, "height": 16195, "width": 10973, "@context": "http://iiif.io/api/image/2/context.json", "@id": "https://ids.lib.harvard.edu/ids/iiif/21159013"}