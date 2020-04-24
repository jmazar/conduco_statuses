import subprocess
import conducto as co


def run(branch: str) -> co.Serial:
    image = co.Image(image="python:3.6", reqs_py=["conducto"])
    root = co.Serial(image=image)
    with co.Serial(same_container=co.SameContainer.NEW, cpu=12,
                   mem=32) as build:
        build["fetch"] = co.Exec("echo im fetching")
        build["checkout"] = co.Exec("echo im checking out")
        with co.Parallel(name="checks") as checks:
            checks["yapf"] = co.Exec("echo checking yapf")
            checks["python_tests"] = co.Exec(
                "echo checking python tests")
            checks["flake8"] = co.Exec(
                "echo checking flake8")
            checks["pylint"] = co.Exec(
                "echo im checking pylint")
            checks["mypy"] = co.Exec("echo im checking mypy")
            checks["cppcheck"] = co.Exec(
                "echo im checking cppcheck")
            checks["clang_format"] = co.Exec(
                "echo im checking clang_format")

        build["build"] = co.Exec('echo im building now')

    root["build"] = build

    auth_token = co.api.Auth().get_token_from_shell()
    access_token = co.api.Secrets().get_user_secrets(
        auth_token)["GITHUB_ACCESS_TOKEN"]
    stdout = subprocess.check_output(
        f"git ls-remote git@github.com:jmazar/conduco_statuses.git refs/heads/{branch} | cut -f1",
        shell=True)
    sha = stdout.decode("utf-8").strip()
    print(sha)
    print(access_token)
    creator = co.callback.github_status_creator(
        owner="jmazar",
        repo="https://github.com/jmazar/conducto_statuses",
        sha=sha,
        access_token=access_token,
    )

    for node in root.stream():
        if isinstance(node, co.Exec):
            node.on_queued(creator(state="pending"))
            node.on_done(creator(state="success"))
            node.on_error(creator(state="failure"))
    return root


if __name__ == "__main__":
    co.main(default=run)
