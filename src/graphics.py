"""
A module for various graphical functions
"""
from abc import ABCMeta, abstractmethod

class ProgressBar(metaclass=ABCMeta):
    """
    Represent the abstract notion of a progress bar
    """
    def __init__(self, max_value):
        self._max_value = max_value
    @abstractmethod
    def update(self, new_value):
        """
        Sets the value to the new value
        """
        pass

class NoProgressBar(ProgressBar):
    """
    A progress bar that does nothing
    """
    def __init_(self):
        super().__init__(0)
    def update(self, new_value):
        del self, new_value

class TerminalProgressBar(ProgressBar):
    """
    A progress bar that prints to the terminal
    """
    def __init__(self, max_value, n_cols=100):
        super().__init__(max_value)
        self.__total_dashes = n_cols - 2
    def update(self, new_value):
        dashes = round(self.__total_dashes * (new_value + 1) / self._max_value)
        print("\r|{}{}|".format("-" * dashes, " " * (self.__total_dashes - dashes)), end="")
