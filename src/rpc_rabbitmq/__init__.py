try:
    from RabbitRpc import RabbitRpcClient, RabbitRpcServer
    from RpcBaseRequest import RpcBaseRequest
    from RpcBaseMethod import RpcBaseMethod
except:
    from .RabbitRpc import RabbitRpcClient, RabbitRpcServer
    from .RpcBaseRequest import RpcBaseRequest
    from .RpcBaseMethod import RpcBaseMethod
