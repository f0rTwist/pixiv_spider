# encoding:utf-8
import json
import os
import time
import pickle
import requests
from bs4 import BeautifulSoup as bs
import threading

class Pixiv:

    def __init__(self, moder, pn):
        self.pixiv_username = '1466138257@qq.com'
        self.pixiv_password = 'TwistedFate5'
        self.m_set = set()
        self.accounts_url = 'https://accounts.pixiv.net/login?return_to=https%3A%2F%2Fwww.pixiv.net%2F&lang=zh&source=pc&view_type=page'  # 登录界面连接
        self.login_url = 'https://accounts.pixiv.net/api/login?lang=zh'  # 登录URL
        self.post = []  # 获取登录所需的随机cookie

        # 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36' Linux请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
            # 校验码，不添加会被反扒403错误
        }
        self.list_id = []
        self.list_url = []  # 排行榜url列表
        self.url_rank = 'https://www.pixiv.net/ranking.php?'  # 排行榜url
        mode_ = 'daily' if moder == 1 else 'weekly' if moder == 2 else 'monthly'
        self.params_rank = {  # 排行榜url接口
            'mode': mode_,
            'content': 'illust',
            'p': pn,
            'format': 'json'
        }
        self.i = 1  # 图片id
        self.glock = threading.Lock()  # 锁

    def login(self):  # 模拟登陆
        se = requests.session()
        pixiv_key_html = se.get(self.accounts_url, headers=self.headers).text

        pixiv_key_soup = bs(pixiv_key_html, 'lxml')
        self.post = pixiv_key_soup.find('input')['value']
        # print(self.post)
        data = {
            'pixiv_id': self.pixiv_username,
            'password': self.pixiv_password,
            'post_key': self.post,
            "ref": "wwwtop_accounts_index",
            "source": "pc",
            'return_to': 'https://www.pixiv.net/'
        }

        dare = se.post(self.login_url, data=data, headers=self.headers).text  # 登录
        print dare
        da = json.loads(dare)
        print(da)
        se.close()

        # Pixiv.test(self)
        # Pixiv.url_get(self)

    def init_set(self):
        f = open('s_log', 'rb')
        self.m_set = pickle.load(f)
        f.close()

    def dump_set(self):
        o = open('./s_log', 'wb')
        pickle.dump(self.m_set, o)
        o.close()

    def id_get(self):  # 获取rank作品id
        self.init_set()
        if self.params_rank['mode'] == 'daily':
            self.headers['referer'] = 'https://www.pixiv.net/ranking.php?mode=daily'
        elif self.params_rank['mode'] == 'weekly':
            self.headers['referer'] = 'https://www.pixiv.net/ranking.php?mode=weekly'
        elif self.params_rank['mode'] == 'monthly':
            self.headers['referer'] = 'https://www.pixiv.net/ranking.php?mode=monthly'

        for u in range(int(self.params_rank['p'])):
            self.params_rank['p'] = str(u + 1)
            a = requests.get(self.url_rank, headers=self.headers, params=self.params_rank)
            url_get = a.text
            url_json = json.loads(url_get)

            for dict1 in url_json['contents']:  # 获取图片id
                if dict1['illust_id'] not in self.m_set:
                    self.list_id.append(dict1['illust_id'])
                    self.m_set.add(dict1['illust_id'])
            # Pixiv.test(self)

    def url_get(self):  # 多线程获取url
        while True:
            self.glock.acquire()  # 加锁
            if len(self.list_id) == 0:
                self.glock.release()  # 释放锁
                break
            else:
                ID = self.list_id.pop(0)  # 提取列表第一个URL并删除
                self.glock.release()  # 释放锁
                test1 = 'https://www.pixiv.net/ajax/illust/' + str(ID) + '/pages?lang=zh'  # 查询真实ID包
                try:
                    url_text = requests.get(test1, headers=self.headers).text
                    url_testjson = json.loads(url_text)
                    for dict2 in url_testjson['body']:  # 获取url
                        self.list_url.append(dict2['urls']['original'])
                        url = dict2['urls']['original']
                        # print('获取链接:' + str(url))
                except requests.exceptions.ConnectionError:
                    print ('\033[95m请求好多,好频繁,那里(指p站服务器)受不了了...(换个ip吧)')
                    exit(0)

    # def test(self):   # 测试保存
    #     j = 1
    #     for i in self.dict_rank:
    #         self.headers['referer'] = 'https://www.pixiv.net/ranking.php?mode=monthly'
    #         pixiv_test = requests.get(i, headers=self.headers)
    #         path = self.params_rank['mode'] + '/' + str(j) + '.jpg'
    #         if not os.path.exists(self.params_rank['mode']):
    #             os.mkdir(self.params_rank['mode'])
    #         with open(path, 'wb') as f:
    #             f.write(pixiv_test.content)
    #             j += 1
    #             print(f'图片{i}正在保存...')

    def download(self):  # 多线程下载
        while True:
            self.glock.acquire()  # 加锁
            if len(self.list_url) == 0:
                self.glock.release()  # 释放锁
                break
            else:
                if not os.path.exists(
                        str(self.params_rank['mode']) + '-' + time.strftime("%Y-%m-%d", time.localtime())):
                    os.mkdir(str(self.params_rank['mode']) + '-' + time.strftime("%Y-%m-%d", time.localtime()))
                url = self.list_url.pop(0)  # 提取列表第一个URL并删除
                self.glock.release()  # 释放锁
                # 修改文件名
                if url[-3:] == 'jpg':
                    path = str(self.params_rank['mode']) + '-' + time.strftime("%Y-%m-%d",
                                                                               time.localtime()) + '/' + str(
                        self.i) + '.jpg'
                elif url[-3:] == 'png':
                    path = str(self.params_rank['mode']) + '-' + time.strftime("%Y-%m-%d",
                                                                               time.localtime()) + '/' + str(
                        self.i) + '.png'

                pixiv_img = requests.get(url, headers=self.headers)
                with open(path, 'wb') as f:
                    f.write(pixiv_img.content)
                    print('图片' + str(self.i) + '正在保存...' + path)
                    self.i += 1


def main():
    moder = input('请选择排行榜的类型（日:1/周:2/月:3）:')
    pn = input('请输入你想要多少页(50/页):')

    pixivc = Pixiv(moder, pn)
    # pixivc.login()
    pixivc.id_get()

    print('获取链接中...')
    for j in range(3):
        urlget = threading.Thread(target=pixivc.url_get())
        urlget.start()

    print('图片保存到' + pixivc.params_rank['mode'] + '-' + time.strftime("%Y-%m-%d", time.localtime()))
    for i in range(3):
        download = threading.Thread(target=pixivc.download())
        download.start()
    pixivc.dump_set()
    print('爬取结束,共保存' + str(pixivc.i - 1) + '张图片')


if __name__ == "__main__":
    main()
