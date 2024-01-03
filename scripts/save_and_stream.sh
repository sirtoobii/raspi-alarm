# Hardware accel, but no timestamps
libcamera-vid -v 0 --nopreview --inline -t 0 --height 1080 --width 1920 --codec h264 --framerate 20 -o - | gst-launch-1.0 -v fdsrc ! h264parse config-interval=10 \
                                                                        ! tee name=t \
                                                                        t. ! queue \
                                                                           ! mpegtsmux \
                                                                           ! udpsink host=192.168.178.163 port=5004 \
                                                                        t. ! queue \
                                                                           ! filesink location=v.mp4


# No hardware accel but built in timestamps
gst-launch-1.0 -v libcamerasrc ! video/x-raw, width=1280, height=720, framerate=15/1 \
  ! clockoverlay time-format="%d.%m.%Y %H:%M:%S" ! videoconvert \
  ! x264enc tune=zerolatency byte-stream=true bitrate=400 threads=4 \
  ! h264parse config-interval=10 \
  ! tee name=t \
  t. ! queue ! mpegtsmux ! udpsink host=192.168.178.163 port=5004 \
  t. ! queue ! filesink location=v.mp4
