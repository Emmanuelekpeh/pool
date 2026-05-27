import torch
import copy

def mutate_network(network, mutation_rate=0.1, mutation_scale=0.1):
    new_network = copy.deepcopy(network)
    with torch.no_grad():
        for param in new_network.parameters():
            if torch.rand(1).item() < mutation_rate:
                noise = torch.randn_like(param) * mutation_scale
                param.add_(noise)
    return new_network

def mesh_networks(net1, net2, mutation_rate=0.05, mutation_scale=0.1):
    """
    Combines weights of net1 and net2 (crossover) and applies slight mutation.
    """
    new_net = copy.deepcopy(net1)
    net2_state = net2.state_dict()
    
    with torch.no_grad():
        for name, param in new_net.named_parameters():
            param2 = net2_state[name]
            
            # Discrete crossover: randomly choose weights from net1 or net2
            mask = (torch.rand_like(param) > 0.5).float()
            param.copy_(mask * param + (1 - mask) * param2)
            
            # Slight mutation to maintain diversity
            if mutation_rate > 0:
                mutation_mask = (torch.rand_like(param) < mutation_rate).float()
                noise = torch.randn_like(param) * mutation_scale
                param.add_(mutation_mask * noise)
                
    return new_net
