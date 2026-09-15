# Cursor Cloud Agent environment for the synthetic data factory.
# Do not COPY the repository; Cursor checks out the target commit itself.
# Official CPython 3.14 line (same family as GitHub Actions setup-python),
# not Ubuntu 24.04's distro python3 (3.12).
FROM python:3.14-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        sudo \
    && rm -rf /var/lib/apt/lists/*

# python:*-slim has no ubuntu user; Cloud agents clone with git and escalate with sudo.
RUN groupadd --gid 1000 ubuntu \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ubuntu \
    && printf 'ubuntu ALL=(ALL) NOPASSWD:ALL\n' > /etc/sudoers.d/ubuntu \
    && chmod 0440 /etc/sudoers.d/ubuntu

WORKDIR /workspace
