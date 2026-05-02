from flask import Flask
import requests, time, logging
from controller import config_blueprint
from config import RuntimeConfig
from algo import videoProcess
import threading
from util import Logger
from service import AlarmService

logger = Logger.setup_logger()


def create_app():
    app = Flask(__name__)
    app.config.from_object(RuntimeConfig)
    print(app.config)
    config_blueprint(app)
    try:
        file = open("token.txt", "r")
        token = app.config['token'] = file.read()
        if token is None or token == "":
            logger.error("token is None")
            file.close()
            raise FileNotFoundError
        file.close()
    except FileNotFoundError:
        while app.config['TOKEN'] is None or app.config['TOKEN'] == "":
            # todo: get token from backend
            # token = requests.post(app.config['BACKEND_URL'] + "/token").json()['TOKEN']
            app.config['TOKEN'] = "nihao"
            logger.error("token is None, retrying...")
            time.sleep(3)
        file = open("token.txt", "w")
        file.write(app.config['TOKEN'])
        file.close()
    # todo: get monitor info from backend and save to config and common
    # data = requests.get(app.config['BACKEND_URL'] + "/monitorInfo"
    #                     headers={'Authorization': app.config['TOKEN']}).json()
    # if data['code'] == 200:
    #     app.config['TOKEN'] = data['token']
    #     app.config['MONITOR_ID'] = data['monitorId']
    #     app.config['LATITUDE'] = data['latitude']
    #     app.config['LONGITUDE'] = data['longitude']
    #     app.config['STREAM_URL'] = data['streamUrl']
    # else:
    #     raise Exception("get monitor info failed")
    # 创建线程对象
    AlarmService.startAlarmCacheSyncWorker()
    stream_thread = threading.Thread(target=videoProcess.stream_video, name="stream_thread")
    # 启动线程
    stream_thread.start()
    return app
