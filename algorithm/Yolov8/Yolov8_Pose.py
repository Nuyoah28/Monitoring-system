import math
from collections import namedtuple, OrderedDict
import time
import cv2
import numpy as np
import tensorrt as trt
import torch
from torchvision import ops

from Yolov8.main import LoadEngineModel
from Yolov8.utils import format_img, gstreamer_pipeline
from Yolov8.utils1 import format_img, draw_on_src, gstreamer_pipeline

KPS_COLORS = [[0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0],
              [255, 128, 0], [255, 128, 0], [255, 128, 0], [255, 128, 0],
              [255, 128, 0], [255, 128, 0], [51, 153, 255], [51, 153, 255],
              [51, 153, 255], [51, 153, 255], [51, 153, 255], [51, 153, 255]]

SKELETON = [[16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12], [7, 13],
            [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3], [1, 2], [1, 3],
            [2, 4], [3, 5], [4, 6], [5, 7]]

LIMB_COLORS = [[51, 153, 255], [51, 153, 255], [51, 153, 255], [51, 153, 255],
               [255, 51, 255], [255, 51, 255], [255, 51, 255], [255, 128, 0],
               [255, 128, 0], [255, 128, 0], [255, 128, 0], [255, 128, 0],
               [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0], [0, 255, 0],
               [0, 255, 0], [0, 255, 0]]

NUM_1 = 0


