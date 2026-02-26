"""AliyunSmStore -- push/pull secrets to Alibaba Cloud KMS Secrets Manager.

See: https://www.alibabacloud.com/help/en/kms/key-management-service/getting-started/getting-started-with-secrets-manager

Requires ``alibabacloud_kms20160120`` (install with ``pip install enveloper[alibaba]``).
Uses ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET, or config.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any

from enveloper.store import DEFAULT_NAMESPACE, SecretStore

_MISSING_ALIBABA = (
    "alibabacloud_kms20160120 is required for the aliyun store. "
    "Install it with: pip install enveloper[alibaba]"
)

# Alibaba secret name: 1-192 chars; allow alphanumeric, hyphen, underscore
_SECRET_NAME_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _sanitize_secret_name(key: str) -> str:
    """Replace invalid chars with underscore for Alibaba secret name."""
    return _SECRET_NAME_RE.sub("_", key).strip("_") or "key"


def _get_client(
    region_id: str = "cn-hangzhou",
    access_key_id: str | None = None,
    access_key_secret: str | None = None,
    endpoint: str | None = None,
) -> Any:
    try:
        from alibabacloud_kms20160120.client import Client  # type: ignore[import-untyped]
        from alibabacloud_tea_openapi import (
            models as open_api_models,  # type: ignore[import-untyped]
        )
    except ModuleNotFoundError:
        raise RuntimeError(_MISSING_ALIBABA) from None

    access_key_id = access_key_id or os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = access_key_secret or os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    if not access_key_id or not access_key_secret:
        raise RuntimeError(
            "Alibaba KMS store requires ALIBABA_CLOUD_ACCESS_KEY_ID and "
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET, or [enveloper.aliyun] access_key_* in config."
        )

    if endpoint is None:
        endpoint = f"kms.{region_id}.aliyuncs.com"

    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        endpoint=endpoint,
        region_id=region_id,
    )
    return Client(config)


class AliyunSmStore(SecretStore):
    """Read/write secrets as Alibaba Cloud KMS generic secrets.

    Each key is stored as a separate secret; secret name = prefix + sanitized key.
    Uses ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET, or
    [enveloper.aliyun] access_key_id / access_key_secret in config.
    """

    default_namespace: str = "_default_"

    @classmethod
    def build_default_prefix(cls, domain: str, project: str) -> str:
        """Default prefix: enveloper--{domain}--{project}-- (separator --)."""
        d = _sanitize_prefix_segment_aliyun(domain)
        p = _sanitize_prefix_segment_aliyun(project)
        return f"enveloper--{d}--{p}--"

    def __init__(
        self,
        prefix: str = "enveloper-",
        region_id: str = "cn-hangzhou",
        access_key_id: str | None = None,
        access_key_secret: str | None = None,
        endpoint: str | None = None,
    ) -> None:
        self._prefix = prefix.strip("_").rstrip("-")
        if self._prefix:
            self._prefix = self._prefix + "-"
        self._region_id = region_id
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret
        self._endpoint = endpoint
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _get_client(
                region_id=self._region_id,
                access_key_id=self._access_key_id,
                access_key_secret=self._access_key_secret,
                endpoint=self._endpoint,
            )
        return self._client

    def _secret_name(self, key: str) -> str:
        return self._prefix + _sanitize_secret_name(key)

    def get(self, key: str) -> str | None:
        try:
            from alibabacloud_kms20160120 import models  # type: ignore[import-untyped]
            req = models.GetSecretValueRequest(secret_name=self._secret_name(key))
            resp = self.client.get_secret_value(req)
            if resp.body and resp.body.secret_data:
                return resp.body.secret_data
            return None
        except Exception as e:
            if "SecretNotFound" in str(e) or "NotFound" in str(e) or "404" in str(e):
                return None
            raise

    def set(self, key: str, value: str) -> None:
        from alibabacloud_kms20160120 import models  # type: ignore[import-untyped]

        name = self._secret_name(key)
        try:
            req = models.CreateSecretRequest(
                secret_name=name,
                version_id="v1",
                secret_data=value,
                secret_data_type="text",
            )
            self.client.create_secret(req)
        except Exception as e:
            if "AlreadyExists" in str(e) or "already exist" in str(e).lower():
                # Add new version (version_id must be unique per put)
                put_req = models.PutSecretValueRequest(
                    secret_name=name,
                    version_id=f"v{int(time.time() * 1000)}",
                    secret_data=value,
                    secret_data_type="text",
                )
                self.client.put_secret_value(put_req)
            else:
                raise

    def delete(self, key: str) -> None:
        try:
            from alibabacloud_kms20160120 import models  # type: ignore[import-untyped]
            req = models.DeleteSecretRequest(secret_name=self._secret_name(key))
            self.client.delete_secret(req)
        except Exception as e:
            if "SecretNotFound" in str(e) or "NotFound" in str(e) or "404" in str(e):
                pass
            else:
                raise

    def list_keys(self) -> list[str]:
        from alibabacloud_kms20160120 import models  # type: ignore[import-untyped]

        keys: list[str] = []
        page = 1
        while True:
            req = models.ListSecretsRequest(page_number=page, page_size=100)
            resp = self.client.list_secrets(req)
            if not resp.body or not resp.body.secret_list:
                break
            for secret in resp.body.secret_list:
                name = getattr(secret, "secret_name", "") or ""
                if name.startswith(self._prefix):
                    key_suffix = name[len(self._prefix) :]
                    keys.append(key_suffix)
            if len(resp.body.secret_list) < 100:
                break
            page += 1
        return sorted(set(keys))

