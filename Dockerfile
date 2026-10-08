FROM debian@sha256:d7e12182ce18b85b93007c1dedf31f2d29e01ccf3182cc4017c709b6259bc132
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.12 python3=3.13.5-1 python3-venv=3.13.5-1 python3-pip=25.1.1+dfsg-1 ninja-build=1.12.1-1 pkg-config=1.8.1-4 \
    libglib2.0-dev=2.84.4-3~deb13u5 libpixman-1-dev=0.44.0-3 zlib1g-dev=1:1.3.dfsg+really1.3.1-1+b1 libfdt-dev=1.7.2-2+b1 git=1:2.47.3-0+deb13u1 ca-certificates=20250419 curl=8.14.1-2+deb13u5 \
    xz-utils=5.8.1-1+deb13u2 device-tree-compiler=1.7.2-2+b1 e2fsprogs=1.47.2-3+b12 mtools=4.0.48-1 fdisk=2.41.5-0+deb13u1 python3-pil=11.1.0-5+deb13u4 ffmpeg=7:7.1.5-0+deb13u1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
