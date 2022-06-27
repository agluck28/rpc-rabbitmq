import sys, os
f = sys.path[0]
(head, tail) = os.path.split(f)
sys.path.append(head)
from src.rpc_rabbitmq.RabbitRpc import RabbitRpcClient
import threading
from RequestHelloWorld import RequestHelloWorld
import time

def main(client):
    request = RequestHelloWorld(client)
    while not client.ready:
        time.sleep(0.2)
        print('waiting to start...')
    print('Making Request...')
    request.make_request()

if __name__ == '__main__':

    client = RabbitRpcClient('testrpc', 'localhost')

    print('Starting Client...')
    try:
        cl_thread = threading.Thread(target=main, args=[client])
        cl_thread.start()
        client.start()
    except (RuntimeError, RuntimeWarning, KeyboardInterrupt, Exception) as e:
        print(e)
        client.close()
