import sys, os
f = sys.path[0]
(head, tail) = os.path.split(f)
sys.path.append(head)
from rpc_rabbitmq.src.rpc_rabbitmq.RpcBaseRequest import RpcBaseRequest

class RequestHelloWorld(RpcBaseRequest):

    def __init__(self, RpcClient, timeout_ms: int = 20000):
        super().__init__(RpcClient, timeout_ms)
        self.routing_key = 'hello_world'
        self.request = 'test'

    def make_request(self):
        response = super().make_request()
        self._logger.info('Received response: %s', response['msg'])