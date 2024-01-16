#!/usr/bin/env python3

import logging
from os import environ
from pathlib import Path

import configargparse
import git
import requests
import simplejson
from slugify import slugify


def clone_repo(repo_url, branch, destination):
    repo = git.Repo.clone_from(repo_url, branch=branch, to_path=destination)

    logging.debug(f"Status: '{repo.git.status()}'")
    logging.info(f"Active branch: {repo.active_branch}")
    logging.info(f"Last commit: {str(repo.head.commit.hexsha)}")
    for remote in repo.remotes:
        logging.info(f"Remote {remote} with URL {remote.url}")


def fetch_cohorts(session, base_url):
    definitions_url = base_url + "/cohortdefinition"

    response = session.get(definitions_url)
    response.raise_for_status()

    cohort_list = response.json()

    cohorts = []
    for cohort in cohort_list:
        cohort_id = cohort["id"]
        detail_url = definitions_url + f"/{cohort_id}"
        logging.info(
            "Fetching details for cohort '%d' ('%s') from %s",
            cohort_id,
            cohort["name"],
            detail_url,
        )

        r = session.get(detail_url)
        r.raise_for_status()

        cohorts.append(r.json())

    return cohorts


def write_cohorts(cohorts, git_root, git_sub_path, cohort_file_prefix):
    for cohort in cohorts:
        cohort_id = cohort["id"]
        cohort_name = slugify(cohort["name"])

        dir = Path().cwd().joinpath(git_root, git_sub_path)
        dir.mkdir(parents=True, exist_ok=True)

        path = dir.joinpath(f"{cohort_file_prefix}{cohort_name}.json")

        logging.info("Saving cohort expression for '%d' to '%s'", cohort_id, path)

        cohort_expression = simplejson.loads(cohort["expression"])

        with open(path, "w+") as cohort_file:
            cohort_file.write(simplejson.dumps(cohort_expression, indent=4))


def add_commit_and_push(git_root, git_commit_user_name, git_commit_email, dry_run):
    repo = git.Repo(git_root)

    if git_commit_user_name:
        logging.info(f"Setting user.name config to {git_commit_user_name}")
        repo.config_writer().set_value("user", "name", git_commit_user_name).release()
    elif "GIT_USERNAME" in environ:
        logging.info(f"Setting user.name config to {environ['GIT_USERNAME']}")
        repo.config_writer().set_value(
            "user", "name", environ["GIT_USERNAME"]
        ).release()

    if git_commit_email:
        logging.info(f"Setting user.email config to {git_commit_email}")
        repo.config_writer().set_value("user", "email", git_commit_email).release()

    repo.git.add(all=True)

    diff = repo.index.diff("HEAD")
    if len(diff) == 0:
        logging.info("No files have changed. Not committing")
        return
    else:
        logging.info(f"Comitting {len(diff)} change(s)")

    repo.index.commit("updated cohorts")
    origin = repo.remote(name="origin")
    if not dry_run:
        logging.info("Pushing commit")
        origin.push()
    else:
        logging.info("Running in dry-run mode. Not pushing commit")
    logging.debug(f"Status: '{repo.git.status()}'")


def main():
    p = configargparse.ArgParser()
    p.add(
        "--git-repo-url",
        required=True,
        env_var="GIT_REPO_URL",
        help="Git repo URL, e.g. https://github.com/miracum/atlas-git-sync.git",
    )
    p.add(
        "--git-branch",
        required=False,
        env_var="GIT_BRANCH",
        help="Git branch to clone and push to. Default: 'master'",
        default="master",
    )
    p.add(
        "--git-destination",
        required=False,
        env_var="GIT_DESTINATION",
        help="Path in the local filesystem where to clone the git repo. "
        + "Created if it doesn't already exist. Default: 'git'",
        default="git",
    )
    p.add(
        "--git-sub-path",
        required=True,
        env_var="GIT_SUB_PATH",
        help="Path in the repo to store the retrieved cohort definitions. "
        + "Created if it doesn't already exist.",
    )
    p.add(
        "--git-commit-user-name",
        required=False,
        env_var="GIT_COMMIT_USER_NAME",
        help="Name to associate with the commit. Equivalent to Git's "
        + "config.user.name setting. Default: $GIT_USERNAME",
    )
    p.add(
        "--git-commit-email",
        required=False,
        env_var="GIT_COMMIT_EMAIL",
        help="Email to associate with the commit. "
        + "Equivalent to Git's config.user.email setting",
        default="",
    )
    p.add(
        "--cohort-file-prefix",
        required=False,
        env_var="COHORT_FILE_PREFIX",
        help="String to prepend the saved cohort "
        + "definition .json files. Default: 'cohort-'",
        default="cohort-",
    )
    p.add(
        "--webapi-url",
        env_var="WEBAPI_URL",
        required=True,
        help="OHDSI WebAPI base URL, e.g. https://atlas.ohdsi.org/WebAPI",
    )
    p.add(
        "--webapi-auth-login-path",
        env_var="WEBAPI_AUTH_LOGIN_PATH",
        required=False,
        help="Relative path to the WebAPI login provider, e.g. /user/login/db",
    )
    p.add(
        "--webapi-auth-username",
        env_var="WEBAPI_AUTH_USERNAME",
        required=False,
        help="Username to authenticate against the WebAPI with",
    )
    p.add(
        "--webapi-auth-password",
        env_var="WEBAPI_AUTH_PASSWORD",
        required=False,
        help="Password to authenticate against the WebAPI with",
    )
    p.add(
        "--dry-run",
        env_var="DRY_RUN",
        required=False,
        help="Dry run mode: clone repo, fetch cohorts, "
        + "and commit but don't push them to origin. Default: 'False'",
        default=False,
        action="store_true",
    )

    options = p.parse_args()

    logging.info(
        "Cloning repo '%s@%s' into '%s'",
        options.git_repo_url,
        options.git_branch,
        options.git_destination,
    )
    clone_repo(options.git_repo_url, options.git_branch, options.git_destination)

    s = requests.Session()

    if options.webapi_auth_login_path:
        logging.info(
            "WebAPI auth is enabled. Using login provider @ %s",
            options.webapi_auth_login_path,
        )
        auth_login_url = f"{options.webapi_url}{options.webapi_auth_login_path}"
        logging.info(
            "Fetching auth token as %s from %s",
            options.webapi_auth_username,
            auth_login_url,
        )
        auth_response = s.post(
            auth_login_url,
            data={
                "login": options.webapi_auth_username,
                "password": options.webapi_auth_password,
            },
        )
        auth_response.raise_for_status()
        auth_bearer_token = auth_response.headers["bearer"]
        s.headers.update({"Authorization": f"Bearer: {auth_bearer_token}"})

    logging.info("Fetching cohort definitions from WebAPI @ %s", options.webapi_url)
    cohorts = fetch_cohorts(s, options.webapi_url)
    logging.info("Retrieved a total of %d cohort(s)", len(cohorts))

    logging.info("Saving cohorts")
    write_cohorts(
        cohorts,
        options.git_destination,
        options.git_sub_path,
        options.cohort_file_prefix,
    )

    logging.info("Adding changes, commiting, and pushing to origin")
    add_commit_and_push(
        options.git_destination,
        options.git_commit_user_name,
        options.git_commit_email,
        options.dry_run,
    )

    logging.info("All done.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
    )
    main()
