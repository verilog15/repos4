import sys
import unittest

sys.path.insert(0, "./")

import torch
import torch.nn as nn
import torchvision

from neural_compressor import WeightPruningConfig
from neural_compressor.data import Datasets
from neural_compressor.data.dataloaders.pytorch_dataloader import PyTorchDataLoader
from neural_compressor.training import prepare_compression

local_types_config = [
    # {
    #     "start_step": 0,
    #     "end_step": 0,
    #     "pruning_type": "pattern_lock",
    #     "op_names": ["layer1.*"],
    #     "excluded_op_names": ["layer2.*"],
    #     "pruning_scope": "global",
    # },
    # {
    #     "start_step": 1,
    #     "end_step": 1,
    #     "target_sparsity": 0.5,
    #     "pruning_type": "snip_momentum_progressive",
    #     "pruning_frequency": 2,
    #     "op_names": ["layer2.*"],
    #     "pruning_scope": "local",
    #     "pattern": "4x1",
    #     "sparsity_decay_type": "exp",
    # },
    # {
    #     "start_step": 2,
    #     "end_step": 8,
    #     "target_sparsity": 0.8,
    #     "pruning_type": "snip_progressive",
    #     "pruning_frequency": 1,
    #     "op_names": ["layer3.*"],
    #     "pruning_scope": "local",
    #     "pattern": "16x1",
    #     "sparsity_decay_type": "cube",
    # },
    {
        "start_step": 0,
        "end_step": 0,
        "pruning_type": "pattern_lock",
        "op_names": ["layer4.*"],
        "pattern": "2:4",
        "pruning_scope": "global",
    },
]

fake_snip_config = WeightPruningConfig(
    local_types_config, target_sparsity=0.9, start_step=0, end_step=10, pruning_frequency=3, sparsity_decay_type="exp"
)


class TestPruningTypes(unittest.TestCase):
    model = torchvision.models.resnet18()

    def test_pruning_types(self):
        compression_manager = prepare_compression(model=self.model, confs=fake_snip_config)
        compression_manager.callbacks.on_train_begin()
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.SGD(self.model.parameters(), lr=0.0001)
        datasets = Datasets("pytorch")
        dummy_dataset = datasets["dummy"](shape=(10, 3, 224, 224), low=0.0, high=1.0, label=True)
        dummy_dataloader = PyTorchDataLoader(dummy_dataset)
        compression_manager.callbacks.on_train_begin()
        for epoch in range(2):
            self.model.train()
            compression_manager.callbacks.on_epoch_begin(epoch)
            local_step = 0
            for image, target in dummy_dataloader:
                compression_manager.callbacks.on_step_begin(local_step)
                output = self.model(image)
                loss = criterion(output, target)
                optimizer.zero_grad()
                loss.backward()
                compression_manager.callbacks.on_before_optimizer_step()
                optimizer.step()
                compression_manager.callbacks.on_after_optimizer_step()
                compression_manager.callbacks.on_step_end()
                local_step += 1
            compression_manager.callbacks.on_epoch_end()
        compression_manager.callbacks.on_train_end()
        compression_manager.callbacks.on_before_eval()
        compression_manager.callbacks.on_after_eval()

        # assert sparsity ratio
        from neural_compressor.compression.pruner.utils import parse_to_prune

        for config in compression_manager.conf.pruning.pruning_configs:
            zero_cnt = 0
            all_cnt = 0
            layers = list(parse_to_prune(config=config, model=self.model).keys())
            for layer in layers:
                layer_weight = self.model.state_dict()[layer + ".weight"]
                zero_cnt += (layer_weight == 0).sum().item()
                all_cnt += layer_weight.numel()
                sparsity = (layer_weight == 0.0).sum().item() / layer_weight.numel()
                # Test local sparsity
                print(layer, sparsity, (layer_weight == 0.0).sum().item(), layer_weight.numel())


if __name__ == "__main__":
    unittest.main()
