from .protocal import TcpProtocal, UdpProtocal, RpcProtocal, ClientUdpProtocal
from .exception import FuncNotFoundException
from .discovery import DiscoveryConfig
from .discovery import ConsulRpcDiscovery
from .wrap import retryTimes
from .discovery import Instance
import socket
import threading
import uuid



class RpcThread(threading.Thread):
    def __init__(self, funmain, func, *args, **kwargs):
        super(RpcThread, self).__init__()
        self.funmain = funmain
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.status = True

    def run(self):
        try:
            self.result = self.funmain(self.func, *self.args, **self.kwargs)
        except Exception as e:
            print(e,type(e))
            self.result = e
            self.status = False

    def getresult(self, timeout=None):
        threading.Thread.join(self, timeout)
        if threading.Thread.is_alive(self):
            self.result = socket.timeout
            self.status = False
        return self.result, self.status


class RpcMiddleware(object):

    def __init__(self, id, fun):
        self.id = id
        self.result = fun

    def get(self, timeout=None):
        if not self.result:
            raise FuncNotFoundException('没有执行的函数')
        result, status = self.result.getresult(timeout)
        if status:
            return result
        else:
            raise result

    def __repr__(self):
        return self.id


class Address(object):
    __slots__ = ('host', 'port')

    def __init__(self, host, port):
        self.host = host
        self.port = port


class Callable(object):

    def __init__(self, rpcClient, remoteMethodName):
        self.rpcClient = rpcClient
        self.remoteMethodName = remoteMethodName

    def __call__(self, *args, **kwargs):
        return self.rpcClient.call(self.remoteMethodName, *args, **kwargs)

    def __getattr__(self, key):
        if key in dir(self):
            return getattr(self, key)
        return Callable(self.rpcClient, self.remoteMethodName + '.' + f"{key}")


class RpcClient(object):
    __slots__ = (
    'discoveryConfig', 'discovery', 'instanceIndex', 'protocalMap', 'isSync', 'syncInterval', 'protocal', 'servers',
    'serversCount', 'serversProtocalMap', 'serverIndex', 'lastServer', 'timeout')

    def __init__(self):
        self.discoveryConfig = None
        self.discovery = None
        self.instanceIndex = 0
        self.protocalMap = {}
        self.isSync = False
        self.syncInterval = 30
        self.protocal = RpcProtocal()
        self.servers = []
        self.serversCount = len(self.servers)
        self.serversProtocalMap = {}
        self.serverIndex = 0
        self.lastServer = ''
        self.timeout = 10

    def getInstance(self):
        instanceList = self.discovery.getInstanceList(self.discoveryConfig.serviceName)
        instanceLength = len(instanceList)
        if instanceLength == 0:
            raise Exception('no instance found')
        index = self.instanceIndex % instanceLength
        self.instanceIndex = self.instanceIndex + 1
        return instanceList[index]

    def refreshProtocal(self):
        if self.discovery:
            instance = self.getInstance()
            self.protocal = self.getProtocalInstance(instance)
        if self.servers:
            self.serversCount = len(self.servers)
            index = self.serverIndex % self.serversCount
            self.serverIndex = self.serverIndex + 1
            server = self.servers[index]
            self.lastServer = server
            self.protocal = self.serversProtocalMap[server]

    def getProtocalInstance(self, instance):
        # overide
        pass

    def setDiscoveryConfig(self, config: DiscoveryConfig):
        self.discoveryConfig = config
        self.discovery = ConsulRpcDiscovery(self.discoveryConfig.consulHost, self.discoveryConfig.consulPort)

    def close(self):
        self.protocal.transport.close()

    def __del__(self):
        self.close()

    def beforeCall(self):
        self.refreshProtocal()

    def debugGetLastServer(self):
        return self.lastServer

    @retryTimes(retryTimes=3)
    def call(self, func, *args, **kwargs):
        pass

    def __getattr__(self, key):
        # def remote_attr(*args, **kwargs):
        #    print(f'{key}方法不存在, 参数为:{args}, {kwargs}')
        #    return self.call(f'{key}', *args, **kwargs)
        # def remote_attr(*args, **kwargs):
        #    return Callable(self, f"{key}")
        if key in dir(self):
            return getattr(self, key)
        return Callable(self, f"{key}")


class TcpRpcClient(RpcClient):

    def __init__(self, host='', port=0, servers=[], timeout=10, keepconnect=True):
        RpcClient.__init__(self)
        self.host = host
        self.port = port
        self.keepconnect = keepconnect
        self.protocal = TcpProtocal(host, port, timeout=timeout)
        self.servers = servers
        self.timeout = timeout
        if len(self.servers) == 0 and self.host != '' and self.port != 0:
            self.servers = [host + ':' + str(port)]
        for server in self.servers:
            host, port = server.split(':')
            self.serversProtocalMap[server] = TcpProtocal(host, int(port), timeout=timeout)

    @retryTimes(retryTimes=3)
    def call(self, func, *args, **kwargs):
        try:
            self.beforeCall()
            self.protocal.transport.connect()
            package = {
                'func': func,
                'args': args,
                'kwargs': kwargs,
            }
            msg = self.protocal.serialize(package)
            self.protocal.transport.send(msg)
            respmsg = self.protocal.transport.recv()
            resp = self.protocal.unserialize(respmsg)
            if isinstance(resp, Exception):
                if not self.keepconnect: self.protocal.transport.close()
                raise resp
            if not self.keepconnect: self.protocal.transport.close()
            return resp
        except socket.timeout as ex:
            self.protocal.transport.close()
            raise ex
        except Exception as e:
            self.protocal.transport.close()
            raise e

    def apply_call(self, func, *args, **kwargs):
        id = str(uuid.uuid4())
        thr = RpcThread(self.call, func, *args, **kwargs)
        thr.start()
        return RpcMiddleware(id, thr)

    def getProtocalInstance(self, instance):
        key = "%s:%s:%s" % (instance.service, instance.address, instance.port)
        if key in self.protocalMap:
            return self.protocalMap.get(key)
        self.protocalMap[key] = TcpProtocal(instance.address, instance.port)
        return self.protocalMap[key]


class UdpRpcClient(RpcClient):

    def __init__(self, host='', port=0, servers=[], timeout=10):
        RpcClient.__init__(self)
        self.host = host
        self.port = port
        self.protocal = ClientUdpProtocal(host, port, timeout=timeout)
        self.servers = servers
        self.timeout = timeout
        if len(self.servers) == 0 and self.host != '' and self.port != 0:
            self.servers = [host + ':' + str(port)]
        for server in self.servers:
            host, port = server.split(':')
            self.serversProtocalMap[server] = ClientUdpProtocal(host, int(port), timeout=timeout)

    @retryTimes(retryTimes=3)
    def call(self, func, *args, **kwargs):
        try:
            self.beforeCall()
            package = {
                'func': func,
                'args': args,
                'kwargs': kwargs
            }
            msg = self.protocal.serialize(package)
            self.protocal.transport.send(msg)
            respmsg, _ = self.protocal.transport.recv()
            resp = self.protocal.unserialize(respmsg)
            if isinstance(resp, Exception):
                raise resp
            return resp
        except socket.timeout as ex:
            self.protocal.newTransport()
            raise ex

    def getProtocalInstance(self, instance):
        key = "%s:%s:%s" % (instance.service, instance.address, instance.port)
        if key in self.protocalMap:
            return self.protocalMap.get(key)
        self.protocalMap[key] = UdpProtocal(instance.address, instance.port)
        return self.protocalMap[key]

