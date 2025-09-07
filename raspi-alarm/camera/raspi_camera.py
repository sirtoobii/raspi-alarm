import time
from typing import ClassVar

from .linux_camera import LinuxCamera
from picamera2 import Picamera2
from libcamera import Transform


class RaspiCamera(LinuxCamera):
    picam2: ClassVar[Picamera2] = Picamera2()


    def __init__(self, fps: int = 20, width: int = 1280, height: int = 720):
        super().__init__(device=0, fps=fps, width=width, height=height)

    def __enter__(self):
        transform = Transform(hflip=1, vflip=1)
        still_config = self.picam2.create_still_configuration(transform=transform,
                                                              main={"size": (self.height, self.width)},
                                                              raw={'size': (2304, 1296)},
                                                              buffer_count=2,
                                                              controls={'FrameRate': 50} )
        self.picam2.configure(still_config)
        # Wait a short moment until the camera is ready (otherwise the first image is just black)
        time.sleep(0.1)
        self.picam2.start(show_preview=False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.picam2.stop()

    def frames(self, wait_between_captures_sec: float = 0,
               add_timestamp: bool = True, n_frames: int = -1):
        frame_ctr = 0
        while frame_ctr != n_frames:
            start_frame = time.time()
            frame = self.picam2.capture_array()
            if add_timestamp:
                frame = LinuxCamera.add_timestamp(frame)
            yield frame
            if n_frames != -1:
                frame_ctr += 1
            if wait_between_captures_sec > 0:
                elapsed = time.time() - start_frame
                time.sleep(max(wait_between_captures_sec - elapsed, 0))

if __name__ == '__main__':
    print("Starting...")
    with RaspiCamera() as cam:
        for frame in cam.frames(wait_between_captures_sec=1, n_frames=4):
            print(frame)