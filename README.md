# doc-unlock

Remove edit protection from Microsoft Office (OOXML) documents — currently PowerPoint (`.pptx`).

`doc-unlock` is a command-line utility that removes the restrictions preventing you from editing a document. It handles two independent mechanisms:

- **Document encryption** — the encrypted OOXML package is decrypted using the password.
- **Edit protection** — the `modifyVerifier` / `documentProtection` elements are stripped from the presentation XML.

A file can be encrypted, edit-protected, both, or neither.

> Use this only on files you own or are otherwise authorized to modify.

## Installation

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

This installs the runtime dependencies and the `doc-unlock` command into the project environment. If the environment is not active, prefix commands with `uv run` (for example, `uv run doc-unlock …`).

## Usage

```
doc-unlock unlock INPUT [--password PASSWORD] [--output OUTPUT] [--encrypted/--no-encrypted]
```

| Argument / option | Description |
| --- | --- |
| `INPUT` | Path to the document to unlock (required). |
| `-p`, `--password` | Password used to decrypt an encrypted document. |
| `-o`, `--output` | Where to save the result. Defaults to `<name> (unprotected).<ext>` next to the input. |
| `--encrypted` / `--no-encrypted` | Whether the file is encrypted. Defaults to `--encrypted`. |

The tool can also be run as a module: `python -m doc_unlock …`.

### Examples

Remove edit protection from a file that is **not** encrypted:

```bash
doc-unlock unlock deck.pptx --no-encrypted
```

Decrypt an encrypted file (and remove edit protection too, if present):

```bash
doc-unlock unlock secret.pptx --password 111
```

Save to a specific location:

```bash
doc-unlock unlock deck.pptx --no-encrypted -o out/deck.pptx
```

## Supported formats

| Format | Decryption | Edit-protection removal |
| --- | --- | --- |
| PPTX | ✅ | ✅ |
| DOCX | planned | planned |
| XLSX | planned | planned |

The format detector recognizes DOCX and XLSX, but their edit-protection schemas are not implemented yet — attempting to unlock them raises `UnsupportedFormatError`.

## How it works

1. Read the input file.
2. If encrypted, decrypt the package with [`msoffcrypto-tool`](https://github.com/nolze/msoffcrypto-tool).
3. Stream the OOXML package (a ZIP archive) entry-by-entry.
4. Remove the edit-protection elements from `ppt/presentation.xml`; copy all other entries unchanged.
5. Write the result as a new package.

The package is processed as a stream, so only the small `ppt/presentation.xml` part is loaded fully; large parts (e.g. media) are copied chunk-by-chunk.

## Project layout

The code follows a layered (DDD) structure, which keeps the CLI thin and makes room for a future FastAPI interface:

```
src/doc_unlock/
├── domain/          # entities, value objects, domain services, ports, exceptions
├── application/     # use cases and DTOs
├── infrastructure/  # adapters: filesystem, msoffcrypto decryptor, OOXML transformer
└── interface/       # primary adapters: Typer CLI (FastAPI planned)
```

## Development

```bash
uv sync                        # install all dependencies
uv run pytest                  # run the test suite
uv run ruff check src tests    # lint
uv run ruff format src tests   # format
uv run mypy src                # type-check
```

## License

[MIT](LICENSE)
