"""
RTMP stream check helper.

Usage:
    python check_stream.py
    python check_stream.py --url rtmp://127.0.0.1:1935:1935/live/raw
"""

from __future__ import annotations

import argparse
import time

import cv2


DEFAULT_STREAM_URL = "rtmp://123.56.248.17:1935/live/raw"
    

def check_rtmp_stream(stream_url: str, attempts: int = 10, delay: float = 0.5) -> bool:
    print(f"Checking stream: {stream_url}")
    cap = cv2.VideoCapture(stream_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    success_count = 0
    for idx in range(attempts):
        ret, frame = cap.read()
        if ret:
            success_count += 1
            print(f"Read frame {idx + 1} successfully, size={frame.shape}")
        else:
            print(f"Read frame {idx + 1} failed")
        time.sleep(delay)

    cap.release()

    print(f"Result: {success_count}/{attempts} frames read")
    if success_count > 0:
        print("Stream is available")
        return True

    print("Stream is unavailable")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether an RTMP stream is readable.")
    parser.add_argument("--url", default=DEFAULT_STREAM_URL, help="RTMP stream url")
    parser.add_argument("--attempts", type=int, default=10, help="Number of read attempts")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between attempts")
    args = parser.parse_args()

    print("=" * 50)
    print("RTMP stream check")
    print("=" * 50)
    check_rtmp_stream(args.url, attempts=args.attempts, delay=args.delay)


if __name__ == "__main__":
    main()
