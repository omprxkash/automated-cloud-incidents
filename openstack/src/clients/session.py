from __future__ import annotations

import os
from typing import Union

from src.config import load_config
from src.mock.mock_cloud import MockCloud


def get_connection(mock: bool = False) -> Union[MockCloud, "openstack.connection.Connection"]:
    """Return a connection object — either MockCloud or a real SDK connection.

    Pass mock=True, or set OPENSTACK_MOCK=1 in the environment, to run entirely
    offline without touching a real cloud.
    """
    cfg = load_config()

    if mock or cfg.mock or os.environ.get("OPENSTACK_MOCK", "0").strip() in ("1", "true", "yes"):
        return MockCloud()

    try:
        import openstack  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "openstacksdk is not installed. Run: pip install openstacksdk"
        ) from exc

    if cfg.clouds_yaml:
        return openstack.connect(cloud=os.environ.get("OS_CLOUD", ""))

    return openstack.connect(
        auth_url=cfg.auth_url,
        project_name=cfg.project_name,
        username=cfg.username,
        password=cfg.password,
        region_name=cfg.region_name,
        user_domain_name=cfg.user_domain_name,
        project_domain_name=cfg.project_domain_name,
        identity_api_version=3,
    )
