import threading
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

class ThreadExecutor(threading.Thread, Generic[T]):
    """Thread class with a result."""
    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self.target = target
        self.args = kwargs['args']
        self.kwargs = kwargs
        self.result: Optional[T] = None # type: ignore

    def run(self) -> None:
        self.result: T = self.target(*self.args)
