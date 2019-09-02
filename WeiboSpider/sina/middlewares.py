# encoding: utf-8
import random

import pymongo
from sina.settings import LOCAL_MONGO_PORT, LOCAL_MONGO_HOST, DB_NAME
import paramiko

global ready
ready = False


class CookieMiddleware(object):
    """
    每次请求都随机从账号池中选择一个账号去访问
    """

    def __init__(self):
        client = pymongo.MongoClient(LOCAL_MONGO_HOST, LOCAL_MONGO_PORT)
        self.account_collection = client[DB_NAME]['account']

    def process_request(self, request, spider):
        all_count = self.account_collection.find({'status': 'success'}).count()
        if all_count == 0:
            raise Exception('当前账号池为空')
        random_index = random.randint(0, all_count - 1)
        random_account = self.account_collection.find({'status': 'success'})[random_index]
        request.headers.setdefault('Cookie', random_account['cookie'])
        request.meta['account'] = random_account


class RedirectMiddleware(object):
    """
    检测账号是否正常
    302 / 403,说明账号cookie失效/账号被封，状态标记为error
    418,偶尔产生,需要再次请求
    """

    def __init__(self):
        client = pymongo.MongoClient(LOCAL_MONGO_HOST, LOCAL_MONGO_PORT)
        self.account_collection = client[DB_NAME]['account']

    def process_response(self, request, response, spider):
        http_code = response.status
        if http_code == 302 or http_code == 403:
            self.account_collection.find_one_and_update({'_id': request.meta['account']['_id']},
                                                        {'$set': {'status': 'error'}}, )
            return request
        elif http_code == 418:
            spider.logger.error('ip 被封了!!!请更换ip,或者停止程序...')
            pm.error += 1
            request.meta['proxy'] = None
            return request
        else:
            return response


from adslproxy import RedisClient


class ProxyManger:

    def __init__(self):
        global ready
        self.client = RedisClient(host='xxx', password='')
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(hostname='221.228.217.108', port=20304, username='root', password='xxx')
        stdin, stdout, stderr = self.ssh.exec_command('python3.4 adsl.py')
        result = stdout.read()
        result = result.decode()[:-1]
        self.proxy = result + ':8888'
        self.error = 0
        ready = True

    def get_random_proxy(self):
        global ready
        if ready is False:  # 拨号完成的判断
            return None
        error_threshold = 10
        if self.error > error_threshold:  # 如果出错数目超过阈值，即IP被封，则重新拨号
            ready = False
        self.ssh.connect(hostname='服务器IP', port=服务器端口, username='用户名', password='密码')
        stdin, stdout, stderr = self.ssh.exec_command('python3.4 adsl.py')
        result = stdout.read()  # 读取代码返回显示的IP字符串
        result = result.decode()[:-1]  # 去除换行符
        self.proxy = result + ':8888'  # 加上端口号
        ready = True
        self.error = 0
        if self.proxy is None:
            return None
        return 'http://' + self.proxy

    def add_error(self):
        self.error += 1


def get_random_proxy():
    client = RedisClient(host='45.117.101.219', password='')
    try:
        proxies = client.all()
        if 'adsl1' in proxies.keys():
            proxies = proxies['adsl1']
        else:
            return None
        return 'http://' + proxies
    except:
        return None


class ProxyMiddleware(object):

    def process_request(self, request, spider):
        global pm
        proxy = pm.get_random_proxy()
        print('Using Proxy:', proxy)
        request.meta['proxy'] = proxy


global pm
pm = ProxyManger()
