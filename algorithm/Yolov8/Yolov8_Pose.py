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

AREA_LOITER_STATE = {
    "active": {},
    "last_seen": {},
}


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

        # 处理关键点的正确位置
        for i in range(self.num_nodes):
            points[:, i * 3] = (points[:, i * 3] - self.dif_w) * self.factor
            points[:, i * 3 + 1] = (points[:, i * 3 + 1] - self.dif_h) * self.factor
            points[:, i * 3: i * 3 + 2] = torch.round(points[:, i * 3: i * 3 + 2])
        # ----
        # points shape is [N, 17, 3]
        # N is number of poses, 17 is keypoints, 3 is (x, y, confidence)
        keypoint_conf_sum = points[:, 2::3].sum(dim=1)
        valid_poses_index = (keypoint_conf_sum > 10).nonzero(as_tuple=False).squeeze(1)
        bboxes = bboxes[valid_poses_index]
        scores = scores[valid_poses_index]
        points = points[valid_poses_index]
        return torch.round(bboxes), scores, points

    def __call__(self, img_src):
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


def _safe_bool(values, index):
    return index < len(values) and bool(values[index])


def _scale_area_to_frame(area_list, frame_shape, monitor_common):
    if not area_list or len(area_list) < 2:
        return None
    frame_h, frame_w = frame_shape[:2]
    x1, y1 = float(area_list[0][0]), float(area_list[0][1])
    x2, y2 = float(area_list[1][0]), float(area_list[1][1])
    input_w = float(getattr(monitor_common, "AREA_INPUT_WIDTH", frame_w) or frame_w)
    input_h = float(getattr(monitor_common, "AREA_INPUT_HEIGHT", frame_h) or frame_h)

    max_area_x = max(abs(x1), abs(x2))
    max_area_y = max(abs(y1), abs(y2))
    if input_w > 0 and input_h > 0 and max_area_x <= input_w + 2 and max_area_y <= input_h + 2:
        x_scale = frame_w / input_w
        y_scale = frame_h / input_h
        x1 *= x_scale
        x2 *= x_scale
        y1 *= y_scale
        y2 *= y_scale

    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))
    if right - left < 2 or bottom - top < 2:
        return None
    return left, top, right, bottom


def _pose_body_points(points, confidence=0.3):
    if points is None or len(points) == 0:
        return np.empty((0, 2), dtype=np.float32)

    body_points = []
    for kpt in points:
        candidates = []
        weights = []
        for joint_idx, weight in ((15, 1.0), (16, 1.0), (13, 0.8), (14, 0.8), (11, 0.6), (12, 0.6)):
            score = float(kpt[joint_idx * 3 + 2])
            if score >= confidence:
                candidates.append((float(kpt[joint_idx * 3]), float(kpt[joint_idx * 3 + 1])))
                weights.append(weight)

        if candidates:
            coords = np.asarray(candidates, dtype=np.float32)
            body_points.append(np.average(coords, axis=0, weights=np.asarray(weights, dtype=np.float32)))
            continue

        bbox_like = kpt.reshape(-1, 3)
        valid = bbox_like[bbox_like[:, 2] >= confidence]
        if len(valid) > 0:
            body_points.append(np.mean(valid[:, :2], axis=0))
        else:
            body_points.append((np.nan, np.nan))

    if not body_points:
        return np.empty((0, 2), dtype=np.float32)
    return np.asarray(body_points, dtype=np.float32)


def _indices_in_area(points, area_box):
    if points is None or len(points) == 0 or area_box is None:
        return np.asarray([], dtype=np.int32)
    left, top, right, bottom = area_box
    return np.where(
        (points[:, 0] >= left) & (points[:, 0] <= right) &
        (points[:, 1] >= top) & (points[:, 1] <= bottom)
    )[0].astype(np.int32)


