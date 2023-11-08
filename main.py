import json
import requests
import argparse


def get_packages(token: str) -> list:
    """Gets a list of packages in the given repository from GitHub

    Args:
        owner (str): Name of the owner of the repo
        repository (str): Name of the repository
        token (str): PAT
    """
    response = requests.get(
        f"https://api.github.com/user/packages?package_type=container",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    data = response.json()
    return data


def filter_packages(owner: str, repository: str, data: list) -> list:
    """Filters out the packages that do not originate from the given repository

    Args:
        owner (str): Owner of the repository
        repository (str): Name of the repository
        data (list): List of packages

    Returns:
        list: List of packages that originate from the given repository
    """
    filtered_data = []
    for entry in data:
        if (
            entry["owner"]["login"] == owner
            and entry["repository"]["name"] == repository
        ):
            filtered_data.append(entry)
    return filtered_data


def get_versions_of_package(token: str, owner: str, package_name: str) -> list:
    url = f"https://api.github.com/users/{owner}/packages/container/{package_name}/versions"
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    data = response.json()
    with open(f"./temp_versions-{package_name}.json", "w") as file:
        json.dump(data, file, indent=4)
    return data


def filter_untagged_package_versions(data: list) -> list:
    """Filters out the untagged versions of a package

    Args:
        data (list): List of versions of a package

    Returns:
        list: List of untagged versions of a package
    """
    untagged_versions = []
    for version in data:
        if len(version["metadata"]["container"]["tags"]) == 0:
            untagged_versions.append(version)
    return untagged_versions


def delete_package_version(token: str, entry: dict) -> None:
    """Deletes the given package version

    Args:
        token (str): Access token
        entry (dict): Entry to delete

    Raises:
        Exception: If the delete request fails
    """
    url = entry["url"]
    response = requests.delete(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    if response.status_code != 204:
        raise Exception(f"Failed to delete {url}")


def parse_arguments() -> tuple:
    """Parses the arguments passed to the script

    Returns:
        tuple: Tuple containing the owner, repository and token
    """
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("--owner", required=True, help="Owner of the repository")
    parser.add_argument("--repository", required=True, help="Name of the repository")
    parser.add_argument("--token", required=True, help="GitHub token")

    args = parser.parse_args()
    return args.owner, args.repository, args.token


if __name__ == "__main__":
    owner, repository, token = parse_arguments()
    packages = get_packages(token)
    filtered_packages = filter_packages(owner, repository, packages)
    for package in filtered_packages:
        package_name = package["name"]
        versions = get_versions_of_package(token, owner, package_name)

        untagged_versions = filter_untagged_package_versions(versions)
        for version in untagged_versions:
            delete_package_version(token, version)
