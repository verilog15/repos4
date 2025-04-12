import copy
import os
import shutil
import subprocess
import unittest

import numpy as np
import onnx
import onnxruntime as ort
from packaging.version import Version
from transformers import AutoTokenizer

from neural_compressor import PostTrainingQuantConfig, quantization
from neural_compressor.adaptor.ox_utils.weight_only import awq_quantize, gptq_quantize, rtn_quantize
from neural_compressor.utils.constant import FP32


def Inference(model, data):
    sess = ort.InferenceSession(model.SerializeToString(), providers=["CPUExecutionProvider"])
    out = sess.run(None, data)
    return out


class DummyNLPDataloader(object):
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.sequence_a = "intel-extension-for-transformers is based in SH"
        self.sequence_b = "Where is intel-extension-for-transformers based? NYC or SH"
        self.encoded_dict = self.tokenizer(self.sequence_a, self.sequence_b, return_tensors="pt")
        self.encoded_dict["labels"] = 1
        self.batch_size = 1

    def __iter__(self):
        yield {
            "input_ids": self.encoded_dict["input_ids"].detach().cpu().numpy(),
            "attention_mask": self.encoded_dict["attention_mask"].detach().cpu().numpy(),
        }, self.encoded_dict["labels"]


class TestWeightOnlyAdaptor(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        cmd = (
            "optimum-cli export onnx --model hf-internal-testing/tiny-random-gptj --task text-generation --legacy gptj/"
        )
        p = subprocess.Popen(
            cmd, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )  # nosec
        p.communicate()

        self.gptj_model = onnx.load("gptj/decoder_model.onnx")
        self.gptj_fp16_model = None
        if "CUDAExecutionProvider" in ort.get_available_providers():
            cmd = "optimum-cli export onnx --model hf-internal-testing/tiny-random-gptj --task text-generation --legacy --fp16 --device cuda gptj_fp16/"
            p = subprocess.Popen(
                cmd, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )  # nosec
            p.communicate()
            self.gptj_fp16_model = onnx.load("gptj_fp16/decoder_model.onnx")
        self.gptj_dataloader = DummyNLPDataloader("hf-internal-testing/tiny-random-gptj")

    @classmethod
    def tearDownClass(self):
        shutil.rmtree("nc_workspace", ignore_errors=True)
        shutil.rmtree("gptj", ignore_errors=True)
        shutil.rmtree("gptj_fp16", ignore_errors=True)

    @unittest.skipIf("CUDAExecutionProvider" not in ort.get_available_providers(), "Skip cuda woq test")
    def test_RTN_quant_with_woq_op(self):
        conf = PostTrainingQuantConfig(
            approach="weight_only",
            device="gpu",
            backend="onnxrt_cuda_ep",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,
                        "group_size": 32,
                        "scheme": "sym",
                        "algorithm": "RTN",
                    },
                },
            },
        )
        # test fp16 model
        q_fp16_model = quantization.fit(self.gptj_fp16_model, conf)

        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_fp16_model.model, data)
            org_out = Inference(self.gptj_fp16_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())
        if Version(ort.__version__) > Version("1.16.1"):
            scale_tensor = [i for i in q_fp16_model.initializer() if i.name.endswith("_scale")]
            self.assertTrue(len(scale_tensor) > 0)
            self.assertEqual(scale_tensor[0].data_type, 10)
            self.assertTrue("MatMulNBits" in set([node.op_type for node in q_fp16_model.model.graph.node]))

    @unittest.skipIf("CUDAExecutionProvider" not in ort.get_available_providers(), "Skip cuda woq test")
    def test_AWQ_quant_with_woq_op(self):
        conf = PostTrainingQuantConfig(
            approach="weight_only",
            device="gpu",
            backend="onnxrt_cuda_ep",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,
                        "group_size": 32,
                        "scheme": "sym",
                        "algorithm": "AWQ",
                    },
                },
            },
            recipes={
                "awq_args": {"enable_auto_scale": True, "enable_mse_search": True},
            },
        )
        # test fp16 model
        q_fp16_model = quantization.fit(self.gptj_fp16_model, conf, calib_dataloader=self.gptj_dataloader)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_fp16_model.model, data)
            org_out = Inference(self.gptj_fp16_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())
        if Version(ort.__version__) > Version("1.16.1"):
            scale_tensor = [i for i in q_fp16_model.initializer() if i.name.endswith("_scale")]
            self.assertTrue(len(scale_tensor) > 0)
            self.assertEqual(scale_tensor[0].data_type, 10)
            self.assertTrue("MatMulNBits" in set([node.op_type for node in q_fp16_model.model.graph.node]))

    @unittest.skipIf("CUDAExecutionProvider" not in ort.get_available_providers(), "Skip cuda woq test")
    def test_GPTQ_quant_with_woq_op(self):
        conf = PostTrainingQuantConfig(
            approach="weight_only",
            device="gpu",
            backend="onnxrt_cuda_ep",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,
                        "group_size": 32,
                        "scheme": "sym",
                        "algorithm": "GPTQ",
                    },
                },
            },
        )
        q_fp16_model = quantization.fit(self.gptj_fp16_model, conf, calib_dataloader=self.gptj_dataloader)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_fp16_model.model, data)
            org_out = Inference(self.gptj_fp16_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())
        if Version(ort.__version__) > Version("1.16.1"):
            scale_tensor = [i for i in q_fp16_model.initializer() if i.name.endswith("_scale")]
            self.assertTrue(len(scale_tensor) > 0)
            self.assertEqual(scale_tensor[0].data_type, 10)
            self.assertTrue("MatMulNBits" in set([node.op_type for node in q_fp16_model.model.graph.node]))

    def test_RTN_quant(self):
        conf = PostTrainingQuantConfig(
            approach="weight_only",
        )
        q_model = quantization.fit(self.gptj_model, conf)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())

        conf = PostTrainingQuantConfig(
            approach="weight_only",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 8,  # 1-8 bits
                        "group_size": -1,  # -1 (per-channel)
                        "scheme": "sym",
                        "algorithm": "RTN",
                    },
                },
            },
        )
        q_model = quantization.fit(self.gptj_model, conf)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())

    def test_AWQ_quant(self):
        conf = PostTrainingQuantConfig(
            approach="weight_only",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,  # 1-8 bits
                        "group_size": -1,  # -1 (per-channel)
                        "scheme": "sym",
                        "algorithm": "AWQ",
                    },
                },
            },
            recipes={
                "awq_args": {"enable_auto_scale": True, "enable_mse_search": True},
            },
        )
        q_model = quantization.fit(self.gptj_model, conf, calib_dataloader=self.gptj_dataloader)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())

        conf = PostTrainingQuantConfig(
            approach="weight_only",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,  # 1-8 bits
                        "group_size": 32,
                        "scheme": "sym",
                        "algorithm": "AWQ",
                    },
                },
            },
            recipes={
                "awq_args": {"enable_auto_scale": False, "enable_mse_search": True},
            },
        )
        q_model = quantization.fit(self.gptj_model, conf, calib_dataloader=self.gptj_dataloader)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())

        conf = PostTrainingQuantConfig(
            approach="weight_only",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,  # 1-8 bits
                        "group_size": 32,
                        "scheme": "asym",
                        "algorithm": "AWQ",
                    },
                },
            },
            recipes={
                "awq_args": {"enable_auto_scale": True, "enable_mse_search": False},
            },
        )
        q_model = quantization.fit(self.gptj_model, conf, calib_dataloader=self.gptj_dataloader)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())

        awq_op_names = [
            i.name for i in q_model.nodes() if i.op_type.startswith("MatMul") and i.input[1].endswith("_Q4G32")
        ]
        conf = PostTrainingQuantConfig(
            approach="weight_only",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,  # 1-8 bits
                        "group_size": 32,
                        "scheme": "asym",
                        "algorithm": "RTN",
                    },
                },
            },
            op_name_dict={
                awq_op_names[0]: {"activation": {"dtype": ["fp32"]}, "weight": {"dtype": ["fp32"]}},
            },
        )
        q_model = quantization.fit(self.gptj_model, conf)
        rtn_op_names = [
            i.name for i in q_model.nodes() if i.op_type.startswith("MatMul") and i.input[1].endswith("_Q4G32")
        ]
        self.assertTrue(len(rtn_op_names) + 1, len(awq_op_names))

    def test_GPTQ_quant(self):
        conf = PostTrainingQuantConfig(
            approach="weight_only",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,  # 1-8 bits
                        "group_size": -1,  # -1 (per-channel)
                        "scheme": "sym",
                        "algorithm": "GPTQ",
                    },
                },
            },
        )
        q_model = quantization.fit(self.gptj_model, conf, calib_dataloader=self.gptj_dataloader)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())

        conf = PostTrainingQuantConfig(
            approach="weight_only",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,  # 1-8 bits
                        "group_size": 32,  # -1 (per-channel)
                        "scheme": "asym",
                        "algorithm": "GPTQ",
                    },
                },
            },
        )
        q_model = quantization.fit(self.gptj_model, conf, calib_dataloader=self.gptj_dataloader)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.7).all())

        conf = PostTrainingQuantConfig(
            approach="weight_only",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,  # 1-8 bits
                        "group_size": 32,
                        "scheme": "sym",
                        "algorithm": "GPTQ",
                    },
                },
            },
            recipes={
                "gptq_args": {"actorder": True, "mse": True, "perchannel": False},
            },
        )
        q_model = quantization.fit(self.gptj_model, conf, calib_dataloader=self.gptj_dataloader)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())

        gptq_op_names = [
            i.name for i in q_model.nodes() if i.op_type.startswith("MatMul") and i.input[1].endswith("_Q4G32")
        ]
        conf = PostTrainingQuantConfig(
            approach="weight_only",
            op_type_dict={
                ".*": {  # re.match
                    "weight": {
                        "bits": 4,  # 1-8 bits
                        "group_size": 32,
                        "scheme": "asym",
                        "algorithm": "RTN",
                    },
                },
            },
            op_name_dict={
                gptq_op_names[0]: {"activation": {"dtype": ["fp32"]}, "weight": {"dtype": ["fp32"]}},
            },
        )
        q_model = quantization.fit(self.gptj_model, conf)
        rtn_op_names = [
            i.name for i in q_model.nodes() if i.op_type.startswith("MatMul") and i.input[1].endswith("_Q4G32")
        ]
        self.assertTrue(len(rtn_op_names) + 1, len(gptq_op_names))

    def _test_woq_tune_common(self, fp32_model, datalaoder, eval_func, quant_level=1, **kwargs):
        from neural_compressor import quantization
        from neural_compressor.config import PostTrainingQuantConfig, TuningCriterion

        tuning_criterion = TuningCriterion(max_trials=5)

        fp32_model = copy.deepcopy(fp32_model)
        conf = PostTrainingQuantConfig(
            approach="weight_only", quant_level=quant_level, tuning_criterion=tuning_criterion, **kwargs
        )
        q_model = quantization.fit(
            fp32_model,
            conf,
            calib_dataloader=datalaoder,
            eval_func=eval_func,
        )
        self.assertIsNotNone(q_model)
        return q_model

    def _count_woq_matmul(self, q_model, bits=4, group_size=32):
        op_names = [
            i.name
            for i in q_model.nodes()
            if i.op_type.startswith("MatMul") and i.input[1].endswith("_Q{}G{}".format(bits, group_size))
        ]
        return len(op_names)

    def test_woq_tune(self):
        from functools import partial

        def fake_eval(model, eval_result_lst):
            acc = eval_result_lst.pop(0)
            return acc

        quant_levels = ["auto", 1]
        for quant_level in quant_levels:
            # Expect tuning ends with WOQ algorithm 'RTN_G32ASYM'
            partial_fake_eval = partial(fake_eval, eval_result_lst=[1, 1.1])
            woq_model_1 = self._test_woq_tune_common(
                self.gptj_model, self.gptj_dataloader, partial_fake_eval, quant_level
            )
            self.assertEqual(self._count_woq_matmul(woq_model_1), 31)

            # Expect tuning ends with WOQ algorithm 'GPTQ_G32ASYM'
            partial_fake_eval = partial(fake_eval, eval_result_lst=[1, 0.8, 1.1])
            woq_model_2 = self._test_woq_tune_common(
                self.gptj_model, self.gptj_dataloader, partial_fake_eval, quant_level
            )
            self.assertEqual(self._count_woq_matmul(woq_model_2), 31)

            # Expect tuning ends with WOQ algorithm 'GPTQ_G32ASYM_DISABLE_LAST_MATMUL'
            partial_fake_eval = partial(fake_eval, eval_result_lst=[1, 0.8, 0.8, 1.1])
            woq_model_3 = self._test_woq_tune_common(
                self.gptj_model, self.gptj_dataloader, partial_fake_eval, quant_level
            )
            self.assertEqual(self._count_woq_matmul(woq_model_3), 30)

            # Expect tuning ends with WOQ algorithm 'GPTQ_G128ASYM'
            partial_fake_eval = partial(fake_eval, eval_result_lst=[1, 0.8, 0.8, 0.8, 1.1])
            woq_model_4 = self._test_woq_tune_common(
                self.gptj_model, self.gptj_dataloader, partial_fake_eval, quant_level
            )
            self.assertEqual(self._count_woq_matmul(woq_model_4, group_size=128), 31)

            # Expect tuning ends with WOQ algorithm 'AWQ_G32ASYM'
            partial_fake_eval = partial(fake_eval, eval_result_lst=[1, 0.8, 0.8, 0.8, 0.8, 1.1])
            woq_model_5 = self._test_woq_tune_common(
                self.gptj_model, self.gptj_dataloader, partial_fake_eval, quant_level
            )
            self.assertEqual(self._count_woq_matmul(woq_model_5), 31)

        # test WOQ tuning with fallback
        partial_fake_eval = partial(fake_eval, eval_result_lst=[1, 1.1])
        woq_model = self._test_woq_tune_common(
            self.gptj_model,
            self.gptj_dataloader,
            partial_fake_eval,
            "auto",
            op_name_dict={"/transformer/h.*/attn/k_proj/MatMul": FP32},
        )
        self.assertEqual(self._count_woq_matmul(woq_model), 26)

        # test 8 bits WOQ
        partial_fake_eval = partial(fake_eval, eval_result_lst=[1, 1.1])
        woq_model = self._test_woq_tune_common(
            self.gptj_model,
            self.gptj_dataloader,
            partial_fake_eval,
            "auto",
            op_type_dict={".*": {"weight": {"bits": 8}}},
        )
        self.assertEqual(self._count_woq_matmul(woq_model, bits=8), 31)

    def test_woq_with_ModelProto_input(self):
        from neural_compressor.model.onnx_model import ONNXModel

        q4_node_config = {}
        template_config_q4 = {"bits": 4, "group_size": 32, "scheme": "sym"}
        template_config_fp32 = "fp32"
        for node in self.gptj_model.graph.node:
            if node.op_type in ["MatMul"]:
                if not all([ONNXModel(self.gptj_model).get_initializer(i) is None for i in node.input]):
                    q4_node_config[node.name] = template_config_q4
                else:
                    q4_node_config[node.name] = template_config_fp32

        q_model = rtn_quantize(self.gptj_model, q4_node_config)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())

        q_model = gptq_quantize(self.gptj_model, self.gptj_dataloader, q4_node_config)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())

        q_model = awq_quantize(self.gptj_model, self.gptj_dataloader, q4_node_config)
        for data, _ in self.gptj_dataloader:
            q_out = Inference(q_model.model, data)
            org_out = Inference(self.gptj_model, data)
            for q, org in zip(q_out, org_out):
                self.assertTrue((np.abs(q_out[0] - org_out[0]) < 0.5).all())


if __name__ == "__main__":
    unittest.main()
