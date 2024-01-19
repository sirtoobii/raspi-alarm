# Raspberry PI Alarm

Yet another Raspberry PI alarm system. 

## OS requirements

Install OS packages

```
sudo apt install -y python3-libcamera python3-kms++
sudo apt install -y python3-prctl libatlas-base-dev ffmpeg libopenjp2-7 python3-pip libcap-dev
```

Enable pigpiod service:

```
sudo systemctl enable pigpiod
```

Enable "Remote GPIO": `Interface Options -> Remote GPIO`

Venv needs to be created with `python3 -m venv --system-site-packages venv` otherwise `libcamera` is not available
