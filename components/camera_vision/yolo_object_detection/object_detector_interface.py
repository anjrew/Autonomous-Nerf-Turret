import abc


class ObjectDetector(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_color_for_class_name(self):
        pass
    
    @abc.abstractmethod
    def detect(self):
        pass