from abc import ABCMeta, abstractmethod
import logging

FORMAT = '%(asctime)s %(levelname)s: %(message)s'


class RpcBaseMethod(metaclass=ABCMeta):
    '''
    Base Method for the Rabbit Rpc Server \n
    Provides methods for override by child classes
    '''

    def __init__(self, level=logging.INFO):
        self.queue = None
        self.response_callback = None
        self.response = None
        self._logger = logging.getLogger(__name__)
        logging.basicConfig(level=level, format=FORMAT)

    @abstractmethod
    def method(self, channel, pika_method, props, body):
        '''
        Child clases implement functionality here
        '''
        self._logger.info('Sending Response...')
        self.response_callback(
            channel, props, pika_method, self.response)
