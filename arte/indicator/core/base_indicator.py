from abc import ABCMeta, abstractmethod


class BaseIndicator(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        # candlemanager가 받아오는 데이터 중에서 지표를 만드는데 필요한 데이터를 사전에 정의한다.
        # self.data_name = []
        # self.data_value = {name: None for name in self.data_name}
        pass

    @abstractmethod
    def calc(self, data):
        #  지표 계산에 필요한 data 저장
        for name in self.data_name:
            self.data_value[name] = data.__getattribute__(name)
        # 해당 지표를 계산.