from src.rpc_rabbitmq.RpcBaseMethod import RpcBaseMethod
from json import dumps


class HelloWorld(RpcBaseMethod):
    '''
    Tester method for the RPC Server
    '''

    def __init__(self):
        super().__init__()
        self.queue = 'hello_world'

    def method(self, channel, pika_method, props, body):
        self.response = dumps({'msg': 'Hello World'})
        super().method(channel, pika_method, props, body)
