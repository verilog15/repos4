import os
import unittest

import torch
import torchvision
from packaging.version import Version

import neural_compressor.adaptor.pytorch as nc_torch
from neural_compressor import PostTrainingQuantConfig, quantization
from neural_compressor.adaptor.torch_utils.model_wrapper import WeightOnlyLinear
from neural_compressor.model import MODELS
from neural_compressor.model import Model as INCModel
from neural_compressor.model.torch_model import PyTorchModel

try:
    import intel_pytorch_extension as ipex

    TEST_IPEX = True
except:
    TEST_IPEX = False

PT_VERSION = nc_torch.get_torch_version()
if PT_VERSION >= Version("1.8.0-rc1"):
    FX_MODE = True
else:
    FX_MODE = False


class Model(torch.nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.fc1 = torch.nn.Linear(30, 40)
        self.fc2 = torch.nn.Linear(40, 30)
        self.fc3 = torch.nn.Linear(30, 5)

    def forward(self, x):
        out = self.fc1(x)
        out = self.fc2(out)
        out = self.fc3(out)
        return out


class TestPytorchModel(unittest.TestCase):
    framework = "pytorch"
    model = torchvision.models.quantization.resnet18()
    lpot_model = MODELS["pytorch"](model)

    def test_Model(self):
        model = torchvision.models.quantization.resnet18()
        inc_model = INCModel(model)
        self.assertTrue(isinstance(inc_model, PyTorchModel))

    def test_get_all_weight_name(self):
        assert len(list(self.lpot_model.get_all_weight_names())) == 62

    def test_get_weight(self):
        for name, param in self.model.named_parameters():
            if name == "layer4.1.conv2.weight":
                param.data.fill_(0.0)
            if name == "fc.bias":
                param.data.fill_(0.1)
        assert int(torch.sum(self.lpot_model.get_weight("layer4.1.conv2.weight"))) == 0
        assert torch.allclose(torch.sum(torch.tensor(self.lpot_model.get_weight("fc.bias"))), torch.tensor(100.0))

    def test_get_input(self):
        model = MODELS["pytorch"](torchvision.models.quantization.resnet18())
        model.model.eval().fuse_model()
        model.register_forward_pre_hook()
        rand_input = torch.rand(100, 3, 256, 256).float()
        model.model(rand_input)
        assert torch.equal(model.get_inputs("x"), rand_input)
        model.remove_hooks()

    def test_update_weights(self):
        self.lpot_model.update_weights("fc.bias", torch.zeros([1000]))
        assert int(torch.sum(self.lpot_model.get_weight("fc.bias"))) == 0

    def test_gradient(self):
        with self.assertRaises(AssertionError):
            self.lpot_model.get_gradient("fc.bias")

        shape = None
        for name, tensor in self.lpot_model._model.named_parameters():
            if name == "fc.bias":
                shape = tensor.shape
                tensor.grad = torch.randn(shape)
                break
        new_grad = torch.zeros(shape)
        self.lpot_model.update_gradient("fc.bias", new_grad)
        assert torch.equal(torch.tensor(self.lpot_model.get_gradient("fc.bias")), torch.zeros(shape))

        rand_input = torch.rand(100, 3, 256, 256).float()
        rand_input.grad = torch.ones_like(rand_input)
        assert torch.equal(torch.tensor(self.lpot_model.get_gradient(rand_input)), torch.ones_like(rand_input))

    def test_report_sparsity(self):
        df, total_sparsity = self.lpot_model.report_sparsity()
        self.assertTrue(total_sparsity > 0)
        self.assertTrue(len(df) == 22)

    def test_WeightOnlyLinear(self):
        model = Model()
        input = torch.randn(1, 30)
        conf = PostTrainingQuantConfig(
            approach="weight_only",
        )
        q_model = quantization.fit(model, conf)
        out1 = q_model(input)
        q_model.save("saved")
        model_size1 = os.path.getsize("saved/best_model.pt") / 1024
        print("FP32 Model size:{:.3f}M".format(model_size1))
        # test compress_bits = [8, 16, 32, 64]
        compression_dtype = [torch.int8, torch.int16, torch.int32, torch.int64]
        for dtype in compression_dtype:
            new_model = Model()
            inc_model = INCModel(new_model)
            compressed_model = inc_model.export_compressed_model(
                qweight_config_path="saved/qconfig.json",
                compression_dtype=dtype,
                scale_dtype=torch.float32,
                use_optimum_format=False,
            )
            out2 = q_model(input)
            torch.save(compressed_model.state_dict(), "saved/tmp.pt")
            model_size2 = os.path.getsize("saved/tmp.pt") / 1024
            print("WeightOnlyLinear Model size:{:.3f}M".format(model_size2))
            self.assertTrue(isinstance(compressed_model.fc1, WeightOnlyLinear))
            self.assertTrue(compressed_model.fc1.qweight.dtype == dtype)
            self.assertTrue(compressed_model.fc1.scales.dtype == torch.float32)
            self.assertTrue(model_size1 / model_size2 > 2)
            self.assertTrue(torch.all(torch.isclose(out1, out2, atol=5e-1)))

        # test compress_bits = [8, 16, 32, 64]
        compress_dims = [0, 1]
        for dim in compress_dims:
            new_model = Model()
            inc_model = INCModel(new_model)
            compressed_model = inc_model.export_compressed_model(
                qweight_config_path="saved/qconfig.json",
                compression_dim=dim,
                use_optimum_format=False,
            )
            out2 = q_model(input)
            torch.save(compressed_model.state_dict(), "saved/tmp.pt")
            model_size2 = os.path.getsize("saved/tmp.pt") / 1024
            print("WeightOnlyLinear Model size:{:.3f}M".format(model_size2))
            self.assertTrue(isinstance(compressed_model.fc1, WeightOnlyLinear))
            if dim == 1:
                self.assertTrue(compressed_model.fc1.qweight.shape[1] != compressed_model.fc1.in_features)
            else:
                self.assertTrue(compressed_model.fc1.qweight.shape[0] != compressed_model.fc1.out_features)
            self.assertTrue(model_size1 / model_size2 > 2)
            self.assertTrue(torch.all(torch.isclose(out1, out2, atol=5e-1)))

        # test half dtype
        new_model = Model()
        inc_model = INCModel(new_model)
        compressed_model = inc_model.export_compressed_model(
            qweight_config_path="saved/qconfig.json",
        )
        out2 = q_model(input)
        torch.save(compressed_model.state_dict(), "saved/tmp.pt")
        model_size2 = os.path.getsize("saved/tmp.pt") / 1024
        print("WeightOnlyLinear Model size:{:.3f}M".format(model_size2))
        self.assertTrue(isinstance(compressed_model.fc1, WeightOnlyLinear))
        self.assertTrue(compressed_model.fc1.scales.dtype == torch.float16)
        self.assertTrue(model_size1 / model_size2 > 2)
        self.assertTrue(torch.all(torch.isclose(out1, out2, atol=5e-1)))


if __name__ == "__main__":
    unittest.main()
