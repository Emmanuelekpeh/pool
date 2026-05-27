import torch
import torch.nn as nn

class PolicyNetwork(nn.Module):
    def __init__(self, input_dim=70, output_dim=2):
        super(PolicyNetwork, self).__init__()
        self.layer1 = nn.Linear(input_dim, 64)
        self.layer2 = nn.Linear(64, 64)
        self.layer3 = nn.Linear(64, output_dim)
        self.relu = nn.ReLU()
        self.tanh = nn.Tanh()
        
    def forward(self, x):
        h1 = self.relu(self.layer1(x))
        h2 = self.relu(self.layer2(h1))
        out = self.tanh(self.layer3(h2))
        return out, h2
