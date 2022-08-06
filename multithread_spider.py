#多线程爬虫
import aiohttp
import asyncio
import time
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
from Download_thread import ThreadWrite

import config

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

seen = set()
unseen = set([config.base_url])

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
}



# proxies = {'http':'http://117.88.5.202',
#            'https':'https://117.88.177.33',
#             'https':'https://119.254.94.93',
#             'https':'https://117.88.5.27',
#             'https':'https://125.73.220.18',
#             'https':'https://117.88.176.110',
#            }


#解析网页数据
def parse(html, url):
    soup = BeautifulSoup(html, 'lxml')

    url_feature = '^[\s\S]*(' + config.url_keyword + ')[\s\S]+$'
    urls = soup.find_all('a', {"href": re.compile(url_feature)}, recursive=True)   #^.+/.+?$

    # 为图片保存的文件夹找一个合适的名字
    title = soup.find('title')
    if title:
        title = title.get_text().strip()
    else:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
        else:
            title = os.path.basename(url)

    #当前url与url连接
    url_list = []
    for url_i in urls:
        url_i = url_i['href']
        if len(url_i) < 2:
            continue
        url_i = url_i.replace("\n", "")
        url_i = url_i.replace("\r", "")
        url_list.append(urljoin(url, url_i.strip()))
    page_urls = set(url_list)

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

    return title, page_urls, img_links, url

#下载网页
async def crawl(url, session):
    print('正在爬取: ', url)
    try:
        r = await session.get(url, headers=headers)   #, proxy = 'http://117.88.5.202'
        html = await r.text("utf-8","ignore")
        await asyncio.sleep(random.uniform(2, 5))       # slightly delay for downloading
        return (html, url)
    except Exception as e:
        print(repr(e))
        return ('', url)


async def main(loop):
    global unseen
    pool = mp.Pool(2)               # slightly affected
    async with aiohttp.ClientSession() as session:
        count = 1
        while len(unseen) != 0:
            # 队列中还有config.thread_num*10个以上的图未下载时，不下载解析网页
            if img_queue.qsize() > config.thread_num*10:
                time.sleep(1)
                continue
            print('Crawled url count: ', len(seen))
            print('UnCrawled url count: ', len(unseen))
            if config.max_page_count != None:
                if count > config.max_page_count:
                    break
            unseen = list(unseen)
            tasks = [loop.create_task(crawl(url, session)) for url in unseen[:5]]
            finished, unfinished = await asyncio.wait(tasks)
            htmls = [f.result() for f in finished]

            parse_jobs = [pool.apply_async(parse, args=(html, url,)) for (html, url) in htmls]
            results = [j.get() for j in parse_jobs]

            seen.update(unseen[:5])
            unseen = unseen[5:]
            unseen = set(unseen)
            for title, page_urls, img_links, url in results:
                print('正在从"%s"下载图片...' % url)
                title = re.sub('[\/:*?"<>|]', '-', title)    #创建文件夹时去除非法字符
                if len(title) > 50:
                    title = title[:50]              #防止文件夹名称过长
                if not os.path.exists(os.path.join(config.save_path + title)):
                    os.makedirs(os.path.join(config.save_path + title))     #一个网页创建一个文件夹

                unseen.update(page_urls - seen)
                count += 1

                for link in img_links:
                    img_queue.put((link, os.path.join(config.save_path + title), url))



if __name__ == "__main__":
    img_queue = Queue()

    URLValid = True
    if len(config.base_url) < 4:
        URLValid = False
        print('请输入要爬取的网站地址！')
    elif not config.base_url.startswith('http'):
        URLValid = False
        print('请输入格式正确的网站地址！')
    if config.max_page_count != None and config.max_page_count <= 0:
        print('最大爬取页数必须大于0！')
    elif URLValid:
        if config.max_page_count == None:
            print('将爬取所有网页图片！手动停止(Ctrl+C)或爬取完所有网页！')

        print('开始从%s爬取图片...' % config.base_url)

        thread_list = []
        loadList = []
        for i in range(config.thread_num):
            loadList.append('线程'+str(i))
        for threadName in loadList:
            Ithraad = ThreadWrite(threadName, img_queue)
            Ithraad.start()
            thread_list.append(Ithraad)

        t1 = time.time()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop))
        loop.close()
        print("Total time: ", time.time() - t1)

        print('等待图片下载...')

        for thread in thread_list:
            thread.THREAD_EXIT = True
            thread.join()

    print('结束！')

