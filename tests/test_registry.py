"""Tests for the metadata registry (compress, register/unregister, rebuild, clear_metadata)."""

from __future__ import annotations

import json

from enveloper.store import SecretStore


class InMemoryStore(SecretStore):
    """Minimal in-memory store for testing base-class registry methods."""

    service_name = "mem"
    service_display_name = "In-Memory Test Store"
    service_doc_url = ""
    key_separator = "--"
    prefix = "envr"

    def __init__(self, domain: str = "_default_", project: str = "_default_") -> None:
        self._data: dict[str, str] = {}
        self._domain = domain
        self._project = project

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def list_keys(self) -> list[str]:
        return sorted(
            k for k in self._data
            if not k.startswith("_envr_meta_")
        )


# ---------------------------------------------------------------------------
# Compression round-trip
# ---------------------------------------------------------------------------

def test_compress_decompress_roundtrip():
    original = '["dev", "staging", "prod"]'
    compressed = SecretStore._compress(original)
    assert compressed != original
    assert SecretStore._decompress(compressed) == original


def test_compress_empty_list():
    data = "[]"
    assert SecretStore._decompress(SecretStore._compress(data)) == data


# ---------------------------------------------------------------------------
# register / unregister domain
# ---------------------------------------------------------------------------

def test_register_domain_creates_metadata():
    s = InMemoryStore()
    s.register_domain("dev")
    raw = s._raw_get(s._META_DOMAINS_KEY)
    assert raw is not None
    domains = json.loads(s._decompress(raw))
    assert "dev" in domains


def test_register_domain_idempotent():
    s = InMemoryStore()
    s.register_domain("dev")
    s.register_domain("dev")
    domains = s._read_meta_list(s._META_DOMAINS_KEY)
    assert domains.count("dev") == 1


def test_unregister_domain_removes():
    s = InMemoryStore()
    s.register_domain("dev")
    s.register_domain("staging")
    s.unregister_domain("dev")
    domains = s._read_meta_list(s._META_DOMAINS_KEY)
    assert "dev" not in domains
    assert "staging" in domains


def test_unregister_last_domain_deletes_key():
    s = InMemoryStore()
    s.register_domain("dev")
    s.unregister_domain("dev")
    assert s._raw_get(s._META_DOMAINS_KEY) is None


def test_unregister_domain_also_removes_projects_key():
    s = InMemoryStore()
    s.register_domain("dev")
    s.register_project("dev", "MyProject")
    s.unregister_domain("dev")
    assert s._raw_get(s._meta_projects_key("dev")) is None


# ---------------------------------------------------------------------------
# register / unregister project
# ---------------------------------------------------------------------------

def test_register_project_creates_metadata():
    s = InMemoryStore()
    s.register_project("dev", "Proj1")
    projects = s._read_meta_list(s._meta_projects_key("dev"))
    assert "Proj1" in projects


def test_register_project_idempotent():
    s = InMemoryStore()
    s.register_project("dev", "Proj1")
    s.register_project("dev", "Proj1")
    projects = s._read_meta_list(s._meta_projects_key("dev"))
    assert projects.count("Proj1") == 1


def test_unregister_project_removes():
    s = InMemoryStore()
    s.register_project("dev", "Proj1")
    s.register_project("dev", "Proj2")
    s.unregister_project("dev", "Proj1")
    projects = s._read_meta_list(s._meta_projects_key("dev"))
    assert "Proj1" not in projects
    assert "Proj2" in projects


def test_unregister_last_project_also_removes_domain():
    s = InMemoryStore()
    s.register_domain("dev")
    s.register_project("dev", "only")
    s.unregister_project("dev", "only")
    assert s._raw_get(s._meta_projects_key("dev")) is None
    domains = s._read_meta_list(s._META_DOMAINS_KEY)
    assert "dev" not in domains


# ---------------------------------------------------------------------------
# set_with_tracking / delete_with_tracking
# ---------------------------------------------------------------------------

def test_set_with_tracking_registers_domain_and_project():
    s = InMemoryStore(domain="dev", project="WebApp")
    key = s.build_key("API_KEY", "dev", "WebApp")
    s.set_with_tracking(key, "secret123")
    assert s.get(key) == "secret123"
    assert "dev" in s._read_meta_list(s._META_DOMAINS_KEY)
    assert "WebApp" in s._read_meta_list(s._meta_projects_key("dev"))


