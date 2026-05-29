import os
import threading
import time
from fractions import Fraction
from typing import Any, Optional, Tuple, Union

import av
import cv2


RTMP_URL = os.environ.get("RTMP_URL", "rtmp://123.56.248.17:1935/live/raw")
CAMERA_SOURCE_ENV = os.environ.get("CAMERA_SOURCE")
CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "1"))
FRAME_RATE = int(os.environ.get("FRAME_RATE", "15"))
RESOLUTION = (
    int(os.environ.get("FRAME_WIDTH", "1280")),
    int(os.environ.get("FRAME_HEIGHT", "720")),
)
OPEN_RETRY_DELAY = float(os.environ.get("OPEN_RETRY_DELAY", "2"))
READ_RETRY_DELAY = float(os.environ.get("READ_RETRY_DELAY", "0.05"))
READ_FAILURE_THRESHOLD = int(os.environ.get("READ_FAILURE_THRESHOLD", "3"))
HEARTBEAT_INTERVAL = int(os.environ.get("HEARTBEAT_INTERVAL", "30"))
BIT_RATE = int(os.environ.get("BIT_RATE", "1200000"))
MAX_RATE = int(os.environ.get("MAX_RATE", str(BIT_RATE)))
ENCODER_BUFFER_SIZE = int(os.environ.get("ENCODER_BUFFER_SIZE", str(BIT_RATE * 2)))
GOP_SIZE = int(os.environ.get("GOP_SIZE", str(max(15, FRAME_RATE))))
MAX_B_FRAMES = int(os.environ.get("MAX_B_FRAMES", "0"))
CRF = int(os.environ.get("CRF", "28"))
ENCODER_PRESET = os.environ.get("ENCODER_PRESET", "ultrafast")
NO_NEW_FRAME_DELAY = float(os.environ.get("NO_NEW_FRAME_DELAY", "0.005"))
AV_ERROR = getattr(av, "AVError", Exception)


def log(message: str) -> None:
    print(f"[push] {time.strftime('%Y-%m-%d %H:%M:%S')} {message}", flush=True)


def resolve_camera_source() -> Union[int, str]:
    if CAMERA_SOURCE_ENV:
        source = CAMERA_SOURCE_ENV.strip()
        if source.isdigit():
            return int(source)
        return source
    return CAMERA_INDEX


def format_kbps(value: int) -> str:
    kbps = max(1, int(round(value / 1000)))
    return f"{kbps}k"


def open_capture(source: Union[int, str]) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
    cap.set(cv2.CAP_PROP_FPS, FRAME_RATE)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def open_output() -> Tuple[av.container.OutputContainer, Any]:
    rate = Fraction(FRAME_RATE, 1)
    output_container = av.open(RTMP_URL, mode="w", format="flv")
    stream = output_container.add_stream("h264", rate=rate)
    stream.width = RESOLUTION[0]
    stream.height = RESOLUTION[1]
    stream.pix_fmt = "yuv420p"
    stream.options = {
        "tune": "zerolatency",
        "preset": ENCODER_PRESET,
        "crf": str(CRF),
        "maxrate": format_kbps(MAX_RATE),
        "bufsize": format_kbps(ENCODER_BUFFER_SIZE),
        "g": str(GOP_SIZE),
        "keyint_min": str(GOP_SIZE),
        "sc_threshold": "0",
        "bf": str(MAX_B_FRAMES),
    }

    codec_context = stream.codec_context
    codec_context.bit_rate = BIT_RATE
    codec_context.max_b_frames = MAX_B_FRAMES
    codec_context.gop_size = GOP_SIZE
    codec_context.time_base = Fraction(1, FRAME_RATE)
    return output_container, stream


def close_output(
    output_container: Optional[av.container.OutputContainer],
    stream: Optional[Any],
) -> None:
    if output_container is None:
        return

    try:
        if stream is not None:
            for packet in stream.encode():
                output_container.mux(packet)
    except Exception as exc:
        log(f"flush output failed: {exc}")
    finally:
        try:
            output_container.close()
        except Exception as exc:
            log(f"close output failed: {exc}")


def close_capture(cap: Optional[cv2.VideoCapture]) -> None:
    if cap is not None:
        cap.release()


