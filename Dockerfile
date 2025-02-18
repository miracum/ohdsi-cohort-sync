FROM docker.io/library/python:3.13.1-slim@sha256:026dd417a88d0be8ed5542a05cff5979d17625151be8a1e25a994f85c87962a5 AS build
WORKDIR /opt/app
ENV GIT_ASKPASS=/opt/app/askpass.py

# hadolint ignore=DL3008
RUN <<EOF
adduser --uid 65532 --no-create-home --disabled-password ohdsi-git-sync

# at least write-permissions are required since we will end up cloning the repo
chown -R ohdsi-git-sync:ohdsi-git-sync /opt/app

apt-get update
apt-get install -y --no-install-recommends git
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF

COPY requirements.txt .

RUN pip install --require-hashes --no-deps --no-cache-dir -r requirements.txt

COPY src .

RUN chmod +x /opt/app/askpass.py

USER 65532:65532
ENTRYPOINT [ "python", "/opt/app/ohdsi_git_sync.py" ]

# Can't use distroless since we require git+dependencies.
# Copying them from the base image is... annoying.
# The below fails with `stderr: 'git: error while loading shared libraries: libpcre2-8.so.0: cannot open shared object file: No such file or directory'`
# FROM gcr.io/distroless/python3-debian12:nonroot@sha256:27d2d6afcfb109e4c147449d4af957f71cb770196527d0da1d1d92b9680b0daa
# WORKDIR /opt/app
# ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages

# COPY --from=build /usr/bin/git /usr/bin/git
# COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# COPY --from=build /opt/app .
