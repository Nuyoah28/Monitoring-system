import tensorrt as trt
import time

import torchvision.ops as ops
import torch
import cv2 as cv
from collections import namedtuple, OrderedDict
import numpy as np
from Yolov8.utils1 import format_img, draw_on_src, gstreamer_pipeline
import numpy as np


class LoadEngineModel:
    def __init__(self, model_path, confidence=0.7, nms_thresh=0.4):
        # 加载模型
        self._confidence = confidence
        self._nms_threshold = nms_thresh
        self._input_shape = (1, 3, 640, 640)
        self._N, self._C, self._H, self._W = self._input_shape
        logger = trt.Logger(trt.Logger.INFO)
        device = torch.device('cuda:0')
        Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
        self._bindings = OrderedDict()
        self._bindings_addrs = OrderedDict()
        self._context = None
        with open(model_path, 'rb') as f, trt.Runtime(logger) as runtime:
            model = runtime.deserialize_cuda_engine(f.read())
            # 适配TensorRT 10.x版本的API
            if hasattr(model, 'num_bindings'):
                # TensorRT 8.x 或 9.x
                num_bindings = model.num_bindings
                for index in range(num_bindings):
                    name = model.get_binding_name(index)
                    dtype = trt.nptype(model.get_binding_dtype(index))
                    shape = model.get_binding_shape(index)
                    data = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
                    self._bindings[name] = Binding(name, dtype, shape, data, int(data.data_ptr()))
            elif hasattr(model, 'nb_bindings'):
                # TensorRT 7.x 或更早版本
                num_bindings = model.nb_bindings
                for index in range(num_bindings):
                    name = model.get_binding_name(index)
                    dtype = trt.nptype(model.get_binding_dtype(index))
                    shape = model.get_binding_shape(index)
                    data = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
                    self._bindings[name] = Binding(name, dtype, shape, data, int(data.data_ptr()))
            else:
                # TensorRT 10.x 版本，使用新的API
                num_io_tensors = model.num_io_tensors
                for index in range(num_io_tensors):
                    name = model.get_tensor_name(index)
                    dtype = trt.nptype(model.get_tensor_dtype(name))
                    shape = model.get_tensor_shape(name)
                    data = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
                    self._bindings[name] = Binding(name, dtype, shape, data, int(data.data_ptr()))
            self._bindings_addrs = OrderedDict((n, d.ptr) for n, d in self._bindings.items())
            self._context = model.create_execution_context()

    def _model_process(self, img_src):
        # 获取处理的结果
        img_blob, dif_w, dif_h, factor = format_img(img_src)
        # print('预处理完毕')
        self._bindings_addrs['images'] = img_blob.data_ptr()
        self._context.execute_v2(list(self._bindings_addrs.values()))
        out_prob = self._bindings['output0'].data.squeeze().permute(1, 0)
        # print('得到推理结果')
        # 以下这段在GPU上操作, 并且要用矩阵操作, 可以节约时间, 处理成NMSBOXES函数可接受的数据格式
        values, idxs = torch.max(out_prob[:, 4:], dim=1)
        flag = values > self._confidence
        out_prob = out_prob[flag]
        out_prob[:, 0] -= out_prob[:, 2] / 2 + dif_w
        out_prob[:, 1] -= out_prob[:, 3] / 2 + dif_h
        # 得到x1, y1
        out_prob[:, 2] += out_prob[:, 0]
        out_prob[:, 3] += out_prob[:, 1]
        # 原3,4为宽高 现得到x2,y2 根据不同的nms算法的输入参数来进行调整
        out_prob[:, :4] *= factor
        out_prob[:, 4] = values[flag]  # 写入confidence
        out_prob[:, 5] = idxs[flag]
        # print('转移到cpu之前')
        boxes = out_prob[:, :4]
        scores = out_prob[:, 4]
        idxs = out_prob[:, 5]
        return boxes, scores, idxs  # 处理完后把数据做最后的NMS处理

    def _nms(self, boxes, scores, idxs):
        indices = ops.batched_nms(boxes, scores, idxs, self._nms_threshold)
        # print('NMS处理完成')
        boxes = boxes[indices]
        scores = scores[indices]
        idxs = idxs[indices]
        # print('得到boxes, ids之前')
        return boxes, scores, idxs

    def __call__(self, img_src):
        boxes, scores, idxs = self._model_process(img_src)
        boxes, scores, idxs = self._nms(boxes, scores, idxs)
        return boxes, scores, idxs


# def main():
#     video_setting = gstreamer_pipeline()
#     cap = cv.VideoCapture(video_setting, cv.CAP_GSTREAMER)
#     cap.set(cv.CAP_PROP_FPS, 30)
#     cap = cv.VideoCapture('image/fire.mp4')
#     infer = LoadEngineModel('fire_detector.engine')
#     print('模型加载成功！')
#     i = 0
#     try:
#         while 1:
#             f, img = cap.read()
#             img = cv.resize(img, (3280, 2464))
#             if not f: break
#             i += 1
#             if i % 4 == 0:
#                 i = 0
#                 # t_s = time.time()
#                 boxes, scores, idxs = infer(img)
#                 boxes, scores, idxs = boxes.cpu().numpy(), scores.cpu().numpy(), idxs.cpu().numpy()
#                 # t_e = time.time()
#                 # print(f"fps:{format(1 / (t_e - t_s), '.2f')}")
#                 draw_on_src(img, boxes, idxs)
#                 np_img = cv.resize(img, (640, 640))
#                 cv.imshow("1", np_img)
#                 if cv.waitKey(1) == ord('q'):
#                     break
#     finally:
#         if cap.isOpened():
#             cap.release()
#
#
# main()
