# -*- coding: utf-8 -*-

# @Time    : 2022/3/30 21:35
# @Author  : Ben
# @Site    : 
# @File    : funconfig.py
# @Software: 同步函数信息到数据库
import queue
import requests
import random
import string
import json
import base64
from redis import StrictRedis
import socket
from .exception import FuncExistsError
import json

local_ip = socket.gethostbyname(socket.gethostname())


def get_conf(key):
    """
    加密，随机字符串+base64
    """
    b64key = base64.b64encode(key.encode('utf-8'))
    ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    random_b64key = ran_str + b64key.decode('utf-8')
    url = 'http://xxx.xxx.xxx.xxx:xxxx/api/dbconf/get?key={}'.format(random_b64key)
    infos = requests.get(url).json()
    infos = base64.b64decode(infos[8:]).decode('utf-8')
    infos = json.loads(infos)
    return infos


class FunPush(object):
    '''token校验'''

    def __init__(self):
        t_redis_host = get_conf('t_redis_host')
        t_redis_port = get_conf('t_redis_port')
        t_redis_password = get_conf('t_redis_password')
        self.dyredis = StrictRedis(host=t_redis_host, port=t_redis_port, db=12, password=t_redis_password)

    def __call__(self, funname, user='', project='RPA'):
        '''校验token,全局变量true_token中不存在则到数据库中查找
        funname  函数别名，可以为中文
        ip  IP或域名
        port   端口，   K8S中映射的端口
        queue   队列，用于consul
        user     函数归属人
        tag   Private  个人   Internal   某项目   Public     公共
        project   函数归属项目
        '''
        fun_key = f'rpa_project_func_{funname}_{user}_{project}'
        fun_info = {'funname': funname, 'name': funname,'ip': local_ip, 'port': 8888, 'queue': 'defule', 'user': None,
                    'tag': 'Internal', 'project': 'RPA'}
        if self.dyredis.setnx(fun_key, json.dumps(fun_info, ensure_ascii=False)):
            fun_info = json.loads(self.dyredis.get(fun_key))
            raise FuncExistsError(f'函数已存在:{fun_info}')


fun_push = FunPush()
