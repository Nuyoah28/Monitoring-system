from flask import Blueprint, request, current_app as app, jsonify, send_file
from service.AlarmService import postAlarm
from common import monitor as monitorCommon
import io
import cv2

monitor = Blueprint('monitor', __name__)


@monitor.route('/ping')
def test():
    return 'pong!'


# just for test
@monitor.route('/testalarm')
def test_alarm():
    postAlarm([True, False, False, False, False, True])
    return 'ok'

@monitor.route('/alarm',methods=['POST'])  # 接受物联网端发来的报警并重新确认
def alarm():
    if request.headers.get('Authorization') != 'sipc115':
        return jsonify({
            "code": 'A0401',
            "msg": "Unauthorized"
        })
    data = request.get_json()
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
    _, jpeg_frame = cv2.imencode('.jpg', monitorCommon.cacheQueue.queue[0])
    image_bytes = jpeg_frame.tobytes()
    # 将字节流转换为BytesIO对象
    bytes_io = io.BytesIO(image_bytes)
    # 返回图像作为HTTP响应
    return send_file(bytes_io, mimetype='image/png')


@monitor.route('/type', methods=['POST'])
def modifyMonitorType():
    monitorCommon.TYPE_LIST = request.get_json()['typeList']
    if request.headers.get('Authorization') != 'sipc115':
        return jsonify({
            "code": 'A0401',
            "msg": "Unauthorized"
        })
    res = {
        "code": "00000",
        "msg": "success"
    }
    return jsonify(res)


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
    print(request.get_json())
    monitorCommon.AREA_LIST[0] = (request.get_json()['areaList'][0], request.get_json()['areaList'][1])
    monitorCommon.AREA_LIST[1] = (request.get_json()['areaList'][2], request.get_json()['areaList'][3])
    if request.headers.get('Authorization') != 'sipc115':
        return jsonify({
            "code": 'A0401',
            "msg": "Unauthorized"
        })
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
