import torch
import torch.nn as nn

class FutureNetwork(nn.Module):
    def __init__(self, input_dim=72, output_dim=70): # 70 state + 2 action
        super(FutureNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim),
            nn.Tanh() # Outputs predicted future state
        )
        
    def forward(self, x):
        return self.net(x)
