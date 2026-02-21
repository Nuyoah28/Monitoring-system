import warnings
from collections import namedtuple
from functools import partial
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import onnxruntime

try:
    import tensorrt as trt
except Exception:
    trt = None
import torch

warnings.filterwarnings(action='ignore', category=DeprecationWarning)


class TRTWrapper(torch.nn.Module):
    dtype_mapping = {}

    def __init__(self, weight: Union[str, Path],
                 device: Optional[torch.device]):
        super().__init__()
        weight = Path(weight) if isinstance(weight, str) else weight
        assert weight.exists() and weight.suffix in ('.engine', '.plan')
        if isinstance(device, str):
            device = torch.device(device)
        elif isinstance(device, int):
            device = torch.device(f'cuda:{device}')
        self.weight = weight
        self.device = device
        self.stream = torch.cuda.Stream(device=device)
        self.__update_mapping()
        self.__init_engine()
        self.__init_bindings()

    def __update_mapping(self):
        self.dtype_mapping.update({
            trt.bool: torch.bool,
            trt.int8: torch.int8,
            trt.int32: torch.int32,
            trt.float16: torch.float16,
            trt.float32: torch.float32
        })

    def __init_engine(self):
        logger = trt.Logger(trt.Logger.ERROR)
        self.log = partial(logger.log, trt.Logger.ERROR)
        trt.init_libnvinfer_plugins(logger, namespace='')
        self.logger = logger
        with trt.Runtime(logger) as runtime:
            model = runtime.deserialize_cuda_engine(self.weight.read_bytes())

        context = model.create_execution_context()

        # 适配TensorRT 10.x版本的API
        if hasattr(model, 'num_bindings'):
            # TensorRT 8.x 或 9.x
            num_bindings = model.num_bindings
            names = [model.get_binding_name(i) for i in range(num_bindings)]
        elif hasattr(model, 'nb_bindings'):
            # TensorRT 7.x 或更早版本
            num_bindings = model.nb_bindings
            names = [model.get_binding_name(i) for i in range(num_bindings)]
        else:
            # TensorRT 10.x 版本，使用新的API
            num_io_tensors = model.num_io_tensors
            names = [model.get_tensor_name(i) for i in range(num_io_tensors)]

        num_inputs, num_outputs = 0, 0

        for i in range(len(names)):
            if hasattr(model, 'binding_is_input'):
                # 旧版本TensorRT
                if model.binding_is_input(i):
                    num_inputs += 1
                else:
                    num_outputs += 1
            else:
                # TensorRT 10.x，需要使用新API判断输入输出
                # 通过其他方式判断，比如通过名称模式或通过实际的tensor模式
                tensor_name = names[i]
                # 简单的启发式判断：通常输入tensor名称包含"input"，但这不是绝对的
                # 更准确的方式需要根据具体模型来判断
                try:
                    # 尝试使用TensorRT 10.x的新API判断输入输出
                    if model.get_tensor_mode(tensor_name) == trt.TensorIOMode.INPUT:
                        num_inputs += 1
                    else:
                        num_outputs += 1
                except:
                    # 如果无法获取tensor mode，则按默认顺序分配（通常是先输入后输出）
                    # 这种情况下我们先假设有固定的输入输出数量
                    if i < 1:  # 假设第一个是输入（通常对于YOLO模型来说是图像输入）
                        num_inputs += 1
                    else:
                        num_outputs += 1

        self.is_dynamic = -1 in model.get_binding_shape(0)

        self.model = model
        self.context = context
        self.input_names = names[:num_inputs]
        self.output_names = names[num_inputs:]
        self.num_inputs = num_inputs
        self.num_outputs = num_outputs
        self.num_bindings = num_inputs + num_outputs
        self.bindings: List[int] = [0] * self.num_bindings

    def __init_bindings(self):
        Binding = namedtuple('Binding', ('name', 'dtype', 'shape'))
        inputs_info = []
        outputs_info = []

        for i, name in enumerate(self.input_names):
            assert self.model.get_binding_name(i) == name
            dtype = self.dtype_mapping[self.model.get_binding_dtype(i)]
            shape = tuple(self.model.get_binding_shape(i))
            inputs_info.append(Binding(name, dtype, shape))

        for i, name in enumerate(self.output_names):
            i += self.num_inputs
            assert self.model.get_binding_name(i) == name
            dtype = self.dtype_mapping[self.model.get_binding_dtype(i)]
            shape = tuple(self.model.get_binding_shape(i))
            outputs_info.append(Binding(name, dtype, shape))
        self.inputs_info = inputs_info
        self.outputs_info = outputs_info
        if not self.is_dynamic:
            self.output_tensor = [
                torch.empty(o.shape, dtype=o.dtype, device=self.device)
                for o in outputs_info
            ]

    def forward(self, *inputs):

        assert len(inputs) == self.num_inputs

        contiguous_inputs: List[torch.Tensor] = [
            i.contiguous() for i in inputs
        ]

        for i in range(self.num_inputs):
            self.bindings[i] = contiguous_inputs[i].data_ptr()
            if self.is_dynamic:
                self.context.set_binding_shape(
                    i, tuple(contiguous_inputs[i].shape))

        # create output tensors
        outputs: List[torch.Tensor] = []

        for i in range(self.num_outputs):
            j = i + self.num_inputs
            if self.is_dynamic:
                shape = tuple(self.context.get_binding_shape(j))
                output = torch.empty(
                    size=shape,
                    dtype=self.output_dtypes[i],
                    device=self.device)

            else:
                output = self.output_tensor[i]
            outputs.append(output)
            self.bindings[j] = output.data_ptr()

        self.context.execute_async_v2(self.bindings, self.stream.cuda_stream)
        self.stream.synchronize()

        return tuple(outputs)


