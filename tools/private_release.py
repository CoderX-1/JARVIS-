"""Build and unpack a private JARVIS Windows release.

Only source/model files are plaintext in the ZIP. The environment and local
configuration are AES-256-GCM encrypted with a passphrase-derived key. The ZIP
must never be committed or published: installed applications expose API keys to
the local machine's owner, regardless of transport encryption. The explicit
passwordless-install option embeds the unlock passphrase in the ZIP; anyone who
gets that ZIP can recover the environment and API keys.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import os
import secrets
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


AAD = b"JARVIS private release v1"
ITERATIONS = 600_000
MAX_FILE = 3_000_000_000
MAX_TOTAL = 7_000_000_000
PRODUCTION_ROOTS = {"core", "desktop", "components", "docs", "tools", "config"}
TOP_FILES = {"RUN-JARVIS.ps1", "START-JARVIS-DESKTOP.bat", "README.md"}
PASSPHRASE_MEMBER = "private/install-passphrase.txt"


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value, validate=True)


def encrypt_private(data: bytes, passphrase: str) -> dict[str, str | int]:
    if len(passphrase) < 16:
        raise ValueError("Use a release passphrase of at least 16 characters")
    salt, nonce = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, ITERATIONS, 32)
    return {"format": 1, "kdf": "pbkdf2-sha256", "iterations": ITERATIONS,
            "salt": _b64(salt), "nonce": _b64(nonce),
            "ciphertext": _b64(AESGCM(key).encrypt(nonce, data, AAD))}


def decrypt_private(envelope: dict, passphrase: str) -> bytes:
    if (envelope.get("format") != 1 or envelope.get("kdf") != "pbkdf2-sha256" or
            envelope.get("iterations") != ITERATIONS):
        raise ValueError("Unsupported private release encryption format")
    salt, nonce, ciphertext = (_unb64(envelope[key]) for key in ("salt", "nonce", "ciphertext"))
    if len(salt) != 16 or len(nonce) != 12 or len(ciphertext) > 1_000_000:
        raise ValueError("Invalid encrypted payload")
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, ITERATIONS, 32)
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, AAD)
    except Exception as exc:
        raise ValueError("Wrong passphrase or damaged private release") from exc


def _source_files(source: Path) -> list[tuple[Path, str]]:
    result = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"],
                            cwd=source, capture_output=True, check=True)
    selected: list[tuple[Path, str]] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        name = os.fsdecode(raw)
        rel = PurePosixPath(name.replace("\\", "/"))
        if (rel.is_absolute() or ".." in rel.parts or not rel.parts or
                (rel.parts[0] not in PRODUCTION_ROOTS and rel.as_posix() not in TOP_FILES) or
                "tests" in rel.parts or "__pycache__" in rel.parts or
                rel.suffix in {".pyc", ".log"} or
                (rel.parts[0] == "config" and rel.suffix == ".json" and
                 not rel.name.endswith(".example.json"))):
            continue
        path = source.joinpath(*rel.parts)
        if path.is_file() and not path.is_symlink():
            selected.append((path, "app/" + rel.as_posix()))
    return selected


def _model_files(models: Path) -> list[tuple[Path, str]]:
    if not models.is_dir():
        raise ValueError("Local models directory is missing")
    selected = []
    for path in models.rglob("*"):
        if path.is_symlink():
            raise ValueError("Model symlinks are not allowed in a private release")
        if path.is_file():
            rel = path.relative_to(models).as_posix()
            selected.append((path, "app/models/" + rel))
    if not selected:
        raise ValueError("Local models directory is empty")
    return selected


def build(source: Path, env_file: Path, config_dir: Path, models: Path,
          output: Path, passphrase: str, *, embed_passphrase: bool = False) -> dict:
    source, env_file, config_dir, models, output = (
        item.resolve(strict=False) for item in (source, env_file, config_dir, models, output))
    if output.exists() or not output.parent.is_dir() or output.suffix.lower() != ".zip":
        raise ValueError("Choose a new .zip filename in an existing folder")
    if not source.joinpath("RUN-JARVIS.ps1").is_file() or not env_file.is_file():
        raise ValueError("JARVIS source or private .env is missing")
    if not config_dir.is_dir():
        raise ValueError("Private config folder is missing")
    configs = {}
    for name in ("backtalk.json", "barehands.json", "ai-visualizer.json"):
        path = config_dir / name
        if not path.is_file():
            raise ValueError(f"Missing private config: {name}")
        configs[name] = json.loads(path.read_text(encoding="utf-8"))
    files = _source_files(source) + _model_files(models)
    names = [name for _, name in files]
    if len(set(names)) != len(names) or "app/tools/private_release.py" not in names:
        raise ValueError("Source list is incomplete or has duplicate entries")
    manifest = {}
    total = 0
    for path, name in files:
        size = path.stat().st_size
        if size > MAX_FILE:
            raise ValueError(f"File exceeds release size limit: {name}")
        total += size
        if total > MAX_TOTAL:
            raise ValueError("Release exceeds size limit")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        manifest[name] = {"sha256": digest.hexdigest(), "bytes": size}
    manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
    private = json.dumps({"env": env_file.read_text(encoding="utf-8"),
                          "configs": configs,
                          "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest()},
                         ensure_ascii=False).encode("utf-8")
    envelope = encrypt_private(private, passphrase)
    try:
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=3, allowZip64=True) as archive:
            for path, name in files:
                archive.write(path, name)
            archive.writestr("private/secrets.json", json.dumps(envelope))
            if embed_passphrase:
                archive.writestr(PASSPHRASE_MEMBER, passphrase)
            archive.writestr("manifest.json", manifest_bytes)
            archive.write(source / "tools" / "Install-JARVIS.ps1", "Install-JARVIS.ps1")
            archive.write(source / "tools" / "Install-JARVIS.bat", "Install-JARVIS.bat")
        return {"path": str(output), "files": len(files), "bytes": output.stat().st_size,
            "passwordless_install": embed_passphrase}
    except Exception:
        output.unlink(missing_ok=True)
        raise


def _safe_name(name: str) -> Path:
    rel = PurePosixPath(name)
    if (rel.is_absolute() or ".." in rel.parts or len(rel.parts) < 2 or
            rel.parts[0] != "app" or "\\" in name or ":" in name):
        raise ValueError("Unsafe release archive path")
    return Path(*rel.parts[1:])


def _rebase_configs(configs: dict, destination: Path) -> dict[str, str]:
    root = destination.as_posix()
    backtalk = dict(configs["backtalk.json"])
    backtalk["agent_dir"] = root
    backtalk["extra_dirs"] = []
    backtalk["signals_dir"] = root + "/runtime/signals"
    backtalk["barehands_state_dir"] = root + "/components/barehands/state"
    backtalk.pop("mic_device", None)
    barehands = dict(configs["barehands.json"])
    barehands["orbs"] = [orb for orb in barehands.get("orbs", [])
                         if orb.get("kind") == "media" and orb.get("path") == "media"]
    visualizer = dict(configs["ai-visualizer.json"])
    visualizer["bus_dir"] = root + "/runtime/signals"
    return {"backtalk.json": json.dumps(backtalk, ensure_ascii=False, indent=2),
            "barehands.json": json.dumps(barehands, ensure_ascii=False, indent=2),
            "ai-visualizer.json": json.dumps(visualizer, ensure_ascii=False, indent=2)}


def unpack(bundle: Path, destination: Path, passphrase: str) -> dict:
    bundle, destination = bundle.resolve(strict=True), destination.resolve(strict=False)
    if destination.exists():
        raise ValueError("Installation folder already exists; no files were overwritten")
    if not destination.parent.is_dir():
        raise ValueError("Installation parent folder does not exist")
    with zipfile.ZipFile(bundle) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("Private release contains duplicate filenames")
        if archive.testzip() is not None:
            raise ValueError("Release ZIP failed its CRC check")
        if PASSPHRASE_MEMBER in archive.namelist():
            try:
                embedded_passphrase = archive.read(PASSPHRASE_MEMBER).decode("ascii")
            except UnicodeDecodeError as exc:
                raise ValueError("Invalid embedded install passphrase") from exc
            if passphrase and passphrase != embedded_passphrase:
                raise ValueError("Provided passphrase does not match this release")
            passphrase = embedded_passphrase
        if not passphrase:
            raise ValueError("This release needs a passphrase or an embedded install passphrase")
        manifest_bytes = archive.read("manifest.json")
        manifest = json.loads(manifest_bytes)
        envelope = json.loads(archive.read("private/secrets.json"))
        private = json.loads(decrypt_private(envelope, passphrase))
        if not isinstance(manifest, dict) or not isinstance(private.get("env"), str):
            raise ValueError("Invalid release metadata")
        if private.get("manifest_sha256") != hashlib.sha256(manifest_bytes).hexdigest():
            raise ValueError("Private release manifest authentication failed")
        expected_names = set(manifest) | {
            "manifest.json", "private/secrets.json", "Install-JARVIS.ps1", "Install-JARVIS.bat"}
        if PASSPHRASE_MEMBER in archive.namelist():
            expected_names.add(PASSPHRASE_MEMBER)
        if set(archive.namelist()) != expected_names:
            raise ValueError("Unexpected file in private release")
        configs = _rebase_configs(private["configs"], destination)
        total = 0
        for name, expected in manifest.items():
            _safe_name(name)
            info = archive.getinfo(name)
            if info.file_size != expected["bytes"] or info.file_size > MAX_FILE:
                raise ValueError("Release file length mismatch")
            total += info.file_size
            if total > MAX_TOTAL:
                raise ValueError("Private release exceeds size limit")
        stage = destination.parent / (".jarvis-install-" + uuid.uuid4().hex)
        stage.mkdir()
        try:
            for name, expected in manifest.items():
                target = stage / _safe_name(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                with archive.open(name) as source_file, target.open("xb") as output:
                    for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
                        digest.update(chunk)
                        output.write(chunk)
                if digest.hexdigest() != expected["sha256"]:
                    raise ValueError(f"Release checksum mismatch: {name}")
            (stage / ".env").write_text(private["env"], encoding="utf-8")
            config_folder = stage / "config"
            config_folder.mkdir(exist_ok=True)
            for name, content in configs.items():
                (config_folder / name).write_text(content, encoding="utf-8")
            stage.rename(destination)
        except Exception:
            # Leave the exact newly-created stage for inspection/recovery; no
            # pre-existing user folder is touched or removed.
            raise
    return {"path": str(destination), "files": len(manifest), "dependencies_ready": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("build")
    for flag in ("source", "env", "config", "models", "output"):
        make.add_argument("--" + flag, type=Path, required=True)
    make.add_argument("--generate-passphrase-file", type=Path)
    make.add_argument("--passwordless-install", action="store_true",
                      help="Embed the unlock passphrase in the ZIP; anyone with it can recover API keys")
    install = sub.add_parser("unpack")
    install.add_argument("--bundle", type=Path, required=True)
    install.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        if args.passwordless_install and args.generate_passphrase_file:
            raise ValueError("Choose either passwordless install or a separate passphrase file")
        if args.passwordless_install:
            password = secrets.token_urlsafe(24)
            result = build(args.source, args.env, args.config, args.models,
                           args.output, password, embed_passphrase=True)
        elif args.generate_passphrase_file:
            password_path = args.generate_passphrase_file.resolve(strict=False)
            if password_path.exists() or not password_path.parent.is_dir():
                raise ValueError("Choose a new passphrase file in an existing folder")
            password = secrets.token_urlsafe(24)
            result = build(args.source, args.env, args.config, args.models, args.output, password)
            try:
                with password_path.open("x", encoding="utf-8") as stream:
                    stream.write(password + "\n")
            except Exception:
                args.output.unlink(missing_ok=True)
                raise ValueError("Passphrase file could not be saved; release ZIP was removed")
            result["passphrase_file"] = str(password_path)
        else:
            password = getpass.getpass("Private release passphrase (not shown): ")
            confirm = getpass.getpass("Repeat passphrase: ")
            if password != confirm:
                raise ValueError("Passphrases do not match")
            result = build(args.source, args.env, args.config, args.models, args.output, password)
    else:
        with zipfile.ZipFile(args.bundle) as archive:
            passwordless = PASSPHRASE_MEMBER in archive.namelist()
        password = "" if passwordless else getpass.getpass("Private release passphrase (not shown): ")
        result = unpack(args.bundle, args.destination, password)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print(f"Private release failed: {error}", file=sys.stderr)
        raise SystemExit(1)
