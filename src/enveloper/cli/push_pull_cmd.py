"""``enveloper push`` and ``enveloper pull`` commands."""

from __future__ import annotations

import click

from enveloper.cli import (
    _get_keychain,
    _get_store,
    _make_cloud_store,
    cli,
    common_options,
    console,
    key_to_export_name,
    GitHubStore,
    KeychainStore,
)


@cli.command()
@click.option("--from", "from_service", default="local", help="Source service to push from (default: local).")
@click.option("--prefix", default=None, help="Key prefix for the target store.")
@click.option("--profile", default=None, help="AWS profile (aws store).")
@click.option("--region", default=None, help="AWS region (aws store).")
@click.option("--repo", default=None, help="GitHub repo owner/name (github store).")
@common_options
def push(
    ctx: click.Context,
    from_service: str,
    prefix: str | None,
    profile: str | None,
    region: str | None,
    repo: str | None,
) -> None:
    """Push secrets to a cloud store. Use global --service to specify the cloud store (e.g. --service aws)."""
    cloud_store = ctx.obj["service"]
    if cloud_store in ("local", "file"):
        raise click.UsageError("Push target must be a cloud store. Use --service aws, github, vault, gcp, azure, or aliyun.")
    domain = ctx.obj["domain_resolved"]
    cfg = ctx.obj["config"]
    env_name = ctx.obj["env_name"]
    path = ctx.obj.get("path", ".env")

    orig_service = ctx.obj["service"]
    ctx.obj["service"] = from_service
    ctx.obj["path"] = path
    try:
        source = _get_store(ctx)
    finally:
        ctx.obj["service"] = orig_service
    keys = source.list_keys()
    if not keys:
        console.print("[yellow]No secrets to push.[/yellow]")
        return

    target = _make_cloud_store(
        cloud_store, cfg, ctx.obj["project"], domain, env_name,
        prefix=prefix, profile=profile, region=region, repo=repo,
    )

    source_version = getattr(source, "_version", None) or ctx.obj.get("version") or "1.0.0"
    project = ctx.obj["project"] or "_default_"
    domain = ctx.obj["domain_resolved"]

    count = 0
    for key in keys:
        val = source.get(key)
        if val is not None:
            name = key_to_export_name(source, key)
            if isinstance(target, GitHubStore):
                target.set(name, val)
                if ctx.obj["verbose"]:
                    console.print(f"  {name}")
            else:
                target_key = target.build_key(name=name, project=project, domain=domain, version=source_version)
                target.set(target_key, val)
                if ctx.obj["verbose"]:
                    console.print(f"  {target_key}")
            count += 1

    console.print(f"[green]Pushed {count} secret(s) to {cloud_store}[/green]")


@cli.command()
@click.option("--to", "to_service", default="local", help="Target service to pull into (default: local).")
@click.option("--prefix", default=None, help="Key prefix on the source store.")
@click.option("--profile", default=None, help="AWS profile (aws store).")
@click.option("--region", default=None, help="AWS region (aws store).")
@common_options
def pull(
    ctx: click.Context,
    to_service: str,
    prefix: str | None,
    profile: str | None,
    region: str | None,
) -> None:
    """Pull secrets from a cloud store. Use global --service to specify the cloud store (e.g. --service aws)."""
    cloud_store = ctx.obj["service"]
    if cloud_store in ("local", "file"):
        raise click.UsageError("Pull source must be a cloud store. Use --service aws, vault, gcp, azure, or aliyun.")
    domain = ctx.obj["domain_resolved"]
    cfg = ctx.obj["config"]
    env_name = ctx.obj["env_name"]
    path = ctx.obj.get("path", ".env")
    source = _make_cloud_store(
        cloud_store, cfg, ctx.obj["project"], domain, env_name,
        prefix=prefix, profile=profile, region=region,
    )

    keys = source.list_keys()
    if not keys:
        console.print("[yellow]No secrets found in remote store.[/yellow]")
        return

    orig_service = ctx.obj["service"]
    ctx.obj["service"] = to_service
    ctx.obj["path"] = path
    try:
        target = _get_store(ctx)
    finally:
        ctx.obj["service"] = orig_service
    count = 0
    for key in keys:
        val = source.get(key)
        if val is not None:
            local_key = key_to_export_name(source, key)
            if isinstance(target, KeychainStore):
                target.set_with_domain_tracking(local_key, val)
            else:
                target.set(local_key, val)
            count += 1
            if ctx.obj["verbose"]:
                console.print(f"  {local_key}")

    console.print(f"[green]Pulled {count} secret(s) from {cloud_store}[/green]")