def _update_loiter_state(bboxes, body_points, inside_indices, now_time, threshold_seconds, grace_seconds):
    active = AREA_LOITER_STATE["active"]
    last_seen = AREA_LOITER_STATE["last_seen"]
    current_ids = set()
    alarm_indices = []

    for index in inside_indices:
        index = int(index)
        if bboxes is not None and index < len(bboxes):
            box = bboxes[index]
            foot = body_points[index] if index < len(body_points) else (0, 0)
            track_id = (
                int(round(float(foot[0]) / 40.0)),
                int(round(float(foot[1]) / 40.0)),
                int(round((float(box[2]) - float(box[0])) / 40.0)),
                int(round((float(box[3]) - float(box[1])) / 40.0)),
            )
        else:
            foot = body_points[index] if index < len(body_points) else (0, 0)
            track_id = (int(round(float(foot[0]) / 40.0)), int(round(float(foot[1]) / 40.0)))

        current_ids.add(track_id)
        active.setdefault(track_id, now_time)
        last_seen[track_id] = now_time
        if now_time - active[track_id] >= threshold_seconds:
            alarm_indices.append(index)

    expired_ids = [
        track_id
        for track_id, seen_at in last_seen.items()
        if track_id not in current_ids and now_time - seen_at > grace_seconds
    ]
    for track_id in expired_ids:
        active.pop(track_id, None)
        last_seen.pop(track_id, None)

    return np.asarray(alarm_indices, dtype=np.int32)


def _expire_loiter_state(now_time, grace_seconds):
    active = AREA_LOITER_STATE["active"]
    last_seen = AREA_LOITER_STATE["last_seen"]
    expired_ids = [track_id for track_id, seen_at in last_seen.items() if now_time - seen_at > grace_seconds]
    for track_id in expired_ids:
        active.pop(track_id, None)
        last_seen.pop(track_id, None)


