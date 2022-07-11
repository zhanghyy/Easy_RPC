# EasyRpc

- 基于python3的建议高效rpc框架，基于agileutil框架修改，仅保留Rpc部分功能代码，并修复因服务端重启导致客户端长连接异常的问题，新增异步调用功能

## 快速开始

myservice.py:

```Python hl_lines="2"
from bmai_easy_rpc.server import rpc

@rpc
def add(n1, n2):
    return n1 + n2
```

启动：

```shell
rpc --run myservice
```

请求

```
from bmai_easy_rpc.client import TcpRpcClient

cli = TcpRpcClient('127.0.0.1', 9988, timeout=10)
res = cli.add(1, 2)
print(res)
```

[文档](./DETAIL.md)