class ORTWrapper(torch.nn.Module):

    def __init__(self, weight: Union[str, Path],
                 device: Optional[torch.device]):
        super().__init__()
        weight = Path(weight) if isinstance(weight, str) else weight
        assert weight.exists() and weight.suffix == '.onnx'

        if isinstance(device, str):
            device = torch.device(device)
        elif isinstance(device, int):
            device = torch.device(f'cuda:{device}')
        self.weight = weight
        self.device = device
        self.__init_session()
        self.__init_bindings()

    def __init_session(self):
        providers = ['CPUExecutionProvider']
        if 'cuda' in self.device.type:
            providers.insert(0, 'CUDAExecutionProvider')

        session = onnxruntime.InferenceSession(
            str(self.weight), providers=providers)
        self.session = session

    def __init_bindings(self):
        Binding = namedtuple('Binding', ('name', 'dtype', 'shape'))
        inputs_info = []
        outputs_info = []
        self.is_dynamic = False
        for i, tensor in enumerate(self.session.get_inputs()):
            if any(not isinstance(i, int) for i in tensor.shape):
                self.is_dynamic = True
            inputs_info.append(
                Binding(tensor.name, tensor.type, tuple(tensor.shape)))

        for i, tensor in enumerate(self.session.get_outputs()):
            outputs_info.append(
                Binding(tensor.name, tensor.type, tuple(tensor.shape)))
        self.inputs_info = inputs_info
        self.outputs_info = outputs_info
        self.num_inputs = len(inputs_info)

    def forward(self, *inputs):

        assert len(inputs) == self.num_inputs

        contiguous_inputs: List[np.ndarray] = [
            i.contiguous().cpu().numpy() for i in inputs
        ]

        if not self.is_dynamic:
            # make sure input shape is right for static input shape
            for i in range(self.num_inputs):
                assert contiguous_inputs[i].shape == self.inputs_info[i].shape

        outputs = self.session.run([o.name for o in self.outputs_info], {
            j.name: contiguous_inputs[i]
            for i, j in enumerate(self.inputs_info)
        })

        return tuple(torch.from_numpy(o).to(self.device) for o in outputs)
