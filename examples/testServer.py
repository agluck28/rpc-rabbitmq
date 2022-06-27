import sys, os
f = sys.path[0]
(head, tail) = os.path.split(f)
sys.path.append(head)
from src.rpc_rabbitmq.RabbitRpc import RabbitRpcServer
from HelloWorld import HelloWorld

methods = [HelloWorld()]

server = RabbitRpcServer('testrpc', methods, 'localhost')

print('Starting Server...')

try:
    server.start()
except:
    server.close()