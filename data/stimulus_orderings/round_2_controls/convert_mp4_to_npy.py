# -*- coding: utf-8 -*-
"""Convert an MP4 into the grayscale uint8 NumPy format used by Camstim."""

from __future__ import print_function

import argparse
import os

import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


PROGRESS_INTERVAL_SECONDS = 10.0


def _read_movie_metadata(capture, input_path):
    frame_count = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
    frame_rate = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
    height = int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    if frame_count <= 0:
        raise ValueError("Could not determine frame count for {}."
                         .format(input_path))
    if frame_rate <= 0:
        raise ValueError("Could not determine frame rate for {}."
                         .format(input_path))
    if width <= 0 or height <= 0:
        raise ValueError("Could not determine frame dimensions for {}."
                         .format(input_path))

    return frame_count, frame_rate, width, height


def _to_grayscale(frame):
    if frame.ndim == 2:
        return frame
    if frame.ndim != 3:
        raise ValueError("Decoded frame must have two or three dimensions.")
    if frame.shape[2] == 3:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if frame.shape[2] == 4:
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
    raise ValueError("Decoded frame has an unsupported channel count: {}."
                     .format(frame.shape[2]))


def convert_mp4_to_npy(input_path, output_path, overwrite=False):
    """Stream an MP4 into a Camstim-compatible (time, y, x) uint8 array."""
    if cv2 is None:
        raise RuntimeError(
            "OpenCV is required; install opencv-python-headless first.")
    if not os.path.isfile(input_path):
        raise IOError("Input movie does not exist: {}".format(input_path))
    if os.path.splitext(input_path)[1].lower() != ".mp4":
        raise ValueError("Input movie must have an .mp4 extension.")
    if os.path.splitext(output_path)[1].lower() != ".npy":
        raise ValueError("Output movie must have an .npy extension.")

    output_path = os.path.abspath(output_path)
    output_directory = os.path.dirname(output_path)
    partial_path = output_path + ".partial"
    if not os.path.isdir(output_directory):
        raise IOError("Output directory does not exist: {}"
                      .format(output_directory))
    if os.path.exists(output_path) and not overwrite:
        raise IOError("Output already exists: {}".format(output_path))
    if os.path.exists(partial_path):
        raise IOError("Partial output already exists: {}".format(partial_path))

    capture = cv2.VideoCapture(input_path)
    if not capture.isOpened():
        capture.release()
        raise IOError("OpenCV could not open: {}".format(input_path))

    movie = None
    converted = None
    try:
        frame_count, frame_rate, width, height = _read_movie_metadata(
            capture, input_path)
        output_bytes = frame_count * width * height
        duration_seconds = frame_count / frame_rate
        print("Input: {} frames, {} x {}, {:.6g} Hz, {:.3f} seconds"
              .format(frame_count, width, height, frame_rate,
                      duration_seconds))
        print("Output: {:.3f} GiB as uint8 ({}, {}, {})"
              .format(output_bytes / float(1024 ** 3), frame_count, height,
                      width))

        movie = np.lib.format.open_memmap(
            partial_path,
            mode="w+",
            dtype=np.uint8,
            shape=(frame_count, height, width))
        progress_interval = max(
            1, int(round(frame_rate * PROGRESS_INTERVAL_SECONDS)))

        for frame_index in range(frame_count):
            decoded, frame = capture.read()
            if not decoded:
                raise ValueError(
                    "Decode ended after {} of {} frames."
                    .format(frame_index, frame_count))
            grayscale_frame = _to_grayscale(frame)
            if grayscale_frame.shape != (height, width):
                raise ValueError(
                    "Frame {} has shape {}; expected ({}, {})."
                    .format(frame_index, grayscale_frame.shape, height, width))
            if grayscale_frame.dtype != np.uint8:
                raise ValueError(
                    "Frame {} has dtype {}; expected uint8."
                    .format(frame_index, grayscale_frame.dtype))
            movie[frame_index] = grayscale_frame

            completed = frame_index + 1
            if (completed % progress_interval == 0 or
                    completed == frame_count):
                print("Converted {}/{} frames ({:.1f}%)."
                      .format(completed, frame_count,
                              completed * 100.0 / frame_count))

        extra_frame, _ = capture.read()
        if extra_frame:
            raise ValueError(
                "Movie contains more frames than its metadata reports.")

        movie.flush()
        del movie
        movie = None

        converted = np.load(partial_path, mmap_mode="r")
        if converted.shape != (frame_count, height, width):
            raise ValueError("Saved array has an unexpected shape: {}."
                             .format(converted.shape))
        if converted.dtype != np.uint8:
            raise ValueError("Saved array has an unexpected dtype: {}."
                             .format(converted.dtype))
        del converted
        converted = None

        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(partial_path, output_path)
    except BaseException:
        if converted is not None:
            del converted
        if movie is not None:
            del movie
        if os.path.exists(partial_path):
            os.remove(partial_path)
        raise
    finally:
        capture.release()

    print("Saved {}".format(output_path))


def main():
    parser = argparse.ArgumentParser(
        description="Convert an MP4 to Camstim's grayscale NumPy format.")
    parser.add_argument("input_mp4", help="Source MP4 movie")
    parser.add_argument("output_npy", help="Destination .npy file")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing destination after conversion succeeds")
    args = parser.parse_args()

    try:
        convert_mp4_to_npy(
            args.input_mp4, args.output_npy, overwrite=args.overwrite)
    except (IOError, RuntimeError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
