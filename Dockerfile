# MeTTaClaw Dockerfile
# ========================================================================
# Podman-compatible Docker image for MeTTaClaw
# ========================================================================

# Base image
FROM archlinux:latest

# PeTTa repo and branch
ARG PETTA_REPO=https://github.com/trueagi-io/PeTTa
ARG PETTA_BRANCH=main

# MeTTaClaw repo and branch
ARG METTACLAW_REPO=https://github.com/autonull/mettaclaw
ARG METTACLAW_BRANCH=main

# Container paths
ARG CONTAINER_PETTA_PATH=/opt/PeTTa
ARG CONTAINER_METTACLAW_PATH=/opt/PeTTa/repos/mettaclaw

# ========================================================================
# Environment
# ========================================================================
ENV TERM=xterm-256color

# ========================================================================
# Install Dependencies (Arch Linux uses pacman)
# ========================================================================
RUN pacman-key --init && pacman -Sy --noconfirm \
    base-devel \
    git \
    curl \
    ca-certificates \
    python \
    python-pip \
    libffi \
    openssl \
    cargo \
    rust \
    cmake \
    wget \
    gmp \
    libedit \
    readline \
    libarchive \
    pcre \
    libyaml \
    swi-prolog \
    || true

# Install janus for Python interop (optional - can work without)
RUN pip3 install --break-system-packages janus || true

# ========================================================================
# Clone PeTTa
# ========================================================================
RUN git clone --depth 1 --branch ${PETTA_BRANCH} ${PETTA_REPO} ${CONTAINER_PETTA_PATH}

# ========================================================================
# Clone MeTTaClaw
# ========================================================================
RUN git clone --depth 1 --branch ${METTACLAW_BRANCH} ${METTACLAW_REPO} ${CONTAINER_METTACLAW_PATH}

# ========================================================================
# Setup
# ========================================================================
WORKDIR ${CONTAINER_PETTA_PATH}

RUN cp ${CONTAINER_METTACLAW_PATH}/run.metta ./

ENV PETTA_PATH=${CONTAINER_PETTA_PATH}
ENV PATH="${CONTAINER_PETTA_PATH}:${PATH}"

RUN chmod +x run.sh

CMD ["/bin/bash", "-c", "echo 'MeTTaClaw ready!'; echo 'To run: ./run.sh run.metta'"]