class ControllerAction:
    
    """A class representing an action that can be taken by the controller."""
    x: int
    """A int between -10 and 10 representing the standardized azimuth angle of the turret"""
    y: int 
    """A int between -10 and 10 representing the standardized elevation angle of the turret"""
    is_firing: bool 
    """A bool representing whether or not the gun is firing"""
    
    def __init__(self, x: int, y: int, is_firing: bool):
        assert type(x) == int, "x must be an int"
        assert x >= -10 and x <= 10, "x must be between -10 and 10 but was: " + str(x) 
        self.x = x
        assert type(y) == int, "y must be an int"
        assert y >= -10 and y <= 10, "y must be between -10 and 10 but was" + str(x) 
        self.y = y
        assert isinstance(is_firing, bool), "is_firing must be a bool"
        self.is_firing = is_firing
        
    def __repr__(self) -> str:
        return f"ControllerAction(x={getattr(self,'x')}, y={getattr(self,'y')}, is_firing={getattr(self,'is_firing')})"