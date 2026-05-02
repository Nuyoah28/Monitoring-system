import os


# Single configuration entry for app-owned runtime settings.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _env_str(name, default=""):
    value = os.environ.get(name)
    return default if value is None else value


def _env_int(name, default=0):
    value = os.environ.get(name)
    if value is None or value == "":
        return int(default)
    return int(value)


def _env_float(name, default=0.0):
    value = os.environ.get(name)
    if value is None or value == "":
        return float(default)
    return float(value)


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return bool(default)
    return value.strip().lower() in ("1", "true", "yes", "on")


def _join_base(*parts):
    return os.path.join(BASE_DIR, *parts)


class Config:
    APP_HOST = _env_str("APP_HOST", "0.0.0.0")
    APP_PORT = _env_int("APP_PORT", 6006)

    BACKEND_URL = _env_str("BACKEND_URL", "")
    STREAM_URL = _env_str("STREAM_URL", "")
    STREAM_RAW_URL = _env_str("STREAM_RAW_URL", "")
    STREAM_PROCESSED_URL = _env_str("STREAM_PROCESSED_URL", "")
    TOKEN = _env_str("TOKEN", "") or None

    MONITOR_ID = _env_int("MONITOR_ID", 1)
    LATITUDE = _env_float("LATITUDE", 0)
    LONGITUDE = _env_float("LONGITUDE", 0)

    TYPE_LIST = [False, False, False, True, False, False, True, False, False, False, False, True]
    AREA_LIST = [(0, 0), (1280, 720)]

    VIDEO_PROCESSING_ENABLED = _env_bool("VIDEO_PROCESSING_ENABLED", True)
    VIDEO_CACHE_SIZE = _env_int("VIDEO_CACHE_SIZE", 50)
    CAPTURE_WIDTH = _env_int("CAPTURE_WIDTH", 1280)
    CAPTURE_HEIGHT = _env_int("CAPTURE_HEIGHT", 720)
    DISPLAY_WIDTH = _env_int("DISPLAY_WIDTH", 1280)
    DISPLAY_HEIGHT = _env_int("DISPLAY_HEIGHT", 720)
    FRAMERATE = _env_int("FRAMERATE", 60)
    FLIP_METHOD = _env_int("FLIP_METHOD", 0)

    CUSTOM_DETECTION_PROMPTS = [
        "overflow",
        "garbage",
        "garbage bin",
        "bicycle",
        "motorcycle",
    ]
    ENABLE_PROMPT_SYNONYMS = _env_bool("ENABLE_PROMPT_SYNONYMS", False)

    ACTION_MODEL_BACKEND = _env_str("ACTION_MODEL_BACKEND", "ctrgcn").lower()
    ACTION_CTR_GCN_ROOT = _env_str("ACTION_CTR_GCN_ROOT", _join_base("CTR-GCN"))
    ACTION_CTR_GCN_FUSION = _env_str("ACTION_CTR_GCN_FUSION", "joint_bone").lower()
    ACTION_CTR_GCN_FUSION_MODE = _env_str("ACTION_CTR_GCN_FUSION_MODE", "logits").lower()
    ACTION_CTR_GCN_JOINT_WEIGHTS = _env_str(
        "ACTION_CTR_GCN_JOINT_WEIGHTS",
        _join_base("algo", "ctrgcn_joint_w90_ref_lie_vfF5O15_wCE.pt"),
    )
    ACTION_CTR_GCN_BONE_WEIGHTS = _env_str(
        "ACTION_CTR_GCN_BONE_WEIGHTS",
        _join_base("algo", "ctrgcn_bone_w90_ref_lie_vfF5O15_wCE.pt"),
    )
    ACTION_CTR_GCN_WEIGHTS = _env_str("ACTION_CTR_GCN_WEIGHTS", ACTION_CTR_GCN_JOINT_WEIGHTS)
    ACTION_CTR_GCN_JOINT_ALPHA = _env_float("ACTION_CTR_GCN_JOINT_ALPHA", 1.0)
    ACTION_CTR_GCN_BONE_ALPHA = _env_float("ACTION_CTR_GCN_BONE_ALPHA", 1.0)
    ACTION_LABEL_ORDER = ("normal", "fall", "punch", "wave")
    ACTION_WINDOW_SIZE = _env_int("ACTION_WINDOW_SIZE", 90)
    ACTION_MIN_FRAMES = _env_int("ACTION_MIN_FRAMES", 8)
    ACTION_SMOOTH = _env_int("ACTION_SMOOTH", 4)
    ACTION_MAX_TRACKS = _env_int("ACTION_MAX_TRACKS", 8)
    ACTION_TOP_K_TRACKS = _env_int("ACTION_TOP_K_TRACKS", 4)
    ACTION_INFER_INTERVAL = _env_int("ACTION_INFER_INTERVAL", 1)
    ACTION_MAX_MISSING = _env_int("ACTION_MAX_MISSING", 10)

    ACTION_FALL_ON_THR = _env_float("ACTION_FALL_ON_THR", 0.35)
    ACTION_FALL_OFF_THR = _env_float("ACTION_FALL_OFF_THR", 0.15)
    ACTION_FALL_HOLD_FRAMES = _env_int("ACTION_FALL_HOLD_FRAMES", 75)
    ACTION_FALL_RELEASE_FRAMES = _env_int("ACTION_FALL_RELEASE_FRAMES", 30)
    ACTION_FALL_LATCH = _env_bool("ACTION_FALL_LATCH", True)

    ACTION_WAVE_ON_THR = _env_float("ACTION_WAVE_ON_THR", 0.40)
    ACTION_WAVE_OFF_THR = _env_float("ACTION_WAVE_OFF_THR", 0.20)
    ACTION_WAVE_CONFIRM_FRAMES = _env_int("ACTION_WAVE_CONFIRM_FRAMES", 3)
    ACTION_WAVE_RELEASE_FRAMES = _env_int("ACTION_WAVE_RELEASE_FRAMES", 8)

    ACTION_PUNCH_ON_THR = _env_float("ACTION_PUNCH_ON_THR", 0.45)
    ACTION_PUNCH_OFF_THR = _env_float("ACTION_PUNCH_OFF_THR", 0.20)
    ACTION_PUNCH_CONFIRM_FRAMES = _env_int("ACTION_PUNCH_CONFIRM_FRAMES", 3)
    ACTION_PUNCH_RELEASE_FRAMES = _env_int("ACTION_PUNCH_RELEASE_FRAMES", 8)
    ACTION_FIGHT_DISTANCE_RATIO = _env_float("ACTION_FIGHT_DISTANCE_RATIO", 1.40)
    ACTION_FIGHT_CONFIRM_FRAMES = _env_int("ACTION_FIGHT_CONFIRM_FRAMES", 4)
    ACTION_FIGHT_RELEASE_FRAMES = _env_int("ACTION_FIGHT_RELEASE_FRAMES", 12)

    WARNING_STREAK_MIN_HITS = _env_int("WARNING_STREAK_MIN_HITS", 3)

    ALARM_CACHE_ENABLED = _env_bool("ALARM_CACHE_ENABLED", True)
    ALARM_CACHE_DIR = _env_str("ALARM_CACHE_DIR", "runtime/alarm_cache")
    ALARM_CACHE_DB = _env_str("ALARM_CACHE_DB", "alarm_cache.sqlite3")
    ALARM_CACHE_CLIP_DIR = _env_str("ALARM_CACHE_CLIP_DIR", "clips")
    ALARM_SYNC_INTERVAL_SECONDS = _env_int("ALARM_SYNC_INTERVAL_SECONDS", 10)
    ALARM_SYNC_BATCH_SIZE = _env_int("ALARM_SYNC_BATCH_SIZE", 20)
    ALARM_REQUEST_TIMEOUT_SECONDS = _env_int("ALARM_REQUEST_TIMEOUT_SECONDS", 5)

    TENCENT_SECRET_ID = _env_str("TENCENT_SECRET_ID", "AKIDT7ufHm8NOF4IHdmkaJtaFxYyHe9f1XvB")
    TENCENT_SECRET_KEY = _env_str("TENCENT_SECRET_KEY", "B9wWO8j9MYfdoqpeHhtth5HH3cy85pLd")


class DevConfig(Config):
    BACKEND_URL = _env_str("BACKEND_URL", "http://host.docker.internal:10215")
    STREAM_URL = _env_str("STREAM_URL", "rtmp://host.docker.internal:1935")
    STREAM_RAW_URL = _env_str("STREAM_RAW_URL", "rtmp://host.docker.internal:1935/live/raw")
    STREAM_PROCESSED_URL = _env_str("STREAM_PROCESSED_URL", "rtmp://host.docker.internal:1935/live/ai")


class ProdConfig(Config):
    pass


config = {
    "dev": DevConfig,
    "prod": ProdConfig,
}


DEFAULT_CONFIG_NAME = _env_str("APP_CONFIG", "dev").lower()
RuntimeConfig = config.get(DEFAULT_CONFIG_NAME, DevConfig)
