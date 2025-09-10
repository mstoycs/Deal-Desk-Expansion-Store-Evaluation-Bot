# Contributing to Eddie

Thank you for your interest in contributing to Eddie! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by Shopify's code of conduct and maintain a respectful, inclusive environment.

## How to Contribute

### Reporting Issues

1. Check if the issue already exists in the GitHub Issues
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - System information (OS, Python version, etc.)
   - Relevant logs or error messages

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create a new issue labeled "enhancement" with:
   - Clear description of the proposed feature
   - Use cases and benefits
   - Potential implementation approach

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write or update tests
5. Update documentation
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/mstoycs/Deal-Desk-Expansion-Store-Evaluation-Bot.git
cd Deal-Desk-Expansion-Store-Evaluation-Bot
```

2. Run the setup script:
```bash
./scripts/setup.sh
```

3. Activate virtual environment:
```bash
source venv/bin/activate
```

4. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Coding Standards

### Python Style Guide

- Follow PEP 8
- Use Black for code formatting
- Use type hints where appropriate
- Maximum line length: 120 characters

### Code Quality

- Write clean, readable code
- Add docstrings to all functions and classes
- Include inline comments for complex logic
- Keep functions focused and small
- Follow DRY (Don't Repeat Yourself) principle

### Testing

- Write unit tests for new features
- Maintain or improve code coverage
- Test edge cases and error conditions
- Run tests before submitting PR:
```bash
pytest
```

### Documentation

- Update README.md if needed
- Add docstrings to new functions/classes
- Update API documentation for endpoint changes
- Include examples for new features

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

### Examples

```
feat(extractor): add support for pagination in product extraction

Implemented automatic pagination detection and traversal for stores
with paginated product listings. This improves product discovery
completeness for large catalogs.

Closes #123
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test
pytest test_product_extraction.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test names
- Include both positive and negative test cases
- Mock external dependencies

## Review Process

1. All code must be reviewed before merging
2. Reviewers will check for:
   - Code quality and style
   - Test coverage
   - Documentation
   - Performance implications
   - Security considerations

## Release Process

1. Update version in `setup.py` or `__version__`
2. Update CHANGELOG.md
3. Create release PR
4. After approval, merge to main
5. Tag release: `git tag -a v1.0.0 -m "Release version 1.0.0"`
6. Push tags: `git push origin --tags`

## Questions?

If you have questions, please:
1. Check the documentation
2. Search existing issues
3. Ask in #deal-desk-tools Slack channel
4. Create a new issue if needed

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Eddie! 🚀
