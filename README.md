# ohdsi-cohort-sync

A tool for backing up OHDSI WebAPI cohorts in a git repository.

## Usage

> **Note:** the current version is intended to be run on an ephemeral filesystem as it tries to always clone the latest version from the remote and not track changes locally. Ie. if you receive a _'fatal: destination path '/git' already exists and is not an empty directory'_, you have to manually clear all paths and start again.

```console
usage: ohdsi_git_sync.py [-h] --git-repo-url GIT_REPO_URL [--git-branch GIT_BRANCH] [--git-destination GIT_DESTINATION] --git-sub-path GIT_SUB_PATH [--git-commit-user-name GIT_COMMIT_USER_NAME]
                         [--git-commit-email GIT_COMMIT_EMAIL] [--cohort-file-prefix COHORT_FILE_PREFIX] --webapi-url WEBAPI_URL [--webapi-auth-login-path WEBAPI_AUTH_LOGIN_PATH] [--webapi-auth-username WEBAPI_AUTH_USERNAME]
                         [--webapi-auth-password WEBAPI_AUTH_PASSWORD] [--dry-run]

options:
  -h, --help            show this help message and exit
  --git-repo-url GIT_REPO_URL
                        Git repo URL, e.g. https://github.com/miracum/atlas-git-sync.git [env var: GIT_REPO_URL]
  --git-branch GIT_BRANCH
                        Git branch to clone and push to. Default: 'master' [env var: GIT_BRANCH]
  --git-destination GIT_DESTINATION
                        Path in the local filesystem where to clone the git repo. Created if it doesn't already exist. Default: 'git' [env var: GIT_DESTINATION]
  --git-sub-path GIT_SUB_PATH
                        Path in the repo to store the retrieved cohort definitions. Created if it doesn't already exist. [env var: GIT_SUB_PATH]
  --git-commit-user-name GIT_COMMIT_USER_NAME
                        Name to associate with the commit. Equivalent to Git's config.user.name setting. Default: $GIT_USERNAME [env var: GIT_COMMIT_USER_NAME]
  --git-commit-email GIT_COMMIT_EMAIL
                        Email to associate with the commit. Equivalent to Git's config.user.email setting [env var: GIT_COMMIT_EMAIL]
  --cohort-file-prefix COHORT_FILE_PREFIX
                        String to prepend the saved cohort definition .json files. Default: 'cohort-' [env var: COHORT_FILE_PREFIX]
  --webapi-url WEBAPI_URL
                        OHDSI WebAPI base URL, e.g. https://atlas.ohdsi.org/WebAPI [env var: WEBAPI_URL]
  --webapi-auth-login-path WEBAPI_AUTH_LOGIN_PATH
                        Relative path to the WebAPI login provider, e.g. /user/login/db [env var: WEBAPI_AUTH_LOGIN_PATH]
  --webapi-auth-username WEBAPI_AUTH_USERNAME
                        Username to authenticate against the WebAPI with [env var: WEBAPI_AUTH_USERNAME]
  --webapi-auth-password WEBAPI_AUTH_PASSWORD
                        Password to authenticate against the WebAPI with [env var: WEBAPI_AUTH_PASSWORD]
  --dry-run             Dry run mode: clone repo, fetch cohorts, and commit but don't push them to origin. Default: 'False' [env var: DRY_RUN]

 In general, command-line values override environment variables which override defaults.
```

For example:

```sh
python ohdsi_git_sync.py \
    --git-repo-url="https://git.example.com/cohorts.git" \
    --webapi-url="http://host.docker.internal:8083/WebAPI" \
    --git-sub-path="test" \
    --git-commit-user-name="OHDSI Cohort Sync Bot" \
    --git-commit-email="ohdsi-git-sync@example.com"
```

### Run Container

When running as a container **you will need to explicitely set your git credentials** via the `GIT_USERNAME` and `GIT_PASSWORD` environment vars.

For example:

```sh
docker run --rm \
    -e GIT_USERNAME=ohdsi-git-sync \
    -e GIT_PASSWORD=<Password/Personal Access Token> \
    -e GIT_REPO_URL="https://git.example.com/cohorts.git" \
    -e WEBAPI_URL="http://host.docker.internal:8083/WebAPI" \
    -e GIT_SUB_PATH="test" \
    -e GIT_COMMIT_USER_NAME="OHDSI Cohort Sync Bot" \
    -e GIT_COMMIT_EMAIL="ohdsi-git-sync@example.com" \
    ghcr.io/miracum/ohdsi-cohort-sync:latest
```

When running outside of a container, your local credentials and credential managers are invoked to authenticate.

## Contributing

After cloning this repo, run the following to install a development dependencies:

```sh
pip install -r requirements-dev.txt
```

Run locally:

```sh
python ./src/ohdsi_git_sync.py \
  --git-repo-url=https://git.example.com/cohorts.git \
  --git-sub-path=test \
  --webapi-url=http://host.docker.internal:8083/WebAPI
```