def test_delete_with_tracking_unregisters_empty_project():
    s = InMemoryStore(domain="dev", project="WebApp")
    key = s.build_key("ONLY_KEY", "dev", "WebApp")
    s.set_with_tracking(key, "val")
    s.delete_with_tracking(key)
    assert s.get(key) is None
    projects = s._read_meta_list(s._meta_projects_key("dev"))
    assert "WebApp" not in projects


def test_delete_with_tracking_keeps_project_if_keys_remain():
    s = InMemoryStore(domain="dev", project="WebApp")
    k1 = s.build_key("K1", "dev", "WebApp")
    k2 = s.build_key("K2", "dev", "WebApp")
    s.set_with_tracking(k1, "v1")
    s.set_with_tracking(k2, "v2")
    s.delete_with_tracking(k1)
    projects = s._read_meta_list(s._meta_projects_key("dev"))
    assert "WebApp" in projects


# ---------------------------------------------------------------------------
# list_domains / list_projects (metadata-backed)
# ---------------------------------------------------------------------------

def test_list_domains_reads_from_metadata():
    s = InMemoryStore()
    s.register_domain("dev")
    s.register_domain("prod")
    assert s.list_domains() == ["dev", "prod"]


def test_list_domains_fallback_scans_keys():
    s = InMemoryStore(domain="staging", project="X")
    key = s.build_key("K", "staging", "X")
    s.set(key, "v")
    domains = s.list_domains()
    assert "staging" in domains


def test_list_projects_reads_from_metadata():
    s = InMemoryStore()
    s.register_project("dev", "P1")
    s.register_project("dev", "P2")
    assert s.list_projects("dev") == ["P1", "P2"]


def test_list_projects_fallback_scans_keys():
    s = InMemoryStore(domain="dev", project="WebApp")
    key = s.build_key("K", "dev", "WebApp")
    s.set(key, "v")
    projects = s.list_projects("dev")
    assert "WebApp" in projects


# ---------------------------------------------------------------------------
# rebuild_registry
# ---------------------------------------------------------------------------

def test_rebuild_registry_from_keys():
    s = InMemoryStore()
    s.set(s.build_key("K1", "dev", "P1"), "v")
    s.set(s.build_key("K2", "dev", "P2"), "v")
    s.set(s.build_key("K3", "staging", "P1"), "v")
    result = s.rebuild_registry()
    assert sorted(result.keys()) == ["dev", "staging"]
    assert sorted(result["dev"]) == ["P1", "P2"]
    assert result["staging"] == ["P1"]
    assert s.list_domains() == ["dev", "staging"]
    assert s.list_projects("dev") == ["P1", "P2"]


def test_rebuild_registry_overwrites_stale_metadata():
    s = InMemoryStore()
    s.register_domain("stale_domain")
    s.register_project("stale_domain", "stale_project")
    s.set(s.build_key("K", "real", "RP"), "v")
    result = s.rebuild_registry()
    assert "stale_domain" not in result
    assert "real" in result
    assert s.list_domains() == ["real"]


# ---------------------------------------------------------------------------
# clear_metadata
# ---------------------------------------------------------------------------

def test_clear_metadata_removes_all():
    s = InMemoryStore()
    s.register_domain("dev")
    s.register_domain("prod")
    s.register_project("dev", "P1")
    s.register_project("prod", "P2")
    s.clear_metadata()
    assert s._raw_get(s._META_DOMAINS_KEY) is None
    assert s._raw_get(s._meta_projects_key("dev")) is None
    assert s._raw_get(s._meta_projects_key("prod")) is None


def test_clear_metadata_on_empty_store():
    s = InMemoryStore()
    s.clear_metadata()


# ---------------------------------------------------------------------------
# meta_projects_key naming
# ---------------------------------------------------------------------------

def test_meta_projects_key_format():
    assert SecretStore._meta_projects_key("dev") == "_envr_meta_dom_dev_projects_"
    assert SecretStore._meta_projects_key("staging") == "_envr_meta_dom_staging_projects_"
