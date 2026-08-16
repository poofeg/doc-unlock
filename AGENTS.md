# AGENTS.md

Guidance for AI coding agents working in this repository.

## What this project is

`doc-unlock` removes edit protection from Microsoft Office (OOXML) documents: PowerPoint (`.pptx`), Word (`.docx`), and Excel (`.xlsx`).

It handles two **independent** concerns:

- **Encryption** — decrypt an encrypted OOXML package using `msoffcrypto-tool`.
- **Edit protection** — strip the per-format protection elements (`modifyVerifier` for PPTX, `writeProtection`/`documentProtection` for DOCX, `fileSharing`/`workbookProtection` for XLSX).

A file can be encrypted, edit-protected, both, or neither.

## Stack

- Python 3.14, managed with `uv`.
- CLI: `typer`.
- Decryption: `msoffcrypto-tool`.
- Dev: `pytest`, `ruff`, `mypy` (strict, `src` only).
- HTTP API: `fastapi` (optional dependency, `uv sync --extra http`).

## Architecture

Strict layered DDD. Dependencies point inward: `interface` → `application` → `domain` ← `infrastructure`.

```
src/doc_unlock/
├── domain/           # pure, no I/O
│   ├── models.py     # DocumentFormat, EditProtection
│   ├── services.py   # ProtectionRemovalService
│   ├── ports.py      # FileStorage, Decryptor, PackageTransformer (interfaces)
│   └── exceptions.py # DocumentUnlockError and subclasses
├── application/      # use cases + DTOs
│   ├── dto.py        # UnlockDocumentCommand
│   └── unlock_document.py  # UnlockDocumentUseCase
├── infrastructure/   # adapters implementing domain ports
│   ├── filesystem.py # LocalFileStorage
│   └── ooxml/
│       ├── decryptor.py    # MsoffcryptoDecryptor
│       └── transformer.py  # ZipPackageTransformer (streaming)
└── interface/        # primary adapters
    ├── cli.py        # Typer app, `unlock` subcommand
    ├── http.py       # FastAPI app, `POST /unlock`, `GET /`
    └── index.html    # minimal upload form (no styles/JS)
```

### Ports (`domain/ports.py`)

- `FileStorage.open_read(path) -> IO[bytes]`, `open_write(path) -> IO[bytes]` (used by the CLI adapter)
- `Decryptor.decrypt(source, destination, password) -> None`, `Decryptor.is_encrypted(source) -> bool`
- `PackageTransformer.transform(source, destination, target_part, transform_part) -> None`

### Domain vocabulary

- `DocumentFormat` — `StrEnum`: `PPTX`, `DOCX`, `XLSX`; `from_path()`, `from_filename()`, `from_suffix()`. Supported suffixes: `.pptx`/`.ppsx`/`.pptm`/`.ppsm`/`.potx`/`.potm` → PPTX; `.docx`/`.docm`/`.dotx`/`.dotm` → DOCX; `.xlsx`/`.xlsm`/`.xltx`/`.xltm` → XLSX. Binary/legacy formats (`.doc`, `.xls`, `.ppt`, `.xlsb`) and add-ins (`.xlam`, `.ppam`) are intentionally unsupported.
- `EditProtection` — frozen value object describing where/how protection is stored (`part_name`, `namespace`, `element_names`).
- `ProtectionRemovalService` — stateless domain service:
  - `protection_for(format) -> EditProtection` (maps `PPTX`, `DOCX`, `XLSX` to their protection location);
  - `strip(content, protection) -> bytes` (pure XML transform of a **single** part).

There is no in-memory `Document` aggregate; the package is processed as a **stream** so it never has to be fully materialized.

### Exceptions

`DocumentUnlockError` (base) → `UnsupportedFormatError`, `InvalidPasswordError`, `PasswordRequiredError`, `InvalidDocumentError`. Domain code raises these; the CLI catches them and returns exit code 1, and the HTTP adapter maps them to status codes (400/415/422).

## Request flow (`UnlockDocumentUseCase`)

The use case operates on **open streams** supplied by the caller:

1. `DocumentFormat.from_filename(command.filename)`
2. `ProtectionRemovalService.protection_for(format)`
3. `Decryptor.is_encrypted(command.source)` — probe the source header once
4. if encrypted and no password: raise `PasswordRequiredError`
5. if encrypted: `Decryptor.decrypt(command.source, temp_file, password)` (streams the source, writes decrypted data to a disk-backed `SpooledTemporaryFile`); otherwise the password is ignored and the plain source is used directly
6. `PackageTransformer.transform(source, command.destination(), protection.part_name, strip)` — streams the ZIP, transforms only the target part, copies all other entries chunk-by-chunk

