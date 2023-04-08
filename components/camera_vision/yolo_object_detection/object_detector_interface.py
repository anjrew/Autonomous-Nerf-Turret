import abc
from typing import Tuple


class ObjectDetector(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_color_for_class_name(self, class_name: str) -> Tuple[int, int, int]:
        """Gets the color for a particular class by name""" 
        pass
    
    @abc.abstractmethod
    def detect(self):
        pass