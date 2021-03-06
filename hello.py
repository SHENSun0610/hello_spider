import requests
import ConfigParser
import argparse
import pickle
import sys
import time
import re

from bs4 import BeautifulSoup
from douban import Post

reload(sys)
sys.setdefaultencoding('utf-8')


urls = []
result_list = []

headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Ubuntu/11.10 Chromium/27.0.1453.93 ",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Host': "www.douban.com",
    'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
}


class douban_spider:

    def __init__(self, fun):
        self.urls = []
        self.url_seed = []
        self.url_gen_fun = fun
        self.post_result = []

    def do_spider(self):
        self.parse_config()
        self.gen_urls()
        # print self.urls
        self.parse_urls()
        # print self.post_result

    def parse_config(self, file_name='url_params.conf'):
        conf = ConfigParser.ConfigParser()
        with open(file_name) as input_file:
            conf.readfp(input_file)
            for section in conf.sections():
                self.url_seed.append(conf.get(section, 'url'))

    def gen_urls(self):
        self.urls = self.url_gen_fun(self.url_seed)

    def parse_urls(self):
        for url in self.urls:
            self.parse_url(url)
            time.sleep(10)

    def parse_url(self, url):
        html = requests.get(url, headers=headers, verify=False)
        if int(html.status_code) != 200:
            print 'parse_url %s failed! status_code: %s' % (url, html.status_code)
        result = self.get_urls_from_html(html.text)
        post = Post()
        for item in result:
            try:
                post_id = item[0]
                latest_timestamp = item[1]
                result_post = post.parse_post(post_id)
                if not result_post:
                    print "parse failed!"
                    print post_id
                    print latest_timestamp
                    continue
                post.save_post_into_db(result_post, latest_timestamp)
            except:
                print "parse failed!"
                pass
            time.sleep(3)

    def get_urls_from_html(self, html):
        try:
            soup = BeautifulSoup(html, "lxml")
            tr_list = soup.find_all('tr', attrs={'class': ''})
            for tr in tr_list:
                if not tr.has_attr('class'):
                    continue
                #get url
                title_td = tr.find('td', attrs={'class': 'title'})
                url = title_td.find('a')['href']
                post_id = self.get_post_id_from_url(url)
                #print post_id
                #get latest time
                time_td = tr.find('td', attrs={'class': 'time'})
                #print time_td.text
                latest_time = self.get_timestamp(time_td.text)
                #print latest_time
                yield (post_id, latest_time)
        except:
            pass

    def get_timestamp(self, latest_time):
        if re.match(r'^\d{4}.*', latest_time) is not None:
            time_array = time.strptime(latest_time, '%Y-%m-%d')
        else:
            time_array = time.strptime('2016-'+latest_time, '%Y-%m-%d %H:%M')
        timestamp = int(time.mktime(time_array))
        return timestamp

    def get_post_id_from_url(slef, url):
        if not url.endswith('/'):
            url += '/'
        return url.split('/')[-2]


def get_html_increase(url_list):
    for url in url_list:
        i = 0
        while i <= 359050:
            this_url = url + str(i)
            i += 25
            yield this_url


if __name__ == '__main__':
    spider = douban_spider(get_html_increase)
    spider.do_spider()

