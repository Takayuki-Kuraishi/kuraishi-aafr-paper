# aafr-paper-env
# Self-contained analysis environment for the AAFR paper.
# Covers both image processing (brightness, distance computation)
# and statistical analysis (correlation, bootstrap CI, plotting).
#
# Build:
#   docker build -t aafr-paper-env .
#
# Run (mount the Analysis directory and keep container alive):
#   docker run -d --name aafr-paper-env \
#       --restart unless-stopped \
#       -v /home/takayukikuraishi/Analysis:/work \
#       -w /work \
#       aafr-paper-env

FROM python:3.11-slim-bookworm

# System dependencies for OpenCV (libGL for cv2.imshow / imdecode etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Pin all Python package versions for reproducibility.
RUN pip install --no-cache-dir \
        numpy==1.26.4 \
        pandas==2.2.2 \
        scipy==1.15.3 \
        matplotlib==3.9.0 \
        opencv-python-headless==4.8.1.78

WORKDIR /work
CMD ["tail", "-f", "/dev/null"]
