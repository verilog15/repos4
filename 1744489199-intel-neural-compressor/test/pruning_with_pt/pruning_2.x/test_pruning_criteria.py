import unittest

import torch
import torch.nn as nn
import torchvision

from neural_compressor import WeightPruningConfig
from neural_compressor.data import Datasets
from neural_compressor.data.dataloaders.pytorch_dataloader import PyTorchDataLoader
from neural_compressor.training import prepare_compression


class TestPruningCriteria(unittest.TestCase):
    model = torchvision.models.resnet18()

    def test_pruning_criteria(self):
        local_configs = [
            {
                "op_names": ["layer1.*"],
                "target_sparsity": 0.4,
                "pattern": "8x2",
                "pruning_type": "magnitude_progressive",
                "pruning_scope": "local",
                "sparsity_decay_type": "cube",
            },
            {
                "op_names": ["layer2.*"],
                "target_sparsity": 0.45,
                "pattern": "2:4",
                "pruning_type": "snip",
                "start_step": 6,
                "end_step": 6,
            },
            {
                "op_names": ["layer3.*"],
                "excluded_op_names": ["downsample.*"],
                "target_sparsity": 0.7,
                "pattern": "4x1",
                "pruning_type": "snip_momentum_progressive",
                "pruning_frequency": 4,
                "min_sparsity_ratio_per_op": 0.5,
                "max_sparsity_ratio_per_op": 0.8,
            },
        ]
        config = WeightPruningConfig(
            local_configs, target_sparsity=0.8, sparsity_decay_type="cube", start_step=1, end_step=10
        )
        compression_manager = prepare_compression(model=self.model, confs=config)
        # compression_manager.callbacks.callbacks_list[0].pruners[0].progressive_configs['progressive_type'] = 'scores'
        # compression_manager.callbacks.callbacks_list[0].pruners[0].progressive_configs['use_global'] = False
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

    def test_pruning_criteria_for_ut(self):
        local_configs = [
            {
                "op_names": ["layer1.*"],
                "target_sparsity": 0.4,
                "pattern": "8x2",
                "pruning_type": "magnitude_progressive",
                "pruning_scope": "local",
                "sparsity_decay_type": "cube",
            },
            {
                "op_names": ["layer3.*"],
                "excluded_op_names": ["downsample.*"],
                "target_sparsity": 0.7,
                "pattern": "4x1",
                "pruning_type": "snip_momentum_progressive",
                "pruning_frequency": 4,
                "min_sparsity_ratio_per_op": 0.5,
                "max_sparsity_ratio_per_op": 0.8,
            },
        ]
        config = WeightPruningConfig(
            local_configs, target_sparsity=0.8, sparsity_decay_type="cube", start_step=1, end_step=10
        )
        compression_manager = prepare_compression(model=self.model, confs=config)
        compression_manager.callbacks.callbacks_list[0].pruners[0].progressive_configs["progressive_type"] = "scores"
        compression_manager.callbacks.callbacks_list[0].pruners[0].progressive_configs["use_global"] = False
        compression_manager.callbacks.callbacks_list[0].pruners[0].progressive_configs["progressive_type"] = "linear"
        compression_manager.callbacks.callbacks_list[0].pruners[0].progressive_configs["use_global"] = False
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


if __name__ == "__main__":
    unittest.main()