def main(infer, infer1, action_recognizer, np_img, TYPE_LIST, AREA_LIST, infer_custom=None):
    from common import monitor as monitorCommon
    indices_danger, fire_indices, smoke_indices = monitorCommon.preList
    try:
        raw_img = np_img.copy()
        draw_img = np_img.copy()

        #   Pose estimation + ST-GCN++ action recognition
        list0 = False   # danger zone
        list2 = False   # area loitering
        list3 = False   # fall
        list6 = False   # punch
        list11 = False  # wave
        bboxes = None
        points = None

        if _safe_bool(TYPE_LIST, 0) or _safe_bool(TYPE_LIST, 2) or _safe_bool(TYPE_LIST, 3) or _safe_bool(TYPE_LIST, 6) or _safe_bool(TYPE_LIST, 11):
            bboxes, scores, points = infer(raw_img)
            scores = scores.cpu().numpy()
            bboxes = bboxes.to(torch.int32).cpu().numpy()
            points = points.cpu().numpy()
            infer.draw_pose(draw_img, bboxes, scores, points)

            # --- ST-GCN++ action recognition 
            if _safe_bool(TYPE_LIST, 3) or _safe_bool(TYPE_LIST, 6) or _safe_bool(TYPE_LIST, 11):
                try:
                    action_result = action_recognizer.predict(
                        points, bboxes, frame_shape=raw_img.shape[:2]
                    )
                except TypeError:
                    action_result = action_recognizer.predict(points, bboxes)
                if _safe_bool(TYPE_LIST, 3):
                    list3 = action_result.get('fall', False)
                if _safe_bool(TYPE_LIST, 6):
                    list6 = action_result.get('punch', False)
                if _safe_bool(TYPE_LIST, 11):
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
                            cv2.putText(draw_img, "fall", (x, y - line * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                            line += 1
                        if one_action.get("punch", False):
                            cv2.putText(draw_img, "punch", (x, y - line * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                            line += 1
                        if one_action.get("wave", False):
                            cv2.putText(draw_img, "wave", (x, y - line * 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                elif bboxes is not None and len(bboxes) > 0:
                    # fallback for legacy recognizer behavior
                    x, y = int(bboxes[0, 0]), int(bboxes[0, 1])
                    if list3:
                        cv2.putText(draw_img, "fall", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (36, 255, 12), 2)
                    if list6:
                        cv2.putText(draw_img, "punch", (x, y - 32), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (36, 255, 12), 2)
                    if list11:
                        cv2.putText(draw_img, "wave", (x, y - 64), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (36, 255, 12), 2)

        # ---------------------------------------------------------#
        #   Danger-zone and loitering detection from YOLOv8-Pose body points.
        # ---------------------------------------------------------#
        area_box = _scale_area_to_frame(AREA_LIST, raw_img.shape, monitorCommon)
        inside_indices = np.asarray([], dtype=np.int32)
        area_loiter_enabled = _safe_bool(TYPE_LIST, 2)
        area_grace_seconds = float(getattr(monitorCommon, "AREA_LOITER_GRACE_SECONDS", 1.5))
        if (_safe_bool(TYPE_LIST, 0) or area_loiter_enabled) and bboxes is not None and points is not None and len(bboxes) > 0:
            body_points = _pose_body_points(points, min(float(getattr(infer, "confidence", 0.3)), 0.4))
            inside_indices = _indices_in_area(body_points, area_box)
            indices_danger = inside_indices

            if area_box is not None:
                left, top, right, bottom = [int(round(value)) for value in area_box]
                cv2.rectangle(draw_img, (left, top), (right, bottom), (0, 0, 255), 2)

            if area_loiter_enabled:
                loiter_indices = _update_loiter_state(
                    bboxes,
                    body_points,
                    inside_indices,
                    time.time(),
                    float(getattr(monitorCommon, "AREA_LOITER_SECONDS", 5.0)),
                    area_grace_seconds,
                )
                list2 = len(loiter_indices) > 0
            else:
                AREA_LOITER_STATE["active"].clear()
                AREA_LOITER_STATE["last_seen"].clear()
        elif area_loiter_enabled:
            _expire_loiter_state(time.time(), area_grace_seconds)
        if indices_danger is None:
            indices_danger = []
        if len(indices_danger) > 0 and _safe_bool(TYPE_LIST, 0):
            list0 = True
            try:
                if len(indices_danger) <= bboxes.shape[0]:
                    for i in range(indices_danger.shape[0]):
                        index = indices_danger[i]
                        x = int(bboxes[index, 0])
                        y = int(bboxes[index, 1])
                        cv2.putText(draw_img, "danger", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2, (36, 255, 12), 2)
            except Exception:
                pass
        if list2:
            try:
                for index in loiter_indices:
                    if index < bboxes.shape[0]:
                        x = int(bboxes[index, 0])
                        y = int(bboxes[index, 1])
                        cv2.putText(draw_img, "loiter", (x, y + 42), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
            except Exception:
                pass

        # ---------------------------------------------------------#
        #   Mamba-YOLO-World detection
        #   Business prompt order follows custom_finetune_class_texts.json:
        #   0 overflow, 1 garbage, 2 garbage bin, 3 bicycle, 4 motorcycle,
        #   5 fire, 6 smoke.
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
        business_ran = False
        if TYPE_LIST[4] or TYPE_LIST[1] or TYPE_LIST[7] or TYPE_LIST[9] or TYPE_LIST[10]:
            boxes1, scores1, idxs1 = infer1(raw_img)
            boxes1  = np.asarray(boxes1,  dtype=np.float32)
            scores1 = np.asarray(scores1, dtype=np.float32)
            idxs1   = np.asarray(idxs1,   dtype=np.int32)
            business_ran = True
            group_label_ids = getattr(infer1, 'business_label_groups', None)
            business_names = [str(name).strip().lower() for name in getattr(infer1, 'business_names', [])]
            group_by_name = {
                name: group_label_ids[i]
                for i, name in enumerate(business_names)
                if group_label_ids is not None and i < len(group_label_ids)
            }
            if group_by_name:
                fire_indices = np.where(np.isin(idxs1, group_by_name.get("fire", [])))[0]
                smoke_indices = np.where(np.isin(idxs1, group_by_name.get("smoke", [])))[0]
                overflow_indices = np.where(np.isin(idxs1, group_by_name.get("overflow", [])))[0]
                garbage_indices = np.where(np.isin(idxs1, group_by_name.get("garbage", [])))[0]
                garbage_bin_indices = np.where(np.isin(idxs1, group_by_name.get("garbage bin", [])))[0]
                ebike_label_ids = group_by_name.get("bicycle", []) + group_by_name.get("motorcycle", [])
                ebike_indices = np.where(np.isin(idxs1, ebike_label_ids))[0]
            else:
                overflow_indices = np.where(idxs1 == 0)[0]
                garbage_indices = np.where(idxs1 == 1)[0]
                garbage_bin_indices = np.where(idxs1 == 2)[0]
                ebike_indices = np.where(np.isin(idxs1, [3, 4]))[0]
                fire_indices = np.where(idxs1 == 5)[0]
                smoke_indices = np.where(idxs1 == 6)[0]
            # vehicle detection is intentionally left for a future dedicated algorithm.

            # Vehicle/road-occupation detection is intentionally left for a future dedicated algorithm.
            vehicle_indices = np.empty((0,), dtype=np.int32)
        if len(fire_indices) > 0 and TYPE_LIST[4]:
            list4 = True
        if len(smoke_indices) > 0 and TYPE_LIST[1]:
            list1 = True
        business_categories = getattr(infer1, 'categories', None)
        # Draw detections
        if TYPE_LIST[4]:
            draw_on_src(draw_img, boxes1[fire_indices], idxs1[fire_indices], business_categories, scores=scores1[fire_indices])
        if TYPE_LIST[1]:
            draw_on_src(draw_img, boxes1[smoke_indices], idxs1[smoke_indices], business_categories, scores=scores1[smoke_indices])
        if TYPE_LIST[7] and (len(overflow_indices) > 0 or len(garbage_indices) > 0):
            garbage_alarm_indices = np.concatenate((overflow_indices, garbage_indices)).astype(np.int32)
            draw_on_src(draw_img, boxes1[garbage_alarm_indices], idxs1[garbage_alarm_indices], business_categories, scores=scores1[garbage_alarm_indices])
        # garbage bin is context only: draw it for visibility, but do not trigger RES_LIST[7].
        if TYPE_LIST[7] and len(garbage_bin_indices) > 0:
            draw_on_src(draw_img, boxes1[garbage_bin_indices], idxs1[garbage_bin_indices], business_categories, scores=scores1[garbage_bin_indices])
        if TYPE_LIST[9] and len(ebike_indices) > 0:
            draw_on_src(draw_img, boxes1[ebike_indices], idxs1[ebike_indices], business_categories, scores=scores1[ebike_indices])
        if TYPE_LIST[10] and len(vehicle_indices) > 0:
            draw_on_src(draw_img, boxes1[vehicle_indices], idxs1[vehicle_indices], business_categories, scores=scores1[vehicle_indices])
            
        # Draw frontend custom open-vocabulary prompts with the open detector.
        # These boxes are visual only; fixed business alarms still come from infer1 above.
        custom_detector = infer_custom if infer_custom is not None else infer1
        custom_group_label_ids = getattr(custom_detector, 'business_label_groups', None)
        if custom_group_label_ids and len(custom_group_label_ids) > 7:
            if custom_detector is infer1 and business_ran:
                custom_boxes = boxes1
                custom_scores = scores1
                custom_idxs = idxs1
            else:
                custom_boxes, custom_scores, custom_idxs = custom_detector(raw_img)
                custom_boxes = np.asarray(custom_boxes, dtype=np.float32)
                custom_scores = np.asarray(custom_scores, dtype=np.float32)
                custom_idxs = np.asarray(custom_idxs, dtype=np.int32)
            custom_label_ids = [label_id for group in custom_group_label_ids[7:] for label_id in group]
            custom_indices = np.where(np.isin(custom_idxs, custom_label_ids))[0]
            if len(custom_indices) > 0:
                draw_on_src(
                    draw_img,
                    custom_boxes[custom_indices],
                    custom_idxs[custom_indices],
                    getattr(custom_detector, 'categories', None),
                    scores=custom_scores[custom_indices],
                )

        # Resize output
        draw_img = cv2.resize(draw_img, (640, 480))

        # Build 12-element RES_LIST aligned with case_type_info (caseType 1~12)
        RES_LIST = [
            list0,   # [0]  caseType=1  danger zone
            list1,   # [1]  caseType=2  smoke
            list2,   # [2]  caseType=3  area loitering
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
        return draw_img, RES_LIST
    finally:
        pass
