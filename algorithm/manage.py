from __init__ import create_app
from config import DEFAULT_CONFIG_NAME, RuntimeConfig


config_name = DEFAULT_CONFIG_NAME
app = create_app(config_name)


if __name__ == "__main__":
    app.run(RuntimeConfig.APP_HOST, port=RuntimeConfig.APP_PORT)
