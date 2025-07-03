from abc import ABC, abstractmethod
from numpy import ndarray

class LinkerKernel(ABC):
    @abstractmethod
    def forward(self, vec_a: ndarray, vec_b: ndarray) -> float:
        pass

