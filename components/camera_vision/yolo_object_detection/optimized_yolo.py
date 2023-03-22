import torch

class OptimizedYOLO(torch.nn.Module):
    def __init__(self, optimized_model):
        super().__init__()
        self.model = optimized_model
    
    def forward(self, x, *args, **kwargs):
        res = self.model(x)
        return res[0], list(res[1:])
    