"""
Push a local video file to an RTMP endpoint.

This script is meant for demo/testing use when you want to simulate a live
camera stream from a local mp4 file.

Example:
    python iot/rtmpService/push_local_video.py --input D:/demo/demo.mp4
"""

from __future__ import annotations

import argparse
import os
from fractions import Fraction
import time
from pathlib import Path

import av
import cv2


DEFAULT_RTMP_URL = "rtmp://127.0.0.1:1935/live/raw"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_FPS = 30.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Push a local video file to RTMP.")
    parser.add_argument("--input", required=True, help="Local video file path")
    parser.add_argument("--rtmp-url", default=os.environ.get("RTMP_URL", DEFAULT_RTMP_URL))
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--fps", type=float, default=None, help="Output fps, defaults to source fps")
    parser.add_argument(
        "--loop",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Loop the video when it reaches the end",
    )
    parser.add_argument(
        "--realtime",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Throttle frame sending to match the target fps",
    )
    parser.add_argument(
        "--preview",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Show a local preview window while pushing",
    )
    parser.add_argument(
        "--start-delay",
        type=float,
        default=2.0,
        help="Seconds to wait before starting the push",
    )
    return parser


def open_capture(video_path: Path) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video file: {video_path}")
    return cap


def read_source_info(cap: cv2.VideoCapture) -> tuple[float, int, int]:
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps is None or fps <= 1e-2:
        fps = DEFAULT_FPS

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or DEFAULT_WIDTH
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or DEFAULT_HEIGHT
    return fps, width, height


def open_rtmp_stream(rtmp_url: str, width: int, height: int, fps: float):
    rate = Fraction(int(round(fps)), 1)
    while True:
        try:
            container = av.open(rtmp_url, mode="w", format="flv")
            stream = container.add_stream("h264", rate=rate)
            stream.width = width
            stream.height = height
            stream.pix_fmt = "yuv420p"
            stream.options = {
                "tune": "zerolatency",
                "preset": "ultrafast",
            }
            return container, stream
        except Exception as exc:  # noqa: BLE001
            print(f"RTMP connect failed: {exc}")
            print("Retrying in 3 seconds...")
            time.sleep(3)


def push_video(
    video_path: Path,
    rtmp_url: str,
    out_width: int,
    out_height: int,
    out_fps: float | None,
    loop: bool,
    realtime: bool,
    preview: bool,
    start_delay: float,
) -> None:
    cap = open_capture(video_path)
    source_fps, source_width, source_height = read_source_info(cap)
    target_fps = out_fps or source_fps
    if target_fps <= 0:
        target_fps = DEFAULT_FPS

    width = out_width or source_width or DEFAULT_WIDTH
    height = out_height or source_height or DEFAULT_HEIGHT

    print(f"Input video: {video_path}")
    print(f"RTMP url   : {rtmp_url}")
    print(f"Output     : {width}x{height} @ {target_fps:.2f} fps")
    print(f"Loop       : {loop}")
    print(f"Realtime   : {realtime}")
    print(f"Preview    : {preview}")

    time.sleep(max(0.0, start_delay))

    container, stream = open_rtmp_stream(rtmp_url, width, height, target_fps)
    frame_index = 0
    loop_count = 0
    start_time = time.monotonic()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                if not loop:
                    print("Reached the end of the video.")
                    break

                loop_count += 1
                print(f"Looping video, round {loop_count}")
                cap.release()
                cap = open_capture(video_path)
                continue

            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            av_frame = av.VideoFrame.from_ndarray(frame_rgb, format="rgb24")
            av_frame = av_frame.reformat(width=width, height=height, format="yuv420p")
            av_frame.pts = frame_index

            for packet in stream.encode(av_frame):
                container.mux(packet)

            if preview:
                cv2.imshow("push_local_video preview", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("Preview window closed by user.")
                    break

            if realtime:
                target_time = start_time + (frame_index / target_fps)
                sleep_time = target_time - time.monotonic()
                if sleep_time > 0:
                    time.sleep(sleep_time)

            frame_index += 1

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        try:
            for packet in stream.encode():
                container.mux(packet)
        except Exception:  # noqa: BLE001
            pass
        container.close()
        cap.release()
        if preview:
            cv2.destroyAllWindows()

    print(f"Done. Total pushed frames: {frame_index}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    video_path = Path(args.input).expanduser().resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"video file not found: {video_path}")

    push_video(
        video_path=video_path,
        rtmp_url=args.rtmp_url,
        out_width=args.width,
        out_height=args.height,
        out_fps=args.fps,
        loop=args.loop,
        realtime=args.realtime,
        preview=args.preview,
        start_delay=args.start_delay,
    )


if __name__ == "__main__":
    main()
