# Algorithm Service

This service provides the Python-side video analysis pipeline and exposes the
Flask API used by the backend.

## Config Layout

Algorithm config is now unified around env files:

- `algorithm/.env.dev`
- `algorithm/.env.prod`
- `algorithm/config.py`

`config.py` no longer keeps separate hard-coded `DevConfig` and `ProdConfig`
classes. It only:

1. reads `APP_CONFIG`
2. loads the matching env file
3. exposes `RuntimeConfig`

## Select Environment

Linux/macOS:

```bash
APP_CONFIG=dev python manage.py
APP_CONFIG=prod python manage.py
```

Windows PowerShell:

```powershell
$env:APP_CONFIG="dev"
python manage.py
```

Rules:

- `APP_CONFIG=dev` loads `.env.dev`
- `APP_CONFIG=prod` loads `.env.prod`
- any other `APP_CONFIG` value falls back to `.env.dev`
- system environment variables override values from the env file

## Common Config Items

Edit the env files for:

- backend address: `BACKEND_URL`
- stream addresses: `STREAM_URL`, `STREAM_RAW_URL`, `STREAM_PROCESSED_URL`
- monitor metadata: `MONITOR_ID`, `LATITUDE`, `LONGITUDE`
- ability toggles: `TYPE_LIST`
- danger area: `AREA_LIST`
- action model thresholds and weights
- local alarm cache settings
- Tencent translation credentials

Structured values use JSON in the env files, for example:

```env
TYPE_LIST=[false,false,false,true,false,false,true,false,false,false,false,true]
AREA_LIST=[[0,0],[1280,720]]
CUSTOM_DETECTION_PROMPTS=["overflow","garbage","garbage bin","bicycle","motorcycle"]
ACTION_LABEL_ORDER=["normal","fall","punch","wave"]
```

## Start

```bash
pip install -r requirements.txt
APP_CONFIG=dev python manage.py
```

The Flask service listens on:

- host: `APP_HOST`
- port: `APP_PORT`

Default port is `6006`.

## API

Prefix:

```text
/api/v1/monitor-device
```

Endpoints:

- `POST /type` update ability switches
- `GET /type` get ability switches
- `POST /area` update danger area
- `GET /area` get danger area
- `GET /image` get latest frame
- `POST /update_prompt` update custom prompts
- `GET /ping` health check

## Notes

- `algorithm/config.py` is the single runtime config entry
- `algorithm/common/monitor.py` reads shared runtime values from `RuntimeConfig`
- if you deploy inside Docker on Linux and need to reach host services, update
  the stream and backend addresses in the selected env file instead of editing
  Python code