`command.destination` is a lazy callable returning the output stream; it is invoked only after the source has been validated/decrypted, so a failed run never creates an output file. The caller (CLI or HTTP) owns and closes the source/destination streams.

Memory: only the target XML part (small) is held fully; large media parts are streamed. The encrypted path streams the source and writes decrypted data to a temp file; peak RSS is ~0.1x input size.

## Conventions

- **No `print`.** Use `typer.echo`/`typer.secho` for user output in the interface layer, `logging` for internals.
- **typing-only imports** go inside `if TYPE_CHECKING:` (no `from __future__ import annotations` needed on Python 3.14).
- **Port implementations** are decorated with `@override` (mypy has `explicit-override` enabled).
- **Domain is pure.** No filesystem/network imports in `domain/`. The one allowed third-party dependency is `lxml` (in-memory XML, no I/O), imported in `services.py` with `# noqa: S410`.
- **Errors are exceptions**, not return codes or swallowed prints.
- ruff: line length 120, single quotes for inline strings, double quotes for docstrings (`quote-style = "single"`).

## Commands

```bash
uv sync                        # install deps + editable project
uv sync --extra http           # also install FastAPI (HTTP interface)
uv run doc-unlock unlock ...   # run CLI
uv run uvicorn doc_unlock.interface.http:app   # run HTTP server
uv run pytest                  # tests
uv run ruff check src tests    # lint
uv run ruff format src tests   # format
uv run mypy src                # type-check (strict, src only)
```

The CLI is also runnable as `python -m doc_unlock` (via `__main__.py`). There is no `main.py`; the console script points at `doc_unlock.interface.cli:app`, and the HTTP app at `doc_unlock.interface.http:app`.

## Tests

- Fixtures: `tests/fixtures/{pptx,docx,xlsx}/` — each with `plain`, `only-locked`, `only-encrypted`, `encrypted-and-locked`.
- Encryption password is `111`. The edit-protection password (`222`) is unused because protection removal is XML-based, not a password check.
- `tests/conftest.py` provides path fixtures and a ready-built `UnlockDocumentUseCase`.
- Tests are structural (parse output, assert protection elements removed / parts preserved). No golden/snapshot files.
- ruff relaxations for tests: `tests/**` ignores `S101` (assert) and `PLR2004` (magic values).
- `tests/test_http.py` uses `fastapi.testclient.TestClient` and requires the `http` extra.

## Gotchas

- **Typer single-command collapse.** With one command and no callback, Typer flattens the command into the root. The `@app.callback()` in `interface/cli.py` forces a group so the subcommand is `unlock`.
- **`Path` stays a runtime import in `interface/cli.py`.** Typer evaluates `Annotated[Path, ...]` via `get_type_hints` at runtime, so it must not be moved to `TYPE_CHECKING` (the import has `# noqa: TC003`).
- **`msoffcrypto` has no stubs.** It is ignored in `[tool.mypy.overrides]` with `ignore_missing_imports = true`.
- **`msoffcrypto` error mapping.** `DecryptionError("Document is not encrypted")` is not a password error; check `office_file.is_encrypted()` first and raise `InvalidDocumentError`.
- **XML security.** `lxml.etree` is used with a parser configured `resolve_entities=False, no_network=True` (import has `# noqa: S410`). Unlike `xml.etree.ElementTree`, lxml preserves namespace prefixes **and unused namespace declarations**, which DOCX requires: `word/settings.xml` has `mc:Ignorable` referencing prefixes (`w14`, `w16*`, `r`, …) whose URIs are declared but otherwise unused. ElementTree would drop those declarations and make Word report "unreadable content".
- **FastAPI evaluates `Annotated[...]` at runtime** (like Typer), so `Annotated` is a runtime import in `interface/http.py`. `BackgroundTask` must be imported from `starlette.background` (FastAPI only re-exports `BackgroundTasks`, plural).

## Current limitations / roadmap

- Edit protection is removed from one main part per format (`ppt/presentation.xml`, `word/settings.xml`, `xl/workbook.xml`); per-sheet XLSX `sheetProtection` (in `xl/worksheets/sheetN.xml`) is not handled yet.
- Streaming decryption is implemented in forks of `msoffcrypto-tool` and `olefile` (wired via `[tool.uv.sources]`), pending upstream merges.
- The HTTP interface is synchronous (`POST /unlock`); streaming the response concurrently with the request is a possible follow-up.
- A minimal HTML upload form is served at `/` (`interface/index.html`, no styles or JS).
