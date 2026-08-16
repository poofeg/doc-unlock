# AGENTS.md

Guidance for AI coding agents working in this repository.

## What this project is

`doc-unlock` removes edit protection from Microsoft Office (OOXML) documents. Currently PowerPoint (`.pptx`) is implemented; DOCX/XLSX are recognized but not yet supported.

It handles two **independent** concerns:

- **Encryption** — decrypt an encrypted OOXML package using `msoffcrypto-tool`.
- **Edit protection** — strip `modifyVerifier` / `documentProtection` elements from `ppt/presentation.xml`.

A file can be encrypted, edit-protected, both, or neither.

## Stack

- Python 3.14, managed with `uv`.
- CLI: `typer`.
- Decryption: `msoffcrypto-tool`.
- Dev: `pytest`, `ruff`, `mypy` (strict, `src` only).
- Future: FastAPI interface (keep in mind when deciding where code belongs).

## Architecture

Strict layered DDD. Dependencies point inward: `interface` → `application` → `domain` ← `infrastructure`.

```
src/doc_unlock/
├── domain/           # pure, no I/O, no external deps
│   ├── models.py     # DocumentFormat, EditProtection
│   ├── services.py   # ProtectionRemovalService
│   ├── ports.py      # FileStorage, Decryptor, PackageTransformer (interfaces)
│   └── exceptions.py # DocumentUnlockError and subclasses
├── application/      # use cases + DTOs
│   ├── dto.py        # UnlockDocumentCommand
│   └── unlock_document.py  # UnlockDocumentUseCase, UnlockDocumentResult
├── infrastructure/   # adapters implementing domain ports
│   ├── filesystem.py # LocalFileStorage
│   └── ooxml/
│       ├── decryptor.py    # MsoffcryptoDecryptor
│       └── transformer.py  # ZipPackageTransformer (streaming)
└── interface/        # primary adapters
    └── cli.py        # Typer app, `unlock` subcommand
```

### Ports (`domain/ports.py`)

- `FileStorage.open_read(path) -> BinaryIO`, `open_write(path) -> BinaryIO`
- `Decryptor.decrypt(source, destination, password) -> None`
- `PackageTransformer.transform(source, destination, target_part, transform_part) -> None`

### Domain vocabulary

- `DocumentFormat` — `StrEnum`: `PPTX`, `DOCX`, `XLSX`; has `from_path()` (PowerPoint variants `.ppsx`/`.pptm`/`.ppsm` map to `PPTX`).
- `EditProtection` — frozen value object describing where/how protection is stored (`part_name`, `namespace`, `element_names`).
- `ProtectionRemovalService` — stateless domain service:
  - `protection_for(format) -> EditProtection` (raises `UnsupportedFormatError` for unhandled formats);
  - `strip(content, protection) -> bytes` (pure XML transform of a **single** part).

There is no in-memory `Document` aggregate; the package is processed as a **stream** so it never has to be fully materialized.

### Exceptions

`DocumentUnlockError` (base) → `UnsupportedFormatError`, `InvalidPasswordError`, `InvalidDocumentError`. Domain code raises these; the CLI catches them and returns exit code 1.

## Request flow (`UnlockDocumentUseCase`)

1. `DocumentFormat.from_path(input_path)`
2. `ProtectionRemovalService.protection_for(format)`
3. if encrypted: `FileStorage.open_read(input_path)` → `Decryptor.decrypt(source, temp_file, password)` (streams the source, writes decrypted data to a disk-backed temp file)
4. else: `FileStorage.open_read(input_path)`
5. `FileStorage.open_write(output_path)`
6. `PackageTransformer.transform(source, destination, protection.part_name, strip)` — streams the ZIP, transforms only the target part, copies all other entries chunk-by-chunk
7. return `UnlockDocumentResult`

Memory: only `ppt/presentation.xml` (small) is held fully; large media parts are streamed. The encrypted path streams the source and writes decrypted data to a temp file; peak RSS is ~0.6x input size (the remaining overhead is inside `olefile`, not `msoffcrypto`).

## Conventions

- **No `print`.** Use `typer.echo`/`typer.secho` for user output in the interface layer, `logging` for internals.
- **typing-only imports** go inside `if TYPE_CHECKING:` (no `from __future__ import annotations` needed on Python 3.14).
- **Port implementations** are decorated with `@override` (mypy has `explicit-override` enabled).
- **Domain is pure.** No filesystem/network/third-party imports in `domain/` except stdlib (`xml.etree.ElementTree`).
- **Errors are exceptions**, not return codes or swallowed prints.
- ruff: line length 120, single quotes for inline strings, double quotes for docstrings (`quote-style = "single"`).

## Commands

```bash
uv sync                        # install deps + editable project
uv run doc-unlock unlock ...   # run CLI
uv run pytest                  # tests
uv run ruff check src tests    # lint
uv run ruff format src tests   # format
uv run mypy src                # type-check (strict, src only)
```

The CLI is also runnable as `python -m doc_unlock` (via `__main__.py`). There is no `main.py`; the console script points at `doc_unlock.interface.cli:app`.

## Tests

- Fixtures: `tests/fixtures/pptx/` — `plain`, `only-locked`, `only-encrypted`, `encrypted-and-locked`.
- Encryption password is `111`. The edit-protection password (`222`) is unused because protection removal is XML-based, not a password check.
- `tests/conftest.py` provides path fixtures and a ready-built `UnlockDocumentUseCase`.
- Tests are structural (parse output, assert protection elements removed / parts preserved). No golden/snapshot files.
- ruff relaxations for tests: `tests/**` ignores `S101` (assert) and `PLR2004` (magic values).

## Gotchas

- **Typer single-command collapse.** With one command and no callback, Typer flattens the command into the root. The `@app.callback()` in `interface/cli.py` forces a group so the subcommand is `unlock`.
- **`Path` stays a runtime import in `interface/cli.py`.** Typer evaluates `Annotated[Path, ...]` via `get_type_hints` at runtime, so it must not be moved to `TYPE_CHECKING` (the import has `# noqa: TC003`).
- **`msoffcrypto` has no stubs.** It is ignored in `[tool.mypy.overrides]` with `ignore_missing_imports = true`.
- **`msoffcrypto` error mapping.** `DecryptionError("Document is not encrypted")` is not a password error; check `office_file.is_encrypted()` first and raise `InvalidDocumentError`.
- **XML security.** `xml.etree.ElementTree` is used with `# noqa: S405`/`S314`. Switching to `defusedxml` is a known follow-up (requires `uv add defusedxml`).

## Current limitations / roadmap

- Only PPTX edit-protection removal is implemented. DOCX/XLSX are recognized by `DocumentFormat.from_path` but `ProtectionRemovalService` raises `UnsupportedFormatError` for them.
- Streaming decryption is implemented in a fork of `msoffcrypto-tool` (wired via `[tool.uv.sources]`), pending upstream merge. The remaining encrypted-path memory overhead is `olefile`.
- FastAPI interface is planned, not started.
