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
│   ├── models.py     # Document, DocumentFormat, PackagePart, EditProtection
│   ├── services.py   # ProtectionRemovalService
│   ├── ports.py      # FileStorage, Decryptor, DocumentRepository (interfaces)
│   └── exceptions.py # DocumentUnlockError and subclasses
├── application/      # use cases + DTOs
│   ├── dto.py        # UnlockDocumentCommand
│   └── unlock_document.py  # UnlockDocumentUseCase, UnlockDocumentResult
├── infrastructure/   # adapters implementing domain ports
│   ├── filesystem.py # LocalFileStorage
│   └── ooxml/
│       ├── decryptor.py   # MsoffcryptoDecryptor
│       └── repository.py  # OoxmlDocumentRepository
└── interface/        # primary adapters
    └── cli.py        # Typer app, `unlock` subcommand
```

### Ports (`domain/ports.py`)

- `FileStorage.read(path) -> bytes`, `write(path, data) -> None`
- `Decryptor.decrypt(data, password) -> bytes`
- `DocumentRepository.parse(data, format) -> Document`, `serialize(document) -> bytes`

Note: `DocumentRepository` is a bytes↔`Document` codec, **not** a path-based `load`/`save`. Decryption operates on raw bytes before parsing, so raw file I/O lives in `FileStorage`.

### Domain vocabulary

- `Document` — aggregate: a `DocumentFormat` plus a list of `PackagePart`s.
- `DocumentFormat` — `StrEnum`: `PPTX`, `DOCX`, `XLSX`; has `from_path()`.
- `PackagePart` — frozen value object: `name` + `content: bytes`.
- `EditProtection` — frozen value object describing where/how protection is stored (`part_name`, `namespace`, `element_names`).
- `ProtectionRemovalService.remove(document) -> Document` — the pure business rule.

### Exceptions

`DocumentUnlockError` (base) → `UnsupportedFormatError`, `InvalidPasswordError`, `InvalidDocumentError`. Domain code raises these; the CLI catches them and returns exit code 1.

## Request flow (`UnlockDocumentUseCase`)

1. `DocumentFormat.from_path(input_path)`
2. `FileStorage.read(input_path)`
3. if encrypted: `Decryptor.decrypt(data, password)`
4. `DocumentRepository.parse(data, format)`
5. `ProtectionRemovalService.remove(document)`
6. `DocumentRepository.serialize(document)`
7. `FileStorage.write(output_path, data)`

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
- FastAPI interface is planned, not started.