class LatestFrameReader:
    def __init__(self, source: Union[int, str]) -> None:
        self.source = source
        self.stop_event = threading.Event()
        self.frame_lock = threading.Lock()
        self.latest_frame: Optional[Any] = None
        self.latest_seq = -1
        self.last_frame_at = 0.0
        self.thread = threading.Thread(target=self._run, name="camera_reader", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=2)

    def snapshot(self) -> Tuple[Optional[Any], int, float]:
        with self.frame_lock:
            if self.latest_frame is None:
                return None, self.latest_seq, self.last_frame_at
            return self.latest_frame.copy(), self.latest_seq, self.last_frame_at

    def _run(self) -> None:
        cap: Optional[cv2.VideoCapture] = None
        consecutive_read_failures = 0

        while not self.stop_event.is_set():
            try:
                if cap is None or not cap.isOpened():
                    close_capture(cap)
                    cap = None
                    log(f"opening camera source: {self.source}")
                    cap = open_capture(self.source)
                    if not cap.isOpened():
                        log(
                            f"camera open failed for source {self.source}; "
                            f"retrying in {OPEN_RETRY_DELAY}s"
                        )
                        close_capture(cap)
                        cap = None
                        time.sleep(OPEN_RETRY_DELAY)
                        continue

                    consecutive_read_failures = 0
                    log("camera opened successfully")

                ret, frame = cap.read()
                if not ret:
                    consecutive_read_failures += 1
                    if consecutive_read_failures == 1 or (
                        consecutive_read_failures % READ_FAILURE_THRESHOLD == 0
                    ):
                        log(
                            f"camera read failed ({consecutive_read_failures}/"
                            f"{READ_FAILURE_THRESHOLD})"
                        )

                    if consecutive_read_failures >= READ_FAILURE_THRESHOLD:
                        log("camera read failed repeatedly; reopening camera")
                        close_capture(cap)
                        cap = None
                        consecutive_read_failures = 0

                    time.sleep(READ_RETRY_DELAY)
                    continue

                consecutive_read_failures = 0
                with self.frame_lock:
                    self.latest_frame = frame
                    self.latest_seq += 1
                    self.last_frame_at = time.monotonic()

            except Exception as exc:
                log(f"camera reader error: {exc}; reopening in {OPEN_RETRY_DELAY}s")
                close_capture(cap)
                cap = None
                consecutive_read_failures = 0
                time.sleep(OPEN_RETRY_DELAY)

        close_capture(cap)


def main() -> None:
    source = resolve_camera_source()
    output_container: Optional[av.container.OutputContainer] = None
    stream: Optional[Any] = None
    reader = LatestFrameReader(source)

    output_frame_count = 0
    dropped_source_frames = 0
    last_sent_source_seq = -1
    last_heartbeat = 0.0
    target_interval = 1.0 / max(1, FRAME_RATE)

    log(
        "service starting "
        f"(camera_source={source}, resolution={RESOLUTION[0]}x{RESOLUTION[1]}, "
        f"fps={FRAME_RATE}, bitrate={BIT_RATE}, rtmp_url={RTMP_URL})"
    )

    reader.start()

    try:
        while True:
            try:
                if output_container is None or stream is None:
                    close_output(output_container, stream)
                    output_container = None
                    stream = None
                    log(f"connecting to RTMP server: {RTMP_URL}")
                    output_container, stream = open_output()
                    log("RTMP output connected")

                frame, source_seq, frame_time = reader.snapshot()
                if frame is None:
                    time.sleep(NO_NEW_FRAME_DELAY)
                    continue

                if source_seq == last_sent_source_seq:
                    time.sleep(NO_NEW_FRAME_DELAY)
                    continue

                if last_sent_source_seq >= 0 and source_seq > last_sent_source_seq + 1:
                    dropped_source_frames += source_seq - last_sent_source_seq - 1

                last_sent_source_seq = source_seq

                if frame.shape[1] != RESOLUTION[0] or frame.shape[0] != RESOLUTION[1]:
                    frame = cv2.resize(frame, RESOLUTION)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                av_frame = av.VideoFrame.from_ndarray(frame_rgb, format="rgb24")
                av_frame = av_frame.reformat(
                    width=stream.width,
                    height=stream.height,
                    format=stream.pix_fmt,
                )
                av_frame.pts = output_frame_count

                for packet in stream.encode(av_frame):
                    output_container.mux(packet)

                output_frame_count += 1

                now = time.monotonic()
                if HEARTBEAT_INTERVAL > 0 and now - last_heartbeat >= HEARTBEAT_INTERVAL:
                    source_delay_ms = 0.0
                    if frame_time > 0:
                        source_delay_ms = max(0.0, (now - frame_time) * 1000)
                    log(
                        "streaming normally, "
                        f"output_frames={output_frame_count}, "
                        f"dropped_source_frames={dropped_source_frames}, "
                        f"latest_frame_delay_ms={source_delay_ms:.0f}"
                    )
                    last_heartbeat = now

                time.sleep(target_interval)

            except KeyboardInterrupt:
                log("received interrupt signal, stopping service")
                break
            except AV_ERROR as exc:
                log(f"RTMP output error: {exc}; reconnecting in {OPEN_RETRY_DELAY}s")
                close_output(output_container, stream)
                output_container = None
                stream = None
                time.sleep(OPEN_RETRY_DELAY)
            except Exception as exc:
                log(f"unexpected error: {exc}; restarting output in {OPEN_RETRY_DELAY}s")
                close_output(output_container, stream)
                output_container = None
                stream = None
                time.sleep(OPEN_RETRY_DELAY)

    finally:
        close_output(output_container, stream)
        reader.stop()
        log(
            "service stopped, "
            f"output_frames={output_frame_count}, "
            f"dropped_source_frames={dropped_source_frames}"
        )


if __name__ == "__main__":
    main()
