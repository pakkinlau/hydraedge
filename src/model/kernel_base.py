from abc import ABC
from abc import ABCMeta, abstractmethod
from numpy import ndarray

# LinkerKernel.forward(e_src,e_dst)
class LinkerKernel(ABC):
    @abstractmethod
    def forward(self, vec_a: ndarray, vec_b: ndarray) -> float:
        pass
