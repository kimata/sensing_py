FROM ubuntu:22.04

ARG TARGETPLATFORM

ENV TZ=Asia/Tokyo
ENV DEBIAN_FRONTEND=noninteractive

RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; then GPIO_LIB="python3-rpi.gpio"; fi; \
    apt-get update && apt-get install -y \
    language-pack-ja \
    python3 python3-pip \
    python3-docopt \
    python3-yaml python3-coloredlogs \
    python3-fluent-logger \
    python3-smbus2 python3-spidev python3-serial python3-bluez \
    ${GPIO_LIB} \
 && apt-get clean \
 && rm -rf /va/rlib/apt/lists/*

WORKDIR /opt/sensing_py
COPY . .

CMD ["./app/app.py"]
