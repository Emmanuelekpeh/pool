import torch
import torch.nn as nn

class DirectorNetwork(nn.Module):
    def __init__(self, input_dim=206): # 70 state + 2 action + 64 hidden + 70 future
        super(DirectorNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Tanh() # Outputs score between -1 and 1
        )
        
    def forward(self, x):
        return self.net(x)
