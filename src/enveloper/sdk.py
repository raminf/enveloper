"""SDK for loading keychain secrets into the environment (python-dotenv style)."""

from __future__ import annotations

import os

from enveloper.config import EnveloperConfig, load_config
from enveloper.resolve_store import get_store
from enveloper.stores.keychain import KeychainStore
from enveloper.util import strip_domain_prefix


def _resolve_project_domain(
    project: str | None,
    domain: str | None,
) -> tuple[str, str]:
    """Resolve project and domain from args, env, and config (same as CLI)."""
    cfg = load_config()
    resolved_project = (
        project or os.environ.get("ENVELOPER_PROJECT") or cfg.project
    )
    resolved_domain = (
        domain or os.environ.get("ENVELOPER_DOMAIN") or "_default_"
    )
    return resolved_project, resolved_domain


def _resolve_service(service: str | None) -> str:
    """Resolve service from args, env, and config (same as CLI)."""
    if service:
        return service
    cfg = load_config()
    return os.environ.get("ENVELOPER_SERVICE") or cfg.service or "local"


def _should_use_ssm() -> bool:
    """Use SSM when aws extra is installed and we're in Lambda or ENVELOPER_USE_SSM is set."""
    if os.environ.get("ENVELOPER_USE_SSM"):
        return True
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return True
    return False


def _get_ssm_prefix(domain: str, cfg: EnveloperConfig) -> str | None:
    """Resolve SSM prefix from config or ENVELOPER_SSM_PREFIX."""
    prefix = os.environ.get("ENVELOPER_SSM_PREFIX")
    if prefix:
        return prefix if prefix.endswith("/") else f"{prefix}/"
    env_name = os.environ.get("ENVELOPER_ENV") or os.environ.get("STILLUP_ENV_NAME")
    return cfg.resolve_ssm_prefix(domain, env_name)


def _load_from_ssm(domain: str, cfg: EnveloperConfig) -> dict[str, str]:
    """Load secrets from SSM when boto3 is available. Returns empty dict if not used or on error."""
    if not _should_use_ssm():
        return {}
    try:
        from enveloper.stores.aws_ssm import AwsSsmStore
    except ImportError:
        return {}
    prefix = _get_ssm_prefix(domain, cfg)
    if not prefix:
        return {}
    if not prefix.endswith("/"):
        prefix = f"{prefix}/"
    try:
        store = AwsSsmStore(
            prefix=prefix,
            profile=cfg.aws_profile if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME") else None,
            region=cfg.aws_region or os.environ.get("AWS_REGION"),
        )
        keys = store.list_keys()
        result: dict[str, str] = {}
        for key in keys:
            value = store.get(key)
            if value is not None:
                result[key] = value
        return result
    except Exception:
        return {}


def _collect_secrets(
    project: str,
    domain: str,
    include_os_environ: bool = False,
    service: str = "local",
    path: str = ".env",
    env_name: str | None = None,
) -> dict[str, str]:
    """Build merged secrets from the given service, or (when service=local) SSM then keychain then optionally os.environ."""
    cfg = load_config()
    merged: dict[str, str] = {}

    if service != "local":
        # Single store: file or cloud
        store = get_store(service, project, domain, cfg, path=path, env_name=env_name)
        strip_prefix = service not in ("file",)  # strip domain/project when loading from cloud
        for key in store.list_keys():
            value = store.get(key)
            if value is not None:
                out_key = strip_domain_prefix(key) if strip_prefix else key
                merged[out_key] = value
        if include_os_environ:
            for k, v in os.environ.items():
                if k not in merged and v is not None:
                    merged[k] = v
        return merged

    # service == "local": SSM (if Lambda/ENVELOPER_USE_SSM) then keychain then optionally os.environ
    ssm_values = _load_from_ssm(domain, cfg)
    merged.update(ssm_values)

    store = KeychainStore(project=project, domain=domain)
    for key in store.list_keys():
        if key not in merged:
            value = store.get(key)
            if value is not None:
                merged[key] = value

    if include_os_environ:
        for key, value in os.environ.items():
            if key not in merged and value is not None:
                merged[key] = value

    return merged


