
from typing import List, get_type_hints


class AiControllerArgs:
    """The arguments for the AiController"""
    target_padding: float
    search: bool
    target_type: str
    target_ids: List[str]
    
    def __init__(self, 
        target_padding: float,
        search: bool,
        target_type: str,
        target_ids: List[str] 
    ):  
        self.target_padding = target_padding
        self.search = search
        self.target_type = target_type
        self.target_ids = target_ids
     
        assert self.is_valid(), 'Invalid AiControllerArgs created'

    def is_valid(self):
        return all(getattr(self, prop, None) is not None for prop in get_type_hints(AiControllerArgs))