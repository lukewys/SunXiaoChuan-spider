# coding:utf-8
import re
import time
import requests
from requests.exceptions import ConnectionError, ReadTimeout
import platform

if platform.python_version().startswith('2.'):
    import commands as subprocess
elif platform.python_version().startswith('3.'):
    import subprocess
else:
    raise ValueError('python version must be 2 or 3')


ADSL_CYCLE = 100

# 拨号出错重试间隔
ADSL_ERROR_CYCLE = 5

# ADSL命令
ADSL_BASH = 'adsl-stop;adsl-start'
ADSL_START = 'pppoe-start'
ADSL_STOP = 'pppoe-stop'

# 代理运行端口
PROXY_PORT = 8888

# 拨号网卡
ADSL_IFNAME = 'ppp0'

# 测试URL
TEST_URL = 'http://www.baidu.com'

# 测试超时时间
TEST_TIMEOUT = 20

# API端口
API_PORT = 8000

def get_ip(ifname=ADSL_IFNAME):
    """
    获取本机IP
    :param ifname: 网卡名称
    :return:
    """
    (status, output) = subprocess.getstatusoutput('ifconfig')
    if status == 0:
        pattern = re.compile(ifname + '.*?inet.*?(\d+\.\d+\.\d+\.\d+).*?netmask', re.S)
        result = re.search(pattern, output)
        if result:
            ip = result.group(1)
            return ip


def adsl():
        """
	拨号主进程
        :return: None
        """
	while True:
            subprocess.getstatusoutput(ADSL_STOP)
            time.sleep(0.5)
            (status, output) = subprocess.getstatusoutput(ADSL_START)
            if status == 0:
                ip = get_ip()
                if ip:
                    proxy = '{ip}:{port}'.format(ip=ip, port=PROXY_PORT)
                    if test_proxy(proxy):
                        print(ip)
                    else:
       	       	       	pass
                else:
                    time.sleep(ADSL_ERROR_CYCLE)
            else:
                time.sleep(ADSL_ERROR_CYCLE)

def test_proxy(proxy):
        """
	测试代理
        :param proxy: 代理
        :return: 测试结果
        """
	try:
            response = requests.get(TEST_URL, proxies={
                'http': 'http://' + proxy,
                'https': 'https://' + proxy
            }, timeout=TEST_TIMEOUT)
            if response.status_code == 200:
                return True
        except (ConnectionError, ReadTimeout):
            return False

if __name__ == '__main__':
    adsl()
