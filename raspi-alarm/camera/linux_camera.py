import datetime
import os.path
import time
from dataclasses import dataclass

import cv2
from numpy import ndarray


@dataclass
class ImageCaptureResult:
    raw_images: list[ndarray]


class LinuxCamera:

    @staticmethod
    def add_timestamp(frame: ndarray) -> ndarray:
        ts = time.strftime("%d.%m.%Y %X%z")
        cv2.putText(frame, ts, (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
        return frame

    def __init__(self, device=0, fps: int = 20, width: int = 1280, height: int = 720):
        self.device = device
        self.fps = fps
        self.width = width
        self.height = height
        self.cap: cv2.VideoCapture | None = None

    def __enter__(self):
        self.cap = cv2.VideoCapture(self.device)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cap:
            self.cap.release()

    def frames(self, wait_between_captures_sec: float = 0,
               add_timestamp: bool = True, n_frames: int = -1):
        frame_ctr = 0
        while frame_ctr != n_frames:
            start_frame = time.time()
            ret, frame = self.cap.read()
            if not ret:
                break
            if add_timestamp:
                frame = LinuxCamera.add_timestamp(frame)
            yield frame
            if n_frames != -1:
                frame_ctr += 1
            if wait_between_captures_sec > 0:
                elapsed = time.time() - start_frame
                time.sleep(max(wait_between_captures_sec - elapsed, 0))

    @staticmethod
    def save_images(raw_images: list[ndarray],
                    destination_folder: str,
                    prefix: str) -> list[str]:
        image_paths = []
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        date_str = datetime.datetime.now().strftime("%d%m%d-%H%M%S")
        for i, raw_image in enumerate(raw_images):
            _file_path = os.path.join(destination_folder, f"{prefix}_{date_str}_{i}.jpg")
            cv2.imwrite(_file_path, raw_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
            image_paths.append(_file_path)
        return image_paths
