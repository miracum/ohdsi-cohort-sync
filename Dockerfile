FROM docker.io/library/python:3.11.7-slim@sha256:637774748f62b832dc11e7b286e48cd716727ed04b45a0322776c01bc526afc3 AS build
WORKDIR /opt/app
ENV GIT_ASKPASS=/opt/app/askpass.py
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --uid 65532 --no-create-home --disabled-password ohdsi-git-sync && \
    chown -R ohdsi-git-sync:ohdsi-git-sync /opt/app

COPY requirements.txt .

RUN pip install --require-hashes --no-cache-dir -r requirements.txt

COPY src .

RUN chmod +x /opt/app/askpass.py

USER 65532:65532
ENTRYPOINT [ "python", "/opt/app/ohdsi_git_sync.py" ]
