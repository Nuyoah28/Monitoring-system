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
    indices_danger, fire_indices, smoke_indices = monitorCommon.preList
    try:
        #   Pose estimation + ST-GCN++ action recognition
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

            # --- ST-GCN++ action recognition 
            if TYPE_LIST[3] or TYPE_LIST[6] or TYPE_LIST[11]:
                try:
                    action_result = action_recognizer.predict(
                        points, bboxes, frame_shape=np_img.shape[:2]
                    )
                except TypeError:
                    action_result = action_recognizer.predict(points, bboxes)
                if TYPE_LIST[3]:
                    list3 = action_result.get('fall', False)
                if TYPE_LIST[6]:
                    list6 = action_result.get('punch', False)
                if TYPE_LIST[11]:
                    list11 = action_result.get('wave', False)

                # Draw action labels on image (multi-person overlays when available)
                overlays = []
                if hasattr(action_recognizer, "get_last_overlays"):
                    overlays = action_recognizer.get_last_overlays() or []

                if overlays:
                    for box, one_action in overlays:
                        x, y = int(box[0]), int(box[1])
                        line = 0
                        if one_action.get("fall", False):
                            cv2.putText(np_img, "fall", (x, y - line * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                            line += 1
                        if one_action.get("punch", False):
                            cv2.putText(np_img, "punch", (x, y - line * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                            line += 1
                        if one_action.get("wave", False):
                            cv2.putText(np_img, "wave", (x, y - line * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                elif bboxes is not None and len(bboxes) > 0:
                    # fallback for legacy recognizer behavior
                    x, y = int(bboxes[0, 0]), int(bboxes[0, 1])
                    if list3:
                        cv2.putText(np_img, "fall", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (36, 255, 12), 2)
                    if list6:
                        cv2.putText(np_img, "punch", (x, y - 32), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (36, 255, 12), 2)
                    if list11:
                        cv2.putText(np_img, "wave", (x, y - 64), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (36, 255, 12), 2)

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
        #   Mamba-YOLO-World detection
        #   Conservative prompt order:
        #   0 fire, 1 smoke, 2 overflow, 3 garbage, 4 garbage bin,
        #   5 bicycle, 6 motorcycle.
        #   garbage bin is context only and must not trigger garbage alarm.
        # ---------------------------------------------------------#
        list1 = False   # smoke
        list4 = False   # fire
        
        # 初始化所有可能使用的变量为默认值
        boxes1 = np.empty((0, 4), dtype=np.float32)
        scores1 = np.empty((0,), dtype=np.float32)
        idxs1 = np.empty((0,), dtype=np.int32)
        fire_indices = []
        smoke_indices = []
        overflow_indices = []
        garbage_indices = []
        garbage_bin_indices = []
        ebike_indices = []
        vehicle_indices = []
        if TYPE_LIST[4] or TYPE_LIST[1] or TYPE_LIST[7] or TYPE_LIST[9] or TYPE_LIST[10]:
            boxes1, scores1, idxs1 = infer1(np_img)
            boxes1  = np.asarray(boxes1,  dtype=np.float32)
            scores1 = np.asarray(scores1, dtype=np.float32)
            idxs1   = np.asarray(idxs1,   dtype=np.int32)
            group_label_ids = getattr(infer1, 'business_label_groups', None)
            if group_label_ids and len(group_label_ids) >= 7:
                fire_indices = np.where(np.isin(idxs1, group_label_ids[0]))[0]
                smoke_indices = np.where(np.isin(idxs1, group_label_ids[1]))[0]
                overflow_indices = np.where(np.isin(idxs1, group_label_ids[2]))[0]
                garbage_indices = np.where(np.isin(idxs1, group_label_ids[3]))[0]
                garbage_bin_indices = np.where(np.isin(idxs1, group_label_ids[4]))[0]
                ebike_indices = np.where(np.isin(idxs1, group_label_ids[5] + group_label_ids[6]))[0]
            else:
                fire_indices = np.where(idxs1 == 0)[0]
                smoke_indices = np.where(idxs1 == 1)[0]
                overflow_indices = np.where(idxs1 == 2)[0]
                garbage_indices = np.where(idxs1 == 3)[0]
                garbage_bin_indices = np.where(idxs1 == 4)[0]
                ebike_indices = np.where(np.isin(idxs1, [5, 6]))[0]
            # vehicle detection is intentionally left for a future dedicated algorithm.

            # Vehicle/road-occupation detection is intentionally left for a future dedicated algorithm.
            vehicle_indices = np.empty((0,), dtype=np.int32)
        if len(fire_indices) > 0 and TYPE_LIST[4]:
            list4 = True
        if len(smoke_indices) > 0 and TYPE_LIST[1]:
            list1 = True
        # Draw detections
        if TYPE_LIST[4]:
            draw_on_src(np_img, boxes1[fire_indices], idxs1[fire_indices])
        if TYPE_LIST[1]:
            draw_on_src(np_img, boxes1[smoke_indices], idxs1[smoke_indices])
        if TYPE_LIST[7] and (len(overflow_indices) > 0 or len(garbage_indices) > 0):
            garbage_alarm_indices = np.concatenate((overflow_indices, garbage_indices)).astype(np.int32)
            draw_on_src(np_img, boxes1[garbage_alarm_indices], idxs1[garbage_alarm_indices])
        # garbage bin is context only: draw it for visibility, but do not trigger RES_LIST[7].
        if TYPE_LIST[7] and len(garbage_bin_indices) > 0:
            draw_on_src(np_img, boxes1[garbage_bin_indices], idxs1[garbage_bin_indices])
        if TYPE_LIST[9] and len(ebike_indices) > 0:
            draw_on_src(np_img, boxes1[ebike_indices], idxs1[ebike_indices])
        if TYPE_LIST[10] and len(vehicle_indices) > 0:
            draw_on_src(np_img, boxes1[vehicle_indices], idxs1[vehicle_indices])
            
        # ========================================================
        # 【新增逻辑】：让前端动态传进来的自定义词汇也能被画上红框
        # 固定业务目标顺序为 fire/smoke/overflow/garbage/garbage bin/bicycle/motorcycle，
        # 临时 prompt 的起始 label 从前 7 个业务组之后开始。
        # ========================================================
        group_label_ids = getattr(infer1, 'business_label_groups', None)
        if group_label_ids and len(group_label_ids) > 7:
            custom_label_ids = [label_id for group in group_label_ids[7:] for label_id in group]
            custom_indices = np.where(np.isin(idxs1, custom_label_ids))[0]
        else:
            custom_indices = np.where(idxs1 >= 7)[0]
        if len(custom_indices) > 0:
            # 这些临时加进来的目标我们不管 TYPE_LIST 开关，强制画出来供人观看效果。
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
            bool((len(overflow_indices) > 0 or len(garbage_indices) > 0) and TYPE_LIST[7]),   # [7]  caseType=8  garbage; garbage bin is context only
            False,   # [8]  caseType=9  ice (disabled: Mamba model was not finetuned for ice)
            bool(len(ebike_indices) > 0 and TYPE_LIST[9]),     # [9]  caseType=10 ebike
            bool(len(vehicle_indices) > 0 and TYPE_LIST[10]),  # [10] caseType=11 vehicle
            list11,  # [11] caseType=12 wave (ST-GCN++)
        ]
        monitorCommon.preList = indices_danger, fire_indices, smoke_indices
        return np_img, RES_LIST
    finally:
        pass
