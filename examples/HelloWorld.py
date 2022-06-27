import sys, os
f = sys.path[0]
(head, tail) = os.path.split(f)
sys.path.append(head)
from rpc_rabbitmq.src.rpc_rabbitmq.RpcBaseMethod import RpcBaseMethod
from json import dumps
import time


class HelloWorld(RpcBaseMethod):
    '''
    Tester method for the RPC Server
    '''

    def __init__(self):
        super().__init__()
        self.queue = 'hello_world'

    def method(self, channel, pika_method, props, body):
        print('rec', time.time())
        self.response = dumps({'msg': 'Hello World'})
        super().method(channel, pika_method, props, body)
