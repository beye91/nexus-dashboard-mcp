# Contributing to Nexus Dashboard MCP Server

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## Code of Conduct

Be respectful, inclusive, and professional. We're all here to build great tools for network automation.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Docker version, etc.)
   - Relevant logs

### Suggesting Features

1. Open an issue with the feature request template
2. Describe the use case and benefits
3. Provide examples if possible
4. Be open to discussion and feedback

### Contributing Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write/update tests
5. Update documentation
6. Run tests and linting
7. Commit with clear messages
8. Push to your fork
9. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/nexus-dashboard-mcp.git
cd nexus-dashboard-mcp

# Add upstream remote
git remote add upstream https://github.com/original-owner/nexus-dashboard-mcp.git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use Black for formatting: `black src/ tests/`
- Use isort for imports: `isort src/ tests/`
- Type hints for all function signatures
- Docstrings for all public functions/classes

Example:
```python
def process_data(data: Dict[str, Any], timeout: int = 30) -> List[str]:
    """Process data and return list of results.

    Args:
        data: Input data dictionary
        timeout: Operation timeout in seconds

    Returns:
        List of processed result strings

    Raises:
        ValueError: If data is invalid
    """
    pass
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/
pylint src/

# Type check
mypy src/

# Run all checks
./scripts/quality.sh  # If provided
```

### Testing

- Write tests for all new features
- Maintain >80% code coverage
- Use pytest for testing
- Mock external dependencies (Nexus Dashboard API)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_security.py

# Run specific test
pytest tests/unit/test_security.py::test_edit_mode_enabled
```

## Commit Messages

Use conventional commits format:

```
type(scope): brief description

Detailed explanation if needed

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add support for Analyze API endpoints

Implements loading and tool generation for Nexus Dashboard
Analyze API with 198 endpoints.

Closes #45
```

```
fix(auth): handle token expiration correctly

Previously, expired tokens caused authentication failures.
Now automatically refresh tokens when they expire.

Fixes #67
```

## Pull Request Process

1. **Update Documentation**: Ensure README, docstrings, and docs/ are updated
2. **Add Tests**: All new code must have tests
3. **Run Tests**: Ensure all tests pass
4. **Update Changelog**: Add entry to CHANGELOG.md
5. **One Feature Per PR**: Keep PRs focused and reviewable
6. **Link Issues**: Reference related issues in PR description

### PR Template

```markdown
## Description
Brief description of changes

## Related Issue
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] All tests passing
- [ ] No new warnings
```

## Project Structure

```
src/
├── config/          # Configuration and database setup
├── core/            # MCP server core logic
├── middleware/      # Authentication, security, logging
├── models/          # Database models
├── services/        # Business logic
└── utils/           # Utility functions

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── fixtures/        # Test fixtures and mocks
```

## Adding New Features

### Example: Adding a New API

1. Add OpenAPI spec to `openapi_specs/`
2. Update `src/core/api_loader.py` to include new API
3. Add load method in `src/core/mcp_server.py`
4. Write tests in `tests/integration/test_new_api.py`
5. Update documentation in `docs/API_REFERENCE.md`
6. Add example usage to README

### Example: Adding Middleware

1. Create file in `src/middleware/`
2. Implement middleware interface
3. Integrate in `src/core/mcp_server.py`
4. Write unit tests in `tests/unit/`
5. Document in `docs/ARCHITECTURE.md`

## Documentation

### Where to Document

- **README.md**: Quick start, features, basic usage
- **docs/ARCHITECTURE.md**: System design, components
- **docs/DEPLOYMENT.md**: Installation, configuration
- **docs/API_REFERENCE.md**: API endpoints and usage
- **Docstrings**: All public functions and classes

### Documentation Style

- Clear and concise
- Include examples
- Keep updated with code changes
- Use markdown for all docs

## Release Process

(For maintainers)

1. Update version in `src/__version__.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.2.0`
4. Push tag: `git push origin v1.2.0`
5. GitHub Actions builds and publishes Docker image
6. Create GitHub release with notes

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open an issue with bug template
- **Real-time chat**: (If available) Discord/Slack link

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
