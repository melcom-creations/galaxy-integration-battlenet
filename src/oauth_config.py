from __future__ import annotations

import base64
import binascii
import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from windows_dpapi import DpapiError, protect_current_user, unprotect_current_user


SCHEMA_VERSION = 1
PROVIDER = "battle.net"
PLUGIN_GUID = "ba170431-0649-482f-863b-d248592f1842"
WINDOWS_PROTECTION = "windows-dpapi-current-user"
LOCAL_PROTECTION = "local-user-file"
CONFIG_RELATIVE_PATH = Path(
    "melcom-creations",
    "GOG Galaxy Integrations",
    "Battle.net",
    "oauth.json",
)


class OAuthConfigError(ValueError):
    pass


@dataclass(frozen=True)
class OAuthCredentials:
    client_id: str
    client_secret: str = field(repr=False)


def config_file_path(local_app_data: str | os.PathLike[str] | None = None) -> Path:
    if local_app_data is not None:
        root = Path(local_app_data)
    elif sys.platform == "win32":
        value = os.environ.get("LOCALAPPDATA")
        if not value:
            raise OAuthConfigError("LOCALAPPDATA is unavailable")
        root = Path(value)
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / CONFIG_RELATIVE_PATH


def validate_credentials(client_id, client_secret) -> OAuthCredentials:
    return OAuthCredentials(
        _validate_credential(client_id, "Client ID"),
        _validate_credential(client_secret, "Client Secret"),
    )


def _validate_credential(value, field_name: str) -> str:
    if not isinstance(value, str):
        raise OAuthConfigError(f"{field_name} is invalid")
    value = value.strip()
    if not 8 <= len(value) <= 256:
        raise OAuthConfigError(f"{field_name} must contain between 8 and 256 characters")
    if any(character.isspace() or ord(character) < 33 or ord(character) > 126 for character in value):
        raise OAuthConfigError(f"{field_name} contains unsupported characters")
    return value


def read_oauth_config(path: Path | None = None) -> OAuthCredentials | None:
    target = path or config_file_path()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OAuthConfigError("OAuth configuration file cannot be read") from error

    if not isinstance(payload, dict):
        raise OAuthConfigError("OAuth configuration root is invalid")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise OAuthConfigError("OAuth configuration schema is invalid")
    if payload.get("provider") != PROVIDER:
        raise OAuthConfigError("OAuth configuration provider is invalid")
    if payload.get("plugin_guid") != PLUGIN_GUID:
        raise OAuthConfigError("OAuth configuration plugin GUID is invalid")
    if payload.get("status") == "setup-required":
        return None

    protection = payload.get("protection")
    try:
        if protection == WINDOWS_PROTECTION:
            protected_value = payload.get("protected_credentials")
            if not isinstance(protected_value, str) or not protected_value:
                raise OAuthConfigError("Protected OAuth credentials are invalid")
            protected = base64.b64decode(protected_value, validate=True)
            serialized = unprotect_current_user(protected).decode("utf-8")
            credentials = json.loads(serialized)
        elif protection == LOCAL_PROTECTION and sys.platform != "win32":
            credentials = payload.get("credentials")
        else:
            raise OAuthConfigError("OAuth configuration protection is invalid")
    except (binascii.Error, UnicodeError, json.JSONDecodeError, DpapiError, ValueError) as error:
        if isinstance(error, OAuthConfigError):
            raise
        raise OAuthConfigError("OAuth credentials cannot be decrypted") from error

    if not isinstance(credentials, dict):
        raise OAuthConfigError("OAuth credentials are invalid")
    return validate_credentials(
        credentials.get("client_id"),
        credentials.get("client_secret"),
    )


def prepare_oauth_config(path: Path | None = None) -> Path:
    target = path or config_file_path()
    if target.is_file():
        return target
    payload = {
        "schema_version": SCHEMA_VERSION,
        "provider": PROVIDER,
        "plugin_guid": PLUGIN_GUID,
        "status": "setup-required",
    }
    _write_payload(payload, target)
    return target


def write_oauth_config(
    credentials: OAuthCredentials,
    *,
    path: Path | None = None,
) -> Path:
    credentials = validate_credentials(credentials.client_id, credentials.client_secret)
    target = path or config_file_path()

    credential_payload = {
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
    }
    if sys.platform == "win32":
        try:
            serialized_credentials = json.dumps(
                credential_payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            protected = protect_current_user(serialized_credentials)
        except (DpapiError, ValueError) as error:
            raise OAuthConfigError("OAuth credential protection failed") from error
        payload = {
            "schema_version": SCHEMA_VERSION,
            "provider": PROVIDER,
            "plugin_guid": PLUGIN_GUID,
            "protection": WINDOWS_PROTECTION,
            "protected_credentials": base64.b64encode(protected).decode("ascii"),
        }
    else:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "provider": PROVIDER,
            "plugin_guid": PLUGIN_GUID,
            "protection": LOCAL_PROTECTION,
            "credentials": credential_payload,
        }

    _write_payload(payload, target)
    return target


def _write_payload(payload: dict, target: Path) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temporary_path = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=".oauth-",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, target)
        if sys.platform != "win32":
            target.chmod(0o600)
    except OSError as error:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise OAuthConfigError("OAuth configuration file could not be written") from error
