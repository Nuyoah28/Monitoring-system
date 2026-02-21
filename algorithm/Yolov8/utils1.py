import cv2 as cv
import numpy as np
import torch
from torchvision import transforms as T


# 类别名称列表（与数据库 case_type_info 表 1:1 对应）
# MambaYOLODetector 初始化时会动态覆盖 fire/smoke 相关的项
event_en = [
    "danger_zone",  # caseType=1  -> 但 Mamba-YOLO class_id=0 = fire
    "smoke",        # caseType=2  -> Mamba-YOLO class_id=1 = smoke
]


def update_event_names(categories: list):
    """
    由 MambaYOLODetector 调用，动态同步检测类别名称。
    保证画框时显示正确的类别文字，而不是 IndexError。
    """
    global event_en
    event_en = list(categories)


def draw_on_src(img_src, boxes, class_ids):
    # 左上角x 左上角y 框宽 框高 confidence
    boxes = boxes.astype(np.int32)
    for i in range(len(class_ids)):
        class_id = int(class_ids[i])
        box = boxes[i]
        cv.rectangle(img_src, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 2)
        # 安全取类别名：超出范围时显示 class_N 而非崩溃
        if class_id < len(event_en):
            text = event_en[class_id]
        else:
            text = f"class_{class_id}"
        font = cv.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        thickness = 2
        textX = box[0]
        textY = 22 + box[1]
        cv.putText(img_src, text, (textX, textY), font, fontScale, (0, 0, 255), thickness)

def to_even(number):
    if number & 1:
        return number + 1
    return number

def format_img(np_img):
    # YOLO 输入的预处理，最好直接在GPU上进行处理
    im = torch.from_numpy(np_img).to(torch.device('cuda:0')).permute(2, 0, 1).float() / 255.0
    _, _H, _W = im.shape
    # BGR2RGB
    im = im[[2, 1, 0], ...]
    # 1.最大等比例缩放某一个边到640  2.填充到640x640
    # 1.计算缩放比例
    factor = max(_W / 640, _H / 640)  # default 640
    target_W, target_H = to_even(int(_W / factor)), to_even(int(_H / factor))
    # 2.计算填充值
    dif_w = int((640 - target_W) / 2)
    dif_h = int((640 - target_H) / 2)
    # 定义处理算子
    ts = T.Compose([
        T.Resize((target_H, target_W)),
        T.Pad([dif_w, dif_h], fill=0.7)
    ])
    im = ts(im)
    # 返回一些预处理后的图像, 和预处理时附加的信息
    return im, dif_w, dif_h, factor

def gstreamer_pipeline(
        capture_width=1280,  # 摄像头预捕获的图像宽度
        capture_height=720,  # 摄像头预捕获的图像高度
        display_width=1280,  # 窗口显示的图像宽度
        display_height=720,  # 窗口显示的图像高度
        framerate=30,  # 捕获帧率
        flip_method=4,  # 是否旋转图像
):
    return (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            ))
