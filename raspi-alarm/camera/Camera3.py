import os
from libcamera import Transform
from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput, FfmpegOutput
import cv2
import time


class Camera3:
    picam2 = Picamera2()

    @staticmethod
    def _apply_timestamp(request):
        ts = time.strftime("%d.%m.%Y %X%z")
        with MappedArray(request, "main") as m:
            cv2.putText(m.array, ts, (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

    def capture_images(self, storage_dir: str, file_prefix: str, n_images=1, add_timestamp: bool = True) -> list:
        transform = Transform(hflip=1, vflip=1)
        still_config = self.picam2.create_still_configuration(transform=transform)

        if add_timestamp:
            self.picam2.pre_callback = self._apply_timestamp
        file_path = os.path.join(storage_dir, file_prefix + "_{:03d}.jpg")
        # Wait a short moment until the camera is ready (otherwise the first image is just black)
        time.sleep(0.1)
        self.picam2.start_and_capture_files(file_path, num_files=n_images, delay=0.2, show_preview=False,
                                            initial_delay=0, capture_mode=still_config)
        self.picam2.stop()
        return [file_path.format(i) for i in range(n_images)]

    def capture_and_stream(self, path: str, duration_secs: int, destination_addr, destination_port: int):
        video_config = self.picam2.create_video_configuration(
            main={"size": (1920, 1080), "format": "RGB888"},
            lores={"size": (1280, 720), "format": "YUV420"}, transform=libcamera.Transform(hflip=1, vflip=1))
        self.picam2.configure(video_config)

        local_encoder = H264Encoder(10000000)
        stream_encoder = H264Encoder(10000000)
        self.picam2.pre_callback = self._apply_timestamp
        self.picam2.start_recording(stream_encoder,
                                    FfmpegOutput(f"-f mpegts udp://{destination_addr}:{destination_port}"),
                                    name="lores")
        self.picam2.start_recording(local_encoder, path, name="main")
        time.sleep(duration_secs)
        self.picam2.stop_recording()

    def capture_video(self, duration_secs: int, path: str):
        self.picam2.configure(self.picam2.create_video_configuration(main={"size": (1920, 1080), "format": "RGB888"},
                                                                     transform=libcamera.Transform(hflip=1, vflip=1)))
        self.picam2.pre_callback = self._apply_timestamp
        encoder = H264Encoder(10000000)
        self.picam2.start_recording(encoder, path)
        time.sleep(duration_secs)
        self.picam2.stop_recording()


if __name__ == '__main__':
    cam = Camera3()
    print(cam.capture_images('.', 'bla', 4))
