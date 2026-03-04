from abc import ABC, abstractmethod

class DisplayProvider(ABC):
    @abstractmethod
    def clear(self):
        pass
    
    @abstractmethod
    def write_string(self, text: str, x: int, y: int, set_pos: bool):
        pass