class LoadPoseEngine:
    def __init__(self, model_path, confidence=0.6, nms_thresh=0.4):
        device = torch.device('cuda:0')  # default
        logger = trt.Logger(trt.Logger.INFO)
        Binding = namedtuple('Binding', ('name', 'dtype', 'shape', 'data', 'ptr'))
        # 加载模型
        self.confidence = confidence
        self.nms_threshold = nms_thresh
        self.input_shape = (1, 3, 640, 480)  # default
        self.N, self.C, self.H, self.W = self.input_shape
        self.bindings = OrderedDict()
        self.bindings_addrs = OrderedDict()
        self.context = None
        self.num_nodes = 17  # 关节点的个数
        self.dif_w, self.dif_h, self.factor = 0, 0, 1
        with open(model_path, 'rb') as f, trt.Runtime(logger) as runtime:
            model = runtime.deserialize_cuda_engine(f.read())
            if model is None:
                print("模型加载失败!!")
            # 适配TensorRT 10.x版本的API
            if hasattr(model, 'num_bindings'):
                # TensorRT 8.x 或 9.x
                num_bindings = model.num_bindings
                for index in range(num_bindings):
                    name = model.get_binding_name(index)
                    dtype = trt.nptype(model.get_binding_dtype(index))
                    shape = model.get_binding_shape(index)
                    data = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
                    self.bindings[name] = Binding(name, dtype, shape, data, int(data.data_ptr()))
            elif hasattr(model, 'nb_bindings'):
                # TensorRT 7.x 或更早版本
                num_bindings = model.nb_bindings
                for index in range(num_bindings):
                    name = model.get_binding_name(index)
                    dtype = trt.nptype(model.get_binding_dtype(index))
                    shape = model.get_binding_shape(index)
                    data = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
                    self.bindings[name] = Binding(name, dtype, shape, data, int(data.data_ptr()))
            else:
                # TensorRT 10.x 版本，使用新的API
                num_io_tensors = model.num_io_tensors
                for index in range(num_io_tensors):
                    name = model.get_tensor_name(index)
                    dtype = trt.nptype(model.get_tensor_dtype(name))
                    shape = model.get_tensor_shape(name)
                    data = torch.from_numpy(np.empty(shape, dtype=dtype)).to(device)
                    self.bindings[name] = Binding(name, dtype, shape, data, int(data.data_ptr()))
            self.bindings_addrs = OrderedDict((n, d.ptr) for n, d in self.bindings.items())
            self.context = model.create_execution_context()

    def _model_process(self, img_src):
        # 获取处理的结果
        img_blob, dif_w, dif_h, factor = format_img(img_src)
        self.dif_w, self.dif_h, self.factor = dif_w, dif_h, factor
        # print('预处理完毕')
        self.bindings_addrs['images'] = img_blob.data_ptr()
        self.context.execute_v2(list(self.bindings_addrs.values()))
        out_prob = self.bindings['output0'].data.squeeze().permute(1, 0)

        # 以下这段在GPU上操作, 并且要用矩阵操作, 可以节约时间, 处理成NMSBOXES函数可接受的数据格式
        flag = out_prob[:, 4] > self.confidence
        out_prob = out_prob[flag]
        # 得到x1, y1
        out_prob[:, 0] -= out_prob[:, 2] / 2 + dif_w
        out_prob[:, 1] -= out_prob[:, 3] / 2 + dif_h
        # 得到x2, y2
        out_prob[:, 2] += out_prob[:, 0]
        out_prob[:, 3] += out_prob[:, 1]
        out_prob[:, :4] *= factor
        # 原3,4为宽高 现得到x2,y2 根据不同的nms算法的输入参数来进行调整
        bboxes = out_prob[:, :4]
        scores = out_prob[:, 4]
        points = out_prob[:, 5:]

        return bboxes, scores, points  # 处理完后把数据做最后的NMS处理

    def _nms(self, bboxes, scores, points):
        indices = ops.nms(bboxes, scores, self.nms_threshold)
        # print('NMS处理完成')
        bboxes = bboxes[indices]
        scores = scores[indices]
        points = points[indices]

        # 处理关节点的正确位置
        for i in range(self.num_nodes):
            points[:, i * 3] = (points[:, i * 3] - self.dif_w) * self.factor
            points[:, i * 3 + 1] = (points[:, i * 3 + 1] - self.dif_h) * self.factor
            points[:, i * 3: i * 3 + 2] = torch.round(points[:, i * 3: i * 3 + 2])
        # ----
        # points shape is [N, 17, 3]
        # N is number of poses, 17 is keypoints, 3 is (x, y, confidence)
        keypoint_conf = torch.zeros((points.shape[0], self.num_nodes))
        for i in range(self.num_nodes):
            keypoint_conf[:, i] = points[:, i * 3 + 2]
        keypoint_conf_sum = keypoint_conf.sum(dim=1)
        # print(keypoint_conf_sum)
        valid_poses_index = np.where(keypoint_conf_sum > 10)[0]
        bboxes = bboxes[valid_poses_index]
        scores = scores[valid_poses_index]
        points = points[valid_poses_index]
        return torch.round(bboxes), scores, points

    def __call__(self, img_src):
        self._model_process(img_src)
        bboxes, scores, points = self._model_process(img_src)
        bboxes, scores, points = self._nms(bboxes, scores, points)
        return bboxes, scores, points

    def draw_pose(self, np_img, bboxes, scores, points):
        for (bbox, score, kpt) in zip(bboxes, scores, points):
            # num = NUM_1
            cv2.rectangle(np_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 4)
            for i in range(19):
                if i < 17:
                    # NUM_1 += 1
                    px, py, ps = kpt[i * 3: i * 3 + 3]
                    if ps > self.confidence:
                        kcolor = KPS_COLORS[i]
                        px, py = int(round(px)), int(round(py))
                        radius = 3
                        cv2.circle(np_img, (px, py), radius, kcolor, -1)
                        cv2.putText(np_img, str(i), (px, py), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                xi, yi = SKELETON[i]
                pos1_s = kpt[(xi - 1) * 3 + 2]
                pos2_s = kpt[(yi - 1) * 3 + 2]
                if pos1_s > self.confidence and pos2_s > self.confidence:
                    limb_color = LIMB_COLORS[i]
                    pos1_x, pos1_y = int(round(kpt[(xi - 1) * 3])), int(round(kpt[(xi - 1) * 3 + 1]))
                    pos2_x, pos2_y = int(round(kpt[(yi - 1) * 3])), int(round(kpt[(yi - 1) * 3 + 1]))
                    cv2.line(np_img, (pos1_x, pos1_y), (pos2_x, pos2_y),
                             limb_color, 4)


# ---------------------------------------------------------#
#   main: YOLOv8-Pose + ST-GCN++ + Mamba-YOLO-World
#   - ST-GCN++ handles: fall (caseType=4), punch (caseType=7), wave (caseType=12)
#   - Hand-written rules: danger zone (caseType=1) - position based
#   - Mamba-YOLO handles: fire, smoke, garbage, ice, ebike, vehicle
# ---------------------------------------------------------#
def main(infer, infer1, action_recognizer, np_img, TYPE_LIST, AREA_LIST):
    from common import monitor as monitorCommon
    # Simplified preList: only danger zone + Mamba-YOLO state
    indices_danger, fire_indices, smoke_indices = monitorCommon.preList
    try:
        # ---------------------------------------------------------#
        #   Pose estimation + ST-GCN++ action recognition
        # ---------------------------------------------------------#
        list0 = False   # danger zone
        list3 = False   # fall
        list6 = False   # punch
        list11 = False  # wave
        bboxes = None
        points = None

        if TYPE_LIST[0] or TYPE_LIST[3] or TYPE_LIST[6] or TYPE_LIST[11]:
            bboxes, scores, points = infer(np_img)
            scores = scores.cpu().numpy()
            bboxes = bboxes.to(torch.int32).cpu().numpy()
            points = points.cpu().numpy()
            infer.draw_pose(np_img, bboxes, scores, points)

            # --- ST-GCN++ action recognition (replaces hand-written if-else rules) ---
            if TYPE_LIST[3] or TYPE_LIST[6] or TYPE_LIST[11]:
                action_result = action_recognizer.predict(points, bboxes)
                if TYPE_LIST[3]:
                    list3 = action_result.get('fall', False)
                if TYPE_LIST[6]:
                    list6 = action_result.get('punch', False)
                if TYPE_LIST[11]:
                    list11 = action_result.get('wave', False)

                # Draw action labels on image
                if bboxes is not None and len(bboxes) > 0:
                    x, y = int(bboxes[0, 0]), int(bboxes[0, 1])
                    if list3:
                        cv2.putText(np_img, "fall", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (36, 255, 12), 2)
                    if list6:
                        cv2.putText(np_img, "punch", (x, y - 40), cv2.FONT_HERSHEY_SIMPLEX, 2, (36, 255, 12), 2)
                    if list11:
                        cv2.putText(np_img, "wave", (x, y - 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (36, 255, 12), 2)

        # ---------------------------------------------------------#
        #   Danger zone detection (keep hand-written, position-based)
        # ---------------------------------------------------------#
        if TYPE_LIST[0] and bboxes is not None and points is not None and len(bboxes) > 0:
            M1 = 0.3
            M2 = 0.7
            center_x_up = (points[:, 5 * 3] + points[:, 6 * 3]) / 2
            center_x_down = (points[:, 11 * 3] + points[:, 12 * 3]) / 2
            center_y_up = (points[:, 5 * 3 + 1] + points[:, 6 * 3 + 1]) / 2
            center_y_down = (points[:, 11 * 3 + 1] + points[:, 12 * 3 + 1]) / 2
            center_x = (center_x_up * M1 + center_x_down * M2) / 2
            center_y = (center_y_up * M1 + center_y_down * M2) / 2
            bound_x_left = AREA_LIST[0][0]
            bound_x_right = AREA_LIST[1][0]
            bound_y_up = AREA_LIST[0][1]
            bound_y_down = AREA_LIST[1][1]
            indices_danger = np.where(
                (center_x > bound_x_left) & (center_x < bound_x_right) &
                (center_y > bound_y_up) & (center_y < bound_y_down)
            )[0]
        if indices_danger is None:
            indices_danger = []
        if len(indices_danger) > 0 and TYPE_LIST[0]:
            list0 = True
            try:
                if len(indices_danger) <= bboxes.shape[0]:
                    for i in range(indices_danger.shape[0]):
                        index = indices_danger[i]
                        x = int(bboxes[index, 0])
                        y = int(bboxes[index, 1])
                        cv2.putText(np_img, "danger", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (36, 255, 12), 2)
            except Exception:
                pass

        # ---------------------------------------------------------#
        #   Mamba-YOLO-World detection (fire/smoke/garbage/ice/ebike/vehicle)
        # ---------------------------------------------------------#
        list1 = False   # smoke
        list4 = False   # fire
        garbage_indices = None
        ice_indices = None
        ebike_indices = None
        vehicle_indices = None
        if TYPE_LIST[4] or TYPE_LIST[1] or TYPE_LIST[7] or TYPE_LIST[8] or TYPE_LIST[9] or TYPE_LIST[10]:
            boxes1, scores1, idxs1 = infer1(np_img)
            boxes1  = np.asarray(boxes1,  dtype=np.float32)
            scores1 = np.asarray(scores1, dtype=np.float32)
            idxs1   = np.asarray(idxs1,   dtype=np.int32)
            fire_indices  = np.where(idxs1 == 0)[0]
            smoke_indices = np.where(idxs1 == 1)[0]
            garbage_indices = np.where(idxs1 == 2)[0]
            ice_indices     = np.where(idxs1 == 3)[0]
            ebike_indices   = np.where(idxs1 == 4)[0]
            # vehicle_indices = np.where(idxs1 == 5)[0] # Old naive capture

            # 【新增】区域级载具过滤：只捕捉“跌入”用户设置的 AREA_LIST 禁区的车辆
            raw_vehicle_indices = np.where(idxs1 == 5)[0]
            valid_vehicle_indices = []
            if len(raw_vehicle_indices) > 0:
                bound_x_left = AREA_LIST[0][0]
                bound_x_right = AREA_LIST[1][0]
                bound_y_up = AREA_LIST[0][1]
                bound_y_down = AREA_LIST[1][1]
                
                # Check each vehicle's center point against the ROI boundaries
                for v_idx in raw_vehicle_indices:
                    v_box = boxes1[v_idx]
                    v_center_x = (v_box[0] + v_box[2]) / 2
                    v_center_y = (v_box[1] + v_box[3]) / 2
                    if (bound_x_left < v_center_x < bound_x_right) and (bound_y_up < v_center_y < bound_y_down):
                        valid_vehicle_indices.append(v_idx)
            
            vehicle_indices = np.array(valid_vehicle_indices, dtype=np.int32)
        if fire_indices is None:
            fire_indices = []
        if smoke_indices is None:
            smoke_indices = []
        if garbage_indices is None:
            garbage_indices = []
        if ice_indices is None:
            ice_indices = []
        if ebike_indices is None:
            ebike_indices = []
        if vehicle_indices is None:
            vehicle_indices = []
        if len(fire_indices) > 0 and TYPE_LIST[4]:
            list4 = True
        if len(smoke_indices) > 0 and TYPE_LIST[1]:
            list1 = True
        # Draw detections
        if TYPE_LIST[4]:
            draw_on_src(np_img, boxes1[fire_indices], idxs1[fire_indices])
        if TYPE_LIST[1]:
            draw_on_src(np_img, boxes1[smoke_indices], idxs1[smoke_indices])
        if TYPE_LIST[7] and len(garbage_indices) > 0:
            draw_on_src(np_img, boxes1[garbage_indices], idxs1[garbage_indices])
        if TYPE_LIST[8] and len(ice_indices) > 0:
            draw_on_src(np_img, boxes1[ice_indices], idxs1[ice_indices])
        if TYPE_LIST[9] and len(ebike_indices) > 0:
            draw_on_src(np_img, boxes1[ebike_indices], idxs1[ebike_indices])
        if TYPE_LIST[10] and len(vehicle_indices) > 0:
            draw_on_src(np_img, boxes1[vehicle_indices], idxs1[vehicle_indices])
            
        # ========================================================
        # 【新增逻辑】：让前端动态传进来的自定义词汇也能被画上红框
        # 在 idxs1 中，0-5 是预设目标，>= 6 都是用户临时加进来的提示词
        # ========================================================
        custom_indices = np.where(idxs1 >= 6)[0]
        if len(custom_indices) > 0:
            # 这些临时加进来的目标我们不管 TYPE_LIST 开关，霸道地强制画出来供人观看效果！
            draw_on_src(np_img, boxes1[custom_indices], idxs1[custom_indices])

        # Resize output
        np_img = cv2.resize(np_img, (640, 480))

        # Build 12-element RES_LIST aligned with case_type_info (caseType 1~12)
        RES_LIST = [
            list0,   # [0]  caseType=1  danger zone
            list1,   # [1]  caseType=2  smoke
            False,   # [2]  caseType=3  area loitering (not implemented)
            list3,   # [3]  caseType=4  fall (ST-GCN++)
            list4,   # [4]  caseType=5  fire
            False,   # [5]  caseType=6  smoking (not implemented)
            list6,   # [6]  caseType=7  punch/fight (ST-GCN++)
            bool(len(garbage_indices) > 0 and TYPE_LIST[7]),   # [7]  caseType=8  garbage
            bool(len(ice_indices) > 0 and TYPE_LIST[8]),       # [8]  caseType=9  ice
            bool(len(ebike_indices) > 0 and TYPE_LIST[9]),     # [9]  caseType=10 ebike
            bool(len(vehicle_indices) > 0 and TYPE_LIST[10]),  # [10] caseType=11 vehicle
            list11,  # [11] caseType=12 wave (ST-GCN++)
        ]
        monitorCommon.preList = indices_danger, fire_indices, smoke_indices
        return np_img, RES_LIST
    finally:
        pass
