from __init__ import create_app
from config import RuntimeConfig


app = create_app()


if __name__ == "__main__":
    app.run(RuntimeConfig.APP_HOST, port=RuntimeConfig.APP_PORT)
