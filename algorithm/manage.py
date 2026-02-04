from __init__ import create_app

config_name = 'dev'
app = create_app(config_name)

if __name__ == '__main__':
    app.run('0.0.0.0',port=6006) # 0.0.0.0 表示监听所有网络接口，包括公网
