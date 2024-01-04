import socket

from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput, FfmpegOutput
import cv2
import time


class Camera3:
    picam2 = Picamera2()

    def __init__(self):
        pass

    @staticmethod
    def _apply_timestamp(request):
        ts = time.strftime("%d.%m.%Y %X%z")
        with MappedArray(request, "main") as m:
            cv2.putText(m.array, ts, (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

    def capture_image(self, path: str, add_timestamp: bool = True, n_images=1):
        self.picam2.configure(self.picam2.still_configuration)
        self.picam2.pre_callback = self._apply_timestamp
        self.picam2.start()
        self.picam2.capture_file(path)
        self.picam2.stop()

    def capture_and_stream(self, path: str, destination_addr, destination_port: int):
        video_config = self.picam2.create_video_configuration(main={"size": (1920, 1080), "format": "RGB888"},
                                                              lores={"size": (1280, 720), "format": "YUV420"})
        self.picam2.configure(video_config)

        local_encoder = H264Encoder(10000000)
        stream_encoder = H264Encoder(10000000)
        self.picam2.pre_callback = self._apply_timestamp
        self.picam2.start_recording(stream_encoder,
                                    FfmpegOutput(f"-f mpegts udp://{destination_addr}:{destination_port}"),
                                    name="lores")
        self.picam2.start_recording(local_encoder, path, name="main")

        time.sleep(30)
        self.picam2.stop_recording()

    def capture_video(self, duration_secs: int, path: str):
        self.picam2.configure(self.picam2.create_video_configuration(main={"size": (1920, 1080), "format": "RGB888"}))
        self.picam2.pre_callback = self._apply_timestamp
        encoder = H264Encoder(10000000)
        self.picam2.start_recording(encoder, path)
        time.sleep(duration_secs)
        self.picam2.stop_recording()
