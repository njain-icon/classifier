"""
This is entry point for Classifier(Classifier Server and Local UI)
"""

import argparse
import os
import warnings

from tqdm import tqdm

from classifier.app.config.config import (
    load_config,
    var_server_config,
    var_server_config_dict,
)
from importlib.metadata import PackageNotFoundError, version

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

def get_classifier_version():
    try:
        ver = version("classifier")
    except PackageNotFoundError:
        ver = "unknown"
    return ver

server_version = get_classifier_version()

def start():
    """Entry point for classifier-server."""

    # For loading config file details
    parser = argparse.ArgumentParser(description="Classifier  CLI")
    parser.add_argument("-c", "--config", type=str, help="config file path")
    parser.add_argument(
        "-v", "--version", action="store_true", help="display the version"
    )
    args = parser.parse_args()
    if args.version:
        print(f"Classifier Server version: {server_version}")
        exit(0)

    path = args.config
    if path is not None and not os.path.exists(path):
        raise FileNotFoundError(
            f"'--config' was passed but config file '{path}' does not exist."
        )

    config_details, server_config = load_config(path)
    p_bar = tqdm(range(10))
    var_server_config_dict.set(config_details)
    var_server_config.set(server_config)
    server_start(config_details, p_bar)


def classifier_init(p_bar):
    """Initialize topic and entity classifier."""
    p_bar.write("Downloading entity classifier models ...")
    from classifier.entity_classifier_2.entity_classifier import EntityClassifierV2

    # Init EntityClassifier(This step downloads all necessary training models)
    _ = EntityClassifierV2(countries=["US"])
    p_bar.write("Initializing entity classifier ... done")
    p_bar.update(1)


def server_start(config: dict, p_bar: tqdm):
    """Start server."""
    p_bar.write(f"Classifier server version {server_version} starting ...")

    # Initialize Topic and Entity Classifier
    classifier_init(p_bar)

    # Starting Uvicorn Service Using config details
    from classifier.app.config.service import Service

    p_bar.update(1)
    svc = Service(config_details=config)
    p_bar.update(2)
    p_bar.close()
    svc.start()
    print("Classifier server stopped. BYE!")


if __name__ == "__main__":
    start()
