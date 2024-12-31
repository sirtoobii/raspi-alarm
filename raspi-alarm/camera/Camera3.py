import os
from typing import List

from libcamera import Transform
from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput, FfmpegOutput
import cv2
import time
import numpy as np


class Camera3:
    picam2 = Picamera2()
    _raw_images: List[np.ndarray] = []
    _should_add_timestamp: bool = True

    def _pre_compress_callback(self, request):
        with MappedArray(request, "main") as m:
            self._raw_images.append(m.array)
            if self._should_add_timestamp:
                ts = time.strftime("%d.%m.%Y %X%z")
                cv2.putText(m.array, ts, (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

    def capture_images(self, storage_dir: str, file_prefix: str, n_images=1, add_timestamp: bool = True,
                       wait_between_images: int = 1) -> list:
        self._raw_images.clear()
        transform = Transform(hflip=1, vflip=1)
        still_config = self.picam2.create_still_configuration(transform=transform)

        self._should_add_timestamp = add_timestamp
        self.picam2.pre_callback = self._pre_compress_callback
        file_path = os.path.join(storage_dir, file_prefix + "_{:03d}.jpg")
        image_paths = [file_path.format(i) for i in range(n_images)]
        self.picam2.configure(still_config)

        # Wait a short moment until the camera is ready (otherwise the first image is just black)
        time.sleep(0.1)
        self.picam2.start(show_preview=False)
        for image_path in image_paths:
            self.picam2.capture_file(image_path)
            time.sleep(wait_between_images)

        self.picam2.stop()
        return image_paths

    def get_last_raw_images(self) -> List[np.ndarray]:
        """
        Get last captured images as a list of ndarrys. (Warning, the list contains references and not copies)
        :return: Possibly empty list of raw images
        """
        return self._raw_images

    def capture_and_stream(self, path: str, duration_secs: int, destination_addr, destination_port: int):
        video_config = self.picam2.create_video_configuration(
            main={"size": (1920, 1080), "format": "RGB888"},
            lores={"size": (1280, 720), "format": "YUV420"}, transform=libcamera.Transform(hflip=1, vflip=1))
        self.picam2.configure(video_config)

        local_encoder = H264Encoder(10000000)
        stream_encoder = H264Encoder(10000000)
        self.picam2.pre_callback = self._pre_compress_callback
        self.picam2.start_recording(stream_encoder,
                                    FfmpegOutput(f"-f mpegts udp://{destination_addr}:{destination_port}"),
                                    name="lores")
        self.picam2.start_recording(local_encoder, path, name="main")
        time.sleep(duration_secs)
        self.picam2.stop_recording()

    def capture_video(self, duration_secs: int, path: str):
        self.picam2.configure(self.picam2.create_video_configuration(main={"size": (1920, 1080), "format": "RGB888"},
                                                                     transform=libcamera.Transform(hflip=1, vflip=1)))
        self.picam2.pre_callback = self._pre_compress_callback
        encoder = H264Encoder(10000000)
        self.picam2.start_recording(encoder, path)
        time.sleep(duration_secs)
        self.picam2.stop_recording()


if __name__ == '__main__':
    cam = Camera3()
    print(cam.capture_images('.', 'bla', 4))
