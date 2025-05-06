# Contributing to WNBA Fantasy League

Thank you for considering contributing to WNBA Fantasy League! We welcome contributions of all kinds, including bug reports, feature requests, documentation, and code. By participating, you agree to abide by our code of conduct.

## How to Contribute

1. Fork the repository.
2. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Make your changes, following our coding style:
   - Format code with [Black](https://github.com/psf/black) and [isort](https://github.com/PyCQA/isort).
   - Lint your code with [Ruff](https://github.com/astral-sh/ruff).
4. Run tests:
   ```bash
   pytest
   ```
5. Ensure all pre-commit hooks pass:
   ```bash
   pre-commit run --all-files
   ```
6. Commit your changes with descriptive messages.
7. Push to your fork:
   ```bash
   git push origin <your-branch-name>
   ```
8. Open a pull request against the `main` branch.

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines.
- Automatic formatting is configured with Black and isort.
- Linting rules are enforced by Ruff.

## Tests

We use pytest. To run the test suite:

```bash
pytest
```

## Pre-commit Hooks

We use pre-commit to run linters, formatters, and tests. Set up hooks:

```bash
pre-commit install
```

Ensure all checks pass before committing:

```bash
pre-commit run --all-files
```

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features.