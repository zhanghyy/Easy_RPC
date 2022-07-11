from .transport import TcpTransport, UdpTransport, ClientUdpTransport, RpcTransport
from .serialize import BinarySerialize, JsonSerialize
from multiprocessing import cpu_count


class RpcProtocal(object):

    __slots__ = ('transport')

    def __init__(self):
        self.transport = RpcTransport()

    def serialize(self, obj):
        serializer = None
        if self.serializeType == 'bin':
            serializer = BinarySerialize()
        elif self.serializeType == 'json':
            serializer = JsonSerialize()
        if serializer == None:
            raise Exception('unknown serializeType')
        return serializer.serialize(obj)

    def unserialize(self, msg):
        serializer = None
        if self.serializeType == 'bin':
            serializer = BinarySerialize()
        elif self.serializeType == 'json':
            serializer = JsonSerialize()
        if serializer == None:
            raise Exception('unknown serializeType')
        return serializer.unserialize(msg) 

    def parseRequest(self, package):
        func = package['func']
        args = package['args']
        kwargs = package['kwargs']
        return func, args, kwargs


class UdpProtocal(RpcProtocal):

    def __init__(self):
        pass


class TcpProtocal(RpcProtocal):
    
    def __init__(self, host, port, serializeType = 'bin', timeout = 10):
        RpcProtocal.__init__(self)
        self.serializeType = serializeType
        self.timeout = timeout
        self.transport = TcpTransport(host, port, timeout)


class UdpProtocal(RpcProtocal):

    def __init__(self, host, port, serializeType = 'bin', timeout = 10):
        RpcProtocal.__init__(self)
        self.serializeType = serializeType
        self.timeout = timeout
        self.transport = UdpTransport(host, port)


class ClientUdpProtocal(UdpProtocal):

    def __init__(self, host, port, serializeType = 'bin', timeout = 10):
        UdpProtocal.__init__(self, host, port, serializeType=serializeType, timeout=timeout)
        self.serializeType = serializeType
        self.host = host
        self.port = port
        self.timeout = timeout
        self.transport = ClientUdpTransport(host, port, timeout)
    
    def newTransport(self):
        self.transport.close()
        self.transport = ClientUdpTransport(self.host, self.port, self.timeout)