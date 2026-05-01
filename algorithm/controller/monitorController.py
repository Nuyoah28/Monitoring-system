from flask import Blueprint, request, current_app as app, jsonify, send_file
from service.AlarmService import postAlarm
from common import monitor as monitorCommon
from util.translator import TencentTranslator
import io
import cv2

translator = TencentTranslator()

monitor = Blueprint('monitor', __name__)


@monitor.route('/ping')
def test():
    return 'pong!'


# just for test
@monitor.route('/testalarm')
def test_alarm():
    postAlarm([True, False, False, False, False, True])
    return 'ok'


@monitor.route('/update_prompt', methods=['POST'])
def update_prompt():
    """
    动态更新大模型 Mamba-YOLO-World 检测的自定义单词。
    接收 { "prompts": ["垃圾", "电动车"] } 的 JSON
    """
    data = request.get_json()
    if not data or 'prompts' not in data:
        return jsonify({"code": "E0400", "msg": "Bad request"})
    
    # 也可以限制这口的访问权限
    # if request.headers.get('Authorization') != 'sipc115': return jsonify(...)
    
    raw_prompts = data['prompts']
    
    # 将中文通过翻译器转为英文
    english_prompts = []
    for p in raw_prompts:
        en_str = translator.translate_zh_to_en(p)
        english_prompts.append(en_str)
        
    print(f"动态更新 Prompt: {raw_prompts} -> {english_prompts}")
    
    # 更新到全局配置中心，并标记修改位
    monitorCommon.CUSTOM_DETECTION_PROMPTS = english_prompts
    monitorCommon.PROMPTS_CHANGED = True
    
    return jsonify({
        "code": "00000",
        "msg": "success",
        "translated": english_prompts
    })

@monitor.route('/alarm',methods=['POST'])  # 接受物联网端发来的报警并重新确认
def alarm():
    if request.headers.get('Authorization') != 'sipc115':
        return jsonify({
            "code": 'A0401',
            "msg": "Unauthorized"
        })
    data = request.get_json()
    # TODO

    print(data)
    return jsonify({
        "code": "00000",
        "msg": "success"
    })



@monitor.route("/image", methods=["GET"])
def get_image():
    if request.headers.get('Authorization') != 'sipc115':
        return jsonify({
            "code": 'A0401',
            "msg": "Unauthorized"
        })
    if monitorCommon.cacheQueue.empty():
        return jsonify({
            "code": 'A0404',
            "msg": "No image available"
        }), 404
    _, jpeg_frame = cv2.imencode('.jpg', monitorCommon.cacheQueue.queue[0])
    image_bytes = jpeg_frame.tobytes()
    # 将字节流转换为BytesIO对象
    bytes_io = io.BytesIO(image_bytes)
    # 返回图像作为HTTP响应
    return send_file(bytes_io, mimetype='image/png')


@monitor.route('/type', methods=['POST'])
def modifyMonitorType():
    if request.headers.get('Authorization') != 'sipc115':
        return jsonify({
            "code": 'A0401',
            "msg": "Unauthorized"
        })
    monitorCommon.TYPE_LIST = request.get_json()['typeList']
    res = {
        "code": "00000",
        "msg": "success"
    }
    return jsonify(res)

#
@monitor.route('/type', methods=['GET'])
def getMonitorType():
    if request.headers.get('Authorization') != 'sipc115':
        return jsonify({
            "code": 'A0401',
            "msg": "Unauthorized"
        })
    res = {
        "code": '00000',
        "msg": "success",
        "typeList": monitorCommon.TYPE_LIST
    }
    return jsonify(res)


@monitor.route('/area', methods=['POST'])
def modifyMonitorArea():
    if request.headers.get('Authorization') != 'sipc115':
        return jsonify({
            "code": 'A0401',
            "msg": "Unauthorized"
        })
    print(request.get_json())
    monitorCommon.AREA_LIST[0] = (request.get_json()['areaList'][0], request.get_json()['areaList'][1])
    monitorCommon.AREA_LIST[1] = (request.get_json()['areaList'][2], request.get_json()['areaList'][3])
    res = {
        "code": "00000",
        "msg": "success"
    }
    return jsonify(res)


@monitor.route('/area', methods=['GET'])
def getMonitorArea():
    if request.headers.get('Authorization') != 'sipc115':
        return jsonify({
            "code": 'A0401',
            "msg": "Unauthorized"
        })
    resList = [monitorCommon.AREA_LIST[0][0], monitorCommon.AREA_LIST[0][1], monitorCommon.AREA_LIST[1][0],
               monitorCommon.AREA_LIST[1][1]]
    res = {
        "code": '00000',
        "msg": "success",
        "areaList": resList
    }
    return jsonify(res)