def load_dotenv(
    project: str | None = None,
    domain: str | None = None,
    override: bool = True,
    verbose: bool = False,
    service: str | None = None,
    path: str = ".env",
    env_name: str | None = None,
) -> bool:
    """Load secrets into os.environ (python-dotenv compatible API).

    Uses the same project/domain/service resolution as the CLI: optional
    arguments, then ENVELOPER_PROJECT / ENVELOPER_DOMAIN / ENVELOPER_SERVICE,
    then config (e.g. .enveloper.toml), and defaults project ``"_default_"``,
    service ``"local"``.

    Parameters
    ----------
    project : str, optional
        Project namespace. Defaults from ENVELOPER_PROJECT or config.
    domain : str, optional
        Domain / subsystem scope. Defaults from ENVELOPER_DOMAIN, then ``"_default_"``.
    override : bool, default True
        If True, overwrite existing keys in os.environ. If False, only set
        keys that are not already set (matches python-dotenv semantics).
    verbose : bool, default False
        If True, no-op for now; reserved for future warnings (e.g. missing domain).
    service : str, optional
        Backend to load from: ``"local"`` (keychain), ``"file"`` (.env file), or a
        cloud store name (e.g. ``"aws"``). Defaults from ENVELOPER_SERVICE or
        config, else ``"local"``.
    path : str, default ".env"
        Path to the .env file when ``service="file"``. Ignored otherwise.
    env_name : str, optional
        Environment name for resolving ``{env}`` in config (e.g. domain ssm_prefix).

    Returns
    -------
    bool
        True if at least one variable was set, False otherwise.

    Examples
    --------
    >>> from enveloper import load_dotenv
    >>> load_dotenv()  # use ENVELOPER_* or config defaults (keychain)
    True
    >>> load_dotenv(project="myapp", domain="aws")
    True
    >>> load_dotenv(service="file", path=".env.local")  # load from file
    True
    >>> load_dotenv(override=False)  # do not overwrite existing env vars
    False

    When ``service="local"`` (default) and ``enveloper[aws]`` is installed and the
    code runs in AWS Lambda (or ``ENVELOPER_USE_SSM=1`` is set), values are loaded
    from SSM Parameter Store first, then keychain. Set ``ENVELOPER_SSM_PREFIX``
    (e.g. ``/myapp/prod/``) when not using ``.enveloper.toml``.
    """
    resolved_project, resolved_domain = _resolve_project_domain(project, domain)
    resolved_service = _resolve_service(service)
    merged = _collect_secrets(
        resolved_project, resolved_domain,
        include_os_environ=False,
        service=resolved_service, path=path, env_name=env_name,
    )
    if not merged:
        if verbose:
            pass  # could log "No secrets found for project X, domain Y"
        return False
    count = 0
    for key, value in merged.items():
        if key in os.environ and not override:
            continue
        os.environ[key] = value
        count += 1
    return count > 0


def dotenv_values(
    project: str | None = None,
    domain: str | None = None,
    service: str | None = None,
    path: str = ".env",
    env_name: str | None = None,
) -> dict[str, str]:
    """Return secrets as a dict without modifying os.environ.

    Same project/domain/service resolution as load_dotenv. Useful when you want to
    inspect or merge secrets yourself instead of loading into the process
    environment.

    Parameters
    ----------
    project : str, optional
        Project namespace. Defaults from ENVELOPER_PROJECT or config.
    domain : str, optional
        Domain / subsystem scope. Defaults from ENVELOPER_DOMAIN, then ``"_default_"``.
    service : str, optional
        Backend to load from. Defaults from ENVELOPER_SERVICE or config, else ``"local"``.
    path : str, default ".env"
        Path to the .env file when ``service="file"``. Ignored otherwise.
    env_name : str, optional
        Environment name for resolving ``{env}`` in config.

    Returns
    -------
    dict[str, str]
        Mapping of variable name to value. When ``service="local"`` and
        ``enveloper[aws]`` is installed and in Lambda or ``ENVELOPER_USE_SSM`` is set,
        values come from SSM first, then keychain, then existing environment as fallback.
    """
    resolved_project, resolved_domain = _resolve_project_domain(project, domain)
    resolved_service = _resolve_service(service)
    include_env = _should_use_ssm() if resolved_service == "local" else False
    return _collect_secrets(
        resolved_project, resolved_domain,
        include_os_environ=include_env,
        service=resolved_service, path=path, env_name=env_name,
    )
