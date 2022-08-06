#下载工具类
from queue import Queue
import threading
from urllib.parse import urljoin
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests
import time
import urllib3
import os
import re
import random

import config

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
}

#多线程下载图片，在spider_thread.py中使用到
class ThreadWrite(threading.Thread):
    def __init__(self, threadName, imageQueue):
        super(ThreadWrite, self).__init__()
        self.threadName = threadName
        self.imageQueue = imageQueue
        self.THREAD_EXIT = False

    def run(self):
        print(self.threadName + ' begin.')
        while not self.THREAD_EXIT or not self.imageQueue.empty():
            if self.imageQueue.empty():
                time.sleep(1)
                continue
            try:
                img_link, save_path, url = self.imageQueue.get(block=False)
                self.writeImage(img_link, save_path, url)
            except Exception as e:
                pass
            time.sleep(random.uniform(0, 1))
        print(self.threadName + ' finish.')

    def writeImage(self, img_link1, save_path, url):
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        img_link = urljoin(url, img_link1)

        filename = os.path.basename(img_link)
        filename = re.sub('[\/:*?"<>|]', '-', filename)
        if len(filename) > 50:
            filename = filename[50:]
        # if os.path.exists(os.path.join(save_path, filename)):   # 减少重复下载图片的开销
        #     print('exist')
        #     return
        try:
            r = requests.get(img_link, stream=False, headers=headers, verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
            print('img requests error')
            return

        try:
            if len(r.content) / 1024 < config.img_size_threld:
                return
            with open(os.path.join(save_path, filename), 'wb') as f:
                #print('response size: ', len(r.content)/1024, 'KB')
                f.write(r.content)
        except Exception as e:
            print(repr(e))
            print('img save error:', os.path.join(save_path, filename))
            return
