"""AwsSsmStore -- push/pull secrets to AWS Systems Manager Parameter Store.

Requires ``boto3`` (install with ``pip install enveloper[aws]``).
"""

from __future__ import annotations

from typing import Any

from enveloper.store import SecretStore

_MISSING_BOTO3 = (
    "boto3 is required for the aws-ssm store. "
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

    Parameters are stored as ``{prefix}{key}`` using ``SecureString`` type
    by default.
    """

    def __init__(
        self,
        prefix: str = "/enveloper/",
        profile: str | None = None,
        region: str | None = None,
        secure: bool = True,
    ) -> None:
        if not prefix.endswith("/"):
            prefix += "/"
        self._prefix = prefix
        self._profile = profile
        self._region = region
        self._type = "SecureString" if secure else "String"
        self._client: Any = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _get_client(self._profile, self._region)
        return self._client

    def _param_name(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> str | None:
        try:
            resp = self.client.get_parameter(
                Name=self._param_name(key), WithDecryption=True
            )
            return resp["Parameter"]["Value"]
        except self.client.exceptions.ParameterNotFound:
            return None

    def set(self, key: str, value: str) -> None:
        self.client.put_parameter(
            Name=self._param_name(key),
            Value=value,
            Type=self._type,
            Overwrite=True,
        )

    def delete(self, key: str) -> None:
        try:
            self.client.delete_parameter(Name=self._param_name(key))
        except self.client.exceptions.ParameterNotFound:
            pass

    def list_keys(self) -> list[str]:
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
                    keys.append(name[len(self._prefix) :])
        return sorted(keys)

    def clear(self) -> None:
        for key in self.list_keys():
            self.delete(key)
