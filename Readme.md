# Rasperberry PI Alarm



## OS requirements

Install OS packages

```
sudo apt install -y python3-libcamera python3-kms++
sudo apt install -y python3-prctl libatlas-base-dev ffmpeg libopenjp2-7 python3-pip
```

Enable pigpiod service:

```
sudo systemctl enable pigpiod
```

Enable "Remote GPIO": `Interface Options -> Remote GPIO`
