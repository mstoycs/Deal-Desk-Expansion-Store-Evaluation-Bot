# Pre-commit Hooks Guide for Eddie

## Overview
Pre-commit hooks automatically format and check your code before each commit, ensuring consistent code quality and preventing CI failures.

## What's Installed

### 1. **Black** (Python Formatter)
- Automatically formats Python code to a consistent style
- Same formatter that checks code in CI pipeline
- Prevents "would reformat" CI failures

### 2. **Flake8** (Critical Error Check)
- Checks for syntax errors and critical issues
- Only checks for serious problems (E9, F63, F7, F82)
- Won't block commits for style issues

### 3. **File Cleanup**
- Removes trailing whitespace
- Ensures files end with a newline
- Checks YAML/JSON syntax
- Prevents merge conflicts
- Blocks large files (>1MB)

## Installation

### First Time Setup
```bash
# Install pre-commit
pip3 install pre-commit

# Navigate to the GitHub package directory
cd Eddie-GitHub-Package

# Install the hooks
pre-commit install
```

Or use the setup script:
```bash
./setup_pre_commit.sh
```

## Usage

### Automatic (Recommended)
Just commit normally! Pre-commit will:
1. Run automatically before each commit
2. Format your Python files with Black
3. Fix trailing whitespace and EOF issues
4. Check for syntax errors
5. If fixes are made, you'll need to add the changes and commit again

### Manual Check
To manually run on all files:
```bash
pre-commit run --all-files
```

To run on specific files:
```bash
pre-commit run --files app.py product_extractor.py
```

## Common Scenarios

### Scenario 1: Black reformats files
```bash
$ git commit -m "Add new feature"
black....................................................................Failed
- hook id: black
- files were modified by this hook

# Black formatted your files. Add the changes and commit again:
$ git add .
$ git commit -m "Add new feature"
```

### Scenario 2: Skipping hooks (emergency only)
```bash
# Use ONLY when absolutely necessary
git commit --no-verify -m "Emergency fix"
```

### Scenario 3: Update hooks to latest versions
```bash
pre-commit autoupdate
```

## Troubleshooting

### Issue: "command not found: pre-commit"
```bash
pip3 install pre-commit
```

### Issue: Hooks not running
```bash
# Reinstall hooks
pre-commit install
```

### Issue: Different formatting locally vs CI
```bash
# Update Black to match CI version
pip3 install black==24.8.0
```

## Benefits

1. **No more CI failures** due to formatting
2. **Consistent code style** across the team
3. **Automatic cleanup** of common issues
4. **Faster PR reviews** (no style comments)
5. **Better code quality** overall

## Configuration

The configuration is in `.pre-commit-config.yaml`. Current settings:
- Black: Standard Python formatting
- Flake8: Only critical errors (not style)
- Max line length: 127 characters
- Max file size: 1MB

## For CI/CD

The same checks run in GitHub Actions:
- `black --check .` verifies formatting
- `flake8` checks for critical errors

With pre-commit hooks, your local commits will always pass these CI checks!
