from abc import ABCMeta, abstractmethod


class RpcBaseMethod(metaclass=ABCMeta):
    '''
    Base Method for the Rabbit Rpc Server \n
    Provides methods for override by child classes
    '''

    def __init__(self):
        self.queue = None
        self.response_callback = None
        self.response = None

    @abstractmethod
    def method(self, channel, pika_method, props, body):
        '''
        Child clases implement functionality here
        '''
        self.response_callback(
            channel, props, pika_method, self.response)