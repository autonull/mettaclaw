# MeTTaClaw Dockerfile
# ========================================================================

FROM archlinux:latest

ENV TERM=xterm-256color
ENV PETTA_PATH=/opt/PeTTa
ENV PATH="/opt/PeTTa:${PATH}"

# ========================================================================
# Install system dependencies
# ========================================================================
RUN pacman-key --init && \
    pacman -Sy --noconfirm \
        base-devel git curl ca-certificates python python-pip \
        libffi openssl cargo rust cmake wget \
        gmp libedit readline libarchive pcre libyaml swi-prolog \
    || true

RUN pip3 install --break-system-packages janus-swi janus litellm || true

# ========================================================================
# Clone PeTTa (the execution engine)
# ========================================================================
RUN git clone --depth 1 --branch main \
    https://github.com/trueagi-io/PeTTa /opt/PeTTa

# ========================================================================
# Clone MeTTaClaw (the agent code)
# ========================================================================
RUN git clone --depth 1 --branch main \
    https://github.com/autonull/mettaclaw /opt/PeTTa/repos/mettaclaw

# ========================================================================
# Setup container runner
# ========================================================================
WORKDIR /opt/PeTTa
COPY container_run.sh /opt/PeTTa/container_run.sh
COPY agent_run.py /opt/PeTTa/agent_run.py
RUN chmod +x /opt/PeTTa/container_run.sh

ENTRYPOINT []
CMD ["/opt/PeTTa/container_run.sh"]
