# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

"""AwsSsmStore -- push/pull secrets to AWS Systems Manager Parameter Store.

Requires ``boto3`` (install with ``pip install enveloper[aws]``).
"""

from __future__ import annotations

from typing import Any

from enveloper.store import DEFAULT_NAMESPACE, DEFAULT_PREFIX, DEFAULT_VERSION, SecretStore, is_valid_semver

_MISSING_BOTO3 = (
    "boto3 is required for the aws store. "
    "Install it with: pip install enveloper[aws]"
)


def _get_client(profile: str | None = None, region: str | None = None) -> Any:
    try:
        import boto3  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        raise RuntimeError(_MISSING_BOTO3) from None

    session_kwargs: dict[str, str] = {}
    if profile:
        session_kwargs["profile_name"] = profile
    if region:
        session_kwargs["region_name"] = region
    session = boto3.Session(**session_kwargs)
    return session.client("ssm")


class AwsSsmStore(SecretStore):
    """Read/write secrets as SSM parameters under a path prefix.

    Parameters are stored as ``/envr/{domain}/{project}/{version}/{key}`` using ``SecureString``
    type by default. The leading ``/`` is added by the store (service-specific separator).
    """

    service_name: str = "aws"
    service_display_name: str = "AWS Systems Manager Parameter Store"
    service_doc_url: str = "https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html"

    default_namespace: str = "_default_"
    key_separator: str = "/"
    prefix: str = DEFAULT_PREFIX

    @classmethod
    def build_default_prefix(cls, domain: str, project: str) -> str:
        """Default SSM path: /envr/{domain}/{project}/ (path separator /). Service prepends /."""
        d = cls.sanitize_key_segment(domain)
        p = cls.sanitize_key_segment(project)
        return f"/{cls.prefix}/{d}/{p}/"

    def __init__(
        self,
        prefix: str = "/envr/",
        profile: str | None = None,
        region: str | None = None,
        secure: bool = True,
        version: str = DEFAULT_VERSION,
        domain: str = DEFAULT_NAMESPACE,
        project: str = DEFAULT_NAMESPACE,
        **kwargs: object,
    ) -> None:
        if not prefix.endswith("/"):
            prefix += "/"
        self._prefix = prefix
        self._profile = profile
        self._region = region
        self._type = "SecureString" if secure else "String"
        self._version = version
        self._domain = domain
        self._project = project
        # Validate version format
        if not is_valid_semver(version):
            raise ValueError(f"Invalid version format: {version}. Must be valid semver (e.g., 1.0.0)")
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _get_client(self._profile, self._region)
        return self._client

    def _resolve_key(self, key: str) -> str:
        """Return full composite key; if key is short name, build full key with domain/project/version."""
        if self.parse_key(key) is not None:
            return key
        return self.build_key(
            name=key, project=self._project, domain=self._domain, version=self._version
        )

    def _param_name(self, key: str) -> str:
        full_key = self._resolve_key(key)
        # SSM parameter names start with / ; prepend if not present
        if full_key.startswith(self.key_separator):
            return full_key
        return self.key_separator + full_key

    def get(self, key: str) -> str | None:
        param_name = self._param_name(key)
        try:
            resp = self.client.get_parameter(
                Name=param_name, WithDecryption=True
            )
            return resp["Parameter"]["Value"]
        except self.client.exceptions.ParameterNotFound:
            return None

    def set(self, key: str, value: str) -> None:
        param_name = self._param_name(key)
        self.client.put_parameter(
            Name=param_name,
            Value=value,
            Type=self._type,
            Overwrite=True,
        )

    def delete(self, key: str) -> None:
        param_name = self._param_name(key)
        try:
            self.client.delete_parameter(Name=param_name)
        except self.client.exceptions.ParameterNotFound:
            pass

    def list_keys(self) -> list[str]:
        """Return full composite keys (e.g. /envr/domain/proj/1.0.0/API_KEY) so get(key) works."""
        keys: list[str] = []
        paginator = self.client.get_paginator("describe_parameters")
        for page in paginator.paginate(
            ParameterFilters=[
                {"Key": "Path", "Option": "Recursive", "Values": [self._prefix.rstrip("/")]}
            ]
        ):
            for param in page.get("Parameters", []):
                name: str = param["Name"]
                if name.startswith(self._prefix):
                    # Return full parameter name as the key (get() expects this)
                    keys.append(name)
        return sorted(set(keys))
