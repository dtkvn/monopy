# monopy

[![CI](https://github.com/dtkvn/monopy/actions/workflows/ci.yml/badge.svg)](https://github.com/dtkvn/monopy/actions/workflows/ci.yml)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/badge/type--checked-ty-blue?labelColor=orange)](https://github.com/astral-sh/ty)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/dtkvn/monopy/blob/main/LICENSE)

A Python package

## Features

- Fast and modern Python toolchain using Astral's tools (uv, ruff, ty)
- Type-safe with full type annotations
- Command-line interface built with Typer

## Installation

```bash
pip install monopy
```

Or using uv (recommended):

```bash
uv add monopy
```

## Quick Start

```python
import monopy

print(monopy.__version__)
```

### CLI Usage

```bash
# Show version
monopy --version

# Say hello
monopy hello World
```

## Development

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for package management

### Setup

```bash
git clone https://github.com/dtkvn/monopy.git
cd monopy
make install
```

### Running Tests

```bash
make test

# With coverage
make test-cov

# Across all Python versions
make test-matrix
```

### Code Quality

```bash
# Run all checks (lint, format, type-check)
make verify

# Auto-fix lint and format issues
make fix
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
