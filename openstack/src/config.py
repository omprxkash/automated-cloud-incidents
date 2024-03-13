from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Config:
    auth_url: str = ""
    project_name: str = ""
    username: str = ""
    password: str = ""
    region_name: str = "RegionOne"
    user_domain_name: str = "Default"
    project_domain_name: str = "Default"
    mock: bool = False
    clouds_yaml: Optional[Path] = None
    extra: dict = field(default_factory=dict)


def load_config(clouds_yaml_path: Optional[str] = None) -> Config:
    """Build a Config from environment variables, falling back to clouds.yaml."""
    mock_flag = os.environ.get("OPENSTACK_MOCK", "0").strip().lower() in ("1", "true", "yes")

    cfg = Config(
        auth_url=os.environ.get("OS_AUTH_URL", ""),
        project_name=os.environ.get("OS_PROJECT_NAME", ""),
        username=os.environ.get("OS_USERNAME", ""),
        password=os.environ.get("OS_PASSWORD", ""),
        region_name=os.environ.get("OS_REGION_NAME", "RegionOne"),
        user_domain_name=os.environ.get("OS_USER_DOMAIN_NAME", "Default"),
        project_domain_name=os.environ.get("OS_PROJECT_DOMAIN_NAME", "Default"),
        mock=mock_flag,
    )

    # If env vars are missing, try clouds.yaml
    if not cfg.auth_url and not mock_flag:
        clouds_path = Path(clouds_yaml_path or "clouds.yaml")
        if clouds_path.exists():
            cfg = _merge_clouds_yaml(cfg, clouds_path)

    return cfg


def _merge_clouds_yaml(cfg: Config, path: Path) -> Config:
    with open(path) as fh:
        data = yaml.safe_load(fh)

    clouds = data.get("clouds", {})
    if not clouds:
        return cfg

    cloud_name = os.environ.get("OS_CLOUD", next(iter(clouds)))
    cloud = clouds.get(cloud_name, {})
    auth = cloud.get("auth", {})

    cfg.auth_url = auth.get("auth_url", cfg.auth_url)
    cfg.project_name = auth.get("project_name", cfg.project_name)
    cfg.username = auth.get("username", cfg.username)
    cfg.password = auth.get("password", cfg.password)
    cfg.region_name = cloud.get("region_name", cfg.region_name)
    cfg.user_domain_name = auth.get("user_domain_name", cfg.user_domain_name)
    cfg.project_domain_name = auth.get("project_domain_name", cfg.project_domain_name)
    cfg.clouds_yaml = path
    return cfg
