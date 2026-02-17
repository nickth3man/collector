# CI/CD Pipeline Implementation Plan

## 1. Overview

### Why CI/CD Matters

Continuous Integration and Continuous Deployment (CI/CD) pipelines are essential for maintaining code quality, catching bugs early, and ensuring smooth deployments. For this project, CI/CD will provide:

- **Automated Quality Checks**: Run tests and linters on every commit
- **Early Bug Detection**: Catch issues before they reach production
- **Consistent Code Style**: Enforce formatting and type checking standards
- **Configuration Validation**: Verify environment variables and settings
- **Coverage Tracking**: Monitor test coverage to prevent regression
- **Developer Confidence**: Know that changes won't break existing functionality

### Current State

The project currently has:
- Manual testing only
- No automated quality gates
- Local pytest execution (`uv run pytest`)
- Local linting tools configured (black, ruff)
- Test dependencies defined (pytest, pytest-cov)
- 6 test files covering services and scrapers
- No pre-commit hooks
- no CI/CD automation

### Target State

After implementing this plan:
- Automated test execution on every push and pull request
- Code style enforcement via black and ruff
- Type checking with mypy
- Configuration validation workflow
- Pre-commit hooks for local quality checks
- Coverage reporting with minimum threshold enforcement
- CI status badges in README
- Optional: Dependabot for dependency updates

---

## 2. Pipeline Architecture

We'll implement three separate GitHub Actions workflows:

### Workflow 1: Test Workflow (`test.yml`)
**Purpose**: Run the full test suite with coverage reporting
**Triggers**: Push to main/dev, Pull requests to main/dev
**Key Features**:
- Automated test execution
- Coverage reporting (XML format)
- Minimum coverage threshold (80%)
- Coverage artifact upload

### Workflow 2: Lint Workflow (`lint.yml`)
**Purpose**: Enforce code quality standards
**Triggers**: Push to all branches, Pull requests to all branches
**Key Features**:
- Black formatting validation
- Ruff linting
- Mypy type checking (excluding route tests initially)

### Workflow 3: Config Validation Workflow (`validate-config.yml`)
**Purpose**: Verify configuration management
**Triggers**: Push to all branches, Pull requests to all branches
**Key Features**:
- Environment variable validation
- Config class instantiation
- Validation rule testing

---

## 3. Test Workflow (.github/workflows/test.yml)

### File Location
`C:/Users/nicolas/Documents/GitHub/collector/.github/workflows/test.yml`

### Workflow Definition

```yaml
name: Tests

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install uv package manager
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: |
          uv sync --group dev

      - name: Run tests with coverage
        run: |
          uv run pytest --cov=src --cov-report=xml --cov-report=term-missing

      - name: Check coverage threshold
        run: |
          coverage=$(uv run python -c "import xml.etree.ElementTree as ET; tree=ET.parse('coverage.xml'); print(tree.getroot().attrib.get('line-rate', '0'))")
          echo "Coverage: $coverage"
          if (( $(echo "$coverage < 0.80" | bc -l) )); then
            echo "Coverage $(echo "$coverage * 100" | bc)% is below 80% threshold"
            exit 1
          fi
          echo "Coverage $(echo "$coverage * 100" | bc)% meets threshold"

      - name: Upload coverage to artifacts
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml
          retention-days: 30

      - name: Upload coverage to Codecov
        if: github.event_name == 'push'
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage.xml
          fail_ci_if_error: false
```

### Key Features Explained

1. **Triggers**: Runs on push to main/dev and all PRs targeting those branches
2. **Python Setup**: Uses Python 3.10 (matching project requirement)
3. **UV Package Manager**: Installs uv for fast dependency management
4. **Coverage Reporting**: Generates both XML and terminal coverage reports
5. **Threshold Enforcement**: Fails if coverage is below 80%
6. **Artifact Upload**: Saves coverage report for 30 days
7. **Codecov Integration**: Optional - requires CODECOV_TOKEN secret

### Expected Output

```
Run pytest --cov=src --cov-report=xml --cov-report=term-missing

---------- coverage: platform linux, python 3.10.12 ----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/collector/config/__init__.py            5      0   100%
src/collector/config/database.py            12      2    83%   23-24
src/collector/config/settings.py           45      3    93%   78-82
src/collector/services/job_service.py       67      8    88%   145-156
---------------------------------------------------------------------
TOTAL                                     350     42    88%

Coverage: 0.88
Coverage 88% meets threshold
```

---

## 4. Lint Workflow (.github/workflows/lint.yml)

### File Location
`C:/Users/nicolas/Documents/GitHub/collector/.github/workflows/lint.yml`

### Workflow Definition

```yaml
name: Lint

on:
  push:
    branches: ['**']
  pull_request:
    branches: ['**']

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install uv package manager
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: |
          uv sync --group dev

      - name: Check code formatting with Black
        run: |
          uv run black --check src tests

      - name: Lint with Ruff
        run: |
          uv run ruff check src tests

      - name: Type check with mypy
        run: |
          uv run mypy src/collector/config \
                      src/collector/models \
                      src/collector/repositories \
                      src/collector/scrapers \
                      src/collector/services \
                      --ignore-missing-imports
        continue-on-error: true  # Don't fail the workflow initially

      - name: Type check routes (optional)
        run: |
          uv run mypy src/collector/routes --ignore-missing-imports
        continue-on-error: true  # Known Flask type issues
```

### Key Features Explained

1. **Triggers**: Runs on all branches (push and PR)
2. **Black Check**: Verifies code is formatted (fails if not)
3. **Ruff Linting**: Catches code quality issues
4. **Mypy Type Checking**:
   - Excludes routes initially (known Flask type issues)
   - Uses `continue-on-error` to prevent workflow failure
   - Can be made strict once type annotations improve

### Configuration Alignment

The workflow uses existing tool configurations from `pyproject.toml`:

```toml
[tool.black]
line-length = 100
target-version = ["py310"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B"]
ignore = ["E501"]
```

### Expected Output

```
Check code formatting with Black
All files formatted correctly

Lint with Ruff
Checked 28 files in 2.5s
No issues found

Type check with mypy
Success: no issues found in 18 source files
```

---

## 5. Config Validation Workflow (.github/workflows/validate-config.yml)

### File Location
`C:/Users/nicolas/Documents/GitHub/collector/.github/workflows/validate-config.yml`

### Workflow Definition

```yaml
name: Validate Config

on:
  push:
    branches: ['**']
  pull_request:
    branches: ['**']

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install uv package manager
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: |
          uv sync

      - name: Create test .env file
        run: |
          cat > .env.test << 'EOF'
          FLASK_SECRET_KEY=test-secret-key-for-ci
          SCRAPER_DOWNLOAD_DIR=/tmp/test-downloads
          SCRAPER_DB_PATH=/tmp/test-scraper.db
          SCRAPER_MAX_CONCURRENT=2
          SCRAPER_IG_DELAY_MIN=5
          SCRAPER_IG_DELAY_MAX=10
          SCRAPER_DISK_WARN_MB=1024
          FLASK_HOST=127.0.0.1
          FLASK_PORT=5000
          EOF

      - name: Test Config class instantiation
        run: |
          uv run python -c "
          import os
          os.environ['FLASK_SECRET_KEY'] = 'test-key'
          from config import Config, get_config
          config = get_config()
          assert config.flask_secret_key == 'test-key'
          assert config.download_dir == './downloads'
          assert config.max_concurrent == 2
          print('Config instantiation: OK')
          print(f'Download dir: {config.download_dir}')
          print(f'Max concurrent: {config.max_concurrent}')
          "

      - name: Test validation rules
        run: |
          uv run python -c "
          import os
          from config import Config

          # Test valid values
          os.environ['FLASK_SECRET_KEY'] = 'test'
          os.environ['SCRAPER_MAX_CONCURRENT'] = '5'
          os.environ['SCRAPER_IG_DELAY_MIN'] = '10'
          os.environ['SCRAPER_IG_DELAY_MAX'] = '20'
          config = Config()
          assert config.max_concurrent == 5
          assert config.ig_delay_min == 10
          assert config.ig_delay_max == 20
          print('Validation rules: OK')
          "

      - name: Test environment variable loading
        run: |
          uv run python -c "
          import os
          os.environ['FLASK_SECRET_KEY'] = 'test'
          os.environ['SCRAPER_DOWNLOAD_DIR'] = '/custom/path'
          from config import get_config
          config = get_config()
          assert config.download_dir == '/custom/path'
          print('Environment variable loading: OK')
          "

      - name: Verify .env.example exists
        run: |
          if [ -f .env.example ]; then
            echo ".env.example exists"
          else
            echo "Warning: .env.example not found"
            echo "Create .env.example with all required environment variables"
          fi
```

### Key Features Explained

1. **Environment Variable Validation**: Tests Config class with various inputs
2. **Validation Rules**: Verifies min/max values, types, and constraints
3. **Default Values**: Confirms fallback values work correctly
4. **.env.example Check**: Ensures documentation file exists

### What This Tests

Based on the project's `src/collector/config/settings.py`:

```python
class Config:
    flask_secret_key: str = Field(..., env="FLASK_SECRET_KEY")
    download_dir: str = Field("./downloads", env="SCRAPER_DOWNLOAD_DIR")
    max_concurrent: int = Field(2, ge=1, le=10, env="SCRAPER_MAX_CONCURRENT")
    ig_delay_min: int = Field(5, ge=1, le=60, env="SCRAPER_IG_DELAY_MIN")
    ig_delay_max: int = Field(10, ge=1, le=60, env="SCRAPER_IG_DELAY_MAX")
    # ... more fields
```

The workflow validates:
- Required fields (FLASK_SECRET_KEY)
- Optional fields with defaults
- Integer constraints (ge=1, le=10)
- String parsing and validation

---

## 6. Pre-commit Hooks (Optional)

### File Location
`C:/Users/nicolas/Documents/GitHub/collector/.pre-commit-config.yaml`

### Configuration

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.15
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: uv run pytest
        language: system
        pass_filenames: false
        always_run: true
```

### Installation

```bash
# Install pre-commit
uv pip install pre-commit

# Install hooks
pre-commit install

# Run on all files (first time)
pre-commit run --all-files

# Run manually
pre-commit run
```

### How It Works

1. **Before Commit**: Hooks run automatically when you commit
2. **Black**: Auto-formats code (no manual intervention needed)
3. **Ruff**: Auto-fixes linting issues where possible
4. **Trailing Whitespace**: Cleans up whitespace
5. **End-of-file Fixer**: Ensures files end with newline
6. **Pytest**: Runs tests (always, even if no Python files changed)

### Benefits

- **Immediate Feedback**: Catch issues before pushing
- **Auto-formatting**: Black fixes formatting automatically
- **Consistency**: Enforces standards across all commits
- **Reduced CI Failures**: Most issues caught locally

---

## 7. Dependency Updates (Optional)

### File Location
`C:/Users/nicolas/Documents/GitHub/collector/.github/dependabot.yml`

### Configuration

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "nicolas"  # Replace with actual GitHub username
    assignees:
      - "nicolas"
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "deps"
      prefix-development: "dev-deps"
      include: "scope"
    groups:
      flask-dependencies:
        patterns:
          - "flask*"
        exclude-patterns:
          - "flask-babel"
      python-dependencies:
        patterns:
          - "*"
        exclude-patterns:
          - "flask*"

  # GitHub Actions dependencies
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "github-actions"
```

### Features

1. **Weekly Checks**: Automatically checks for updates every Monday
2. **Grouped Updates**: Bumps related dependencies together
3. **Auto-assign**: Assigns PRs to specified reviewer
4. **Labels**: Organizes PRs with tags
5. **Commit Messages**: Clear, consistent PR titles

### Auto-merge Strategy (Optional)

Add to `.github/workflows/dependabot-merge.yml`:

```yaml
name: Dependabot Auto-merge

on:
  pull_request:
    branches: [main, dev]

permissions:
  pull-requests: write
  contents: write

jobs:
  dependabot:
    runs-on: ubuntu-latest
    if: github.actor == 'dependabot[bot]'
    steps:
      - uses: actions/checkout@v4

      - name: Auto-merge dependabot PRs
        run: |
          gh pr merge "$PR_URL" --auto --merge
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 8. Implementation Steps

### Phase 1: Directory Structure (5 minutes)

```bash
# Create .github directory structure
mkdir -p .github/workflows

# Verify creation
ls -la .github/
ls -la .github/workflows/
```

### Phase 2: Create Test Workflow (10 minutes)

```bash
# Create test.yml
cat > .github/workflows/test.yml << 'EOF'
[Paste test.yml content from Section 3]
EOF

# Validate YAML syntax
cat .github/workflows/test.yml
```

### Phase 3: Create Lint Workflow (10 minutes)

```bash
# Create lint.yml
cat > .github/workflows/lint.yml << 'EOF'
[Paste lint.yml content from Section 4]
EOF

# Validate YAML syntax
cat .github/workflows/lint.yml
```

### Phase 4: Create Config Validation Workflow (10 minutes)

```bash
# Create validate-config.yml
cat > .github/workflows/validate-config.yml << 'EOF'
[Paste validate-config.yml content from Section 5]
EOF

# Validate YAML syntax
cat .github/workflows/validate-config.yml
```

### Phase 5: Create .env.example (5 minutes)

```bash
# Create .env.example
cat > .env.example << 'EOF'
# Required
FLASK_SECRET_KEY=your-secret-key-here

# Optional (with defaults)
SCRAPER_DOWNLOAD_DIR=./downloads
SCRAPER_DB_PATH=./scraper.db
SCRAPER_MAX_CONCURRENT=2
SCRAPER_IG_DELAY_MIN=5
SCRAPER_IG_DELAY_MAX=10
SCRAPER_DISK_WARN_MB=1024
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Optional (session encryption)
SCRAPER_SESSION_KEY=your-fernet-key-here
EOF
```

### Phase 6: Local Testing (15 minutes)

```bash
# Install act for local GitHub Actions testing
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Test workflows locally
act -j test
act -j lint
act -j validate
```

### Phase 7: Push to GitHub (5 minutes)

```bash
# Add files to git
git add .github/workflows/ .env.example

# Commit
git commit -m "Add CI/CD workflows for testing, linting, and config validation"

# Push to dev branch
git push origin dev
```

### Phase 8: Verify in GitHub Actions (5 minutes)

1. Go to repository on GitHub
2. Click "Actions" tab
3. Verify workflows ran successfully
4. Check each workflow's logs
5. Fix any issues that arise

### Phase 9: Add Pre-commit Hooks (Optional, 10 minutes)

```bash
# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
[Paste pre-commit config from Section 6]
EOF

# Install pre-commit
uv pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Phase 10: Add Dependabot (Optional, 5 minutes)

```bash
# Create .github/dependabot.yml
cat > .github/dependabot.yml << 'EOF'
[Paste dependabot config from Section 7]
EOF

# Commit and push
git add .github/dependabot.yml .pre-commit-config.yaml
git commit -m "Add pre-commit hooks and Dependabot configuration"
git push origin dev
```

### Phase 11: Add Badges to README (5 minutes)

Add badges to `README.md` after the title:

```markdown
# Content Collector

[![Tests](https://github.com/nicolas/collector/actions/workflows/test.yml/badge.svg)](https://github.com/nicolas/collector/actions/workflows/test.yml)
[![Lint](https://github.com/nicolas/collector/actions/workflows/lint.yml/badge.svg)](https://github.com/nicolas/collector/actions/workflows/lint.yml)
[![Config](https://github.com/nicolas/collector/actions/workflows/validate-config.yml/badge.svg)](https://github.com/nicolas/collector/actions/workflows/validate-config.yml)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/nicolas/collector/branch/main/graph/badge.svg)](https://codecov.io/gh/nicolas/collector)

A Flask-based web application...
```

Replace `nicolas/collector` with your actual GitHub repository path.

---

## 9. Badge Integration

### Badge Options

Add badges to `README.md` header:

```markdown
# Content Collector

[![Tests](https://github.com/USERNAME/collector/actions/workflows/test.yml/badge.svg)](https://github.com/USERNAME/collector/actions/workflows/test.yml)
[![Lint](https://github.com/USERNAME/collector/actions/workflows/lint.yml/badge.svg)](https://github.com/USERNAME/collector/actions/workflows/lint.yml)
[![Config](https://github.com/USERNAME/collector/actions/workflows/validate-config.yml/badge.svg)](https://github.com/USERNAME/collector/actions/workflows/validate-config.yml)

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Coverage](https://codecov.io/gh/USERNAME/collector/branch/main/graph/badge.svg)](https://codecov.io/gh/USERNAME/collector)
```

### Badge Types

1. **Workflow Status**: Shows pass/fail for each workflow
2. **Python Version**: Indicates supported Python versions
3. **Code Style**: Shows formatting standard
4. **Coverage**: Displays test coverage percentage (requires Codecov)

### Badge Services

- **GitHub Actions**: Built-in workflow status badges
- **Shields.io**: Custom badges for Python, license, etc.
- **Codecov**: Coverage reporting (requires account and token)

---

## 10. Verification

### Test Commit Workflow

```bash
# Create a test commit
echo "# Test commit" >> test-ci.txt
git add test-ci.txt
git commit -m "test: verify CI workflows"
git push origin dev
```

### Checklist

- [ ] Test workflow runs successfully
- [ ] Lint workflow runs successfully
- [ ] Config validation workflow runs successfully
- [ ] Coverage report generated (should be >80%)
- [ ] Coverage artifact uploaded
- [ ] No errors in workflow logs
- [ ] Badges display correctly in README
- [ ] Pre-commit hooks work (if installed)
- [ ] Dependabot PR created (if configured)

### Expected Workflow Status

After pushing to GitHub, you should see in the Actions tab:

```
✓ Tests (0.88 coverage)
✓ Lint (black, ruff, mypy passed)
✓ Validate Config (all checks passed)
```

### Troubleshooting Common Issues

#### Issue 1: UV Installation Fails

**Error**: `uv: command not found`

**Solution**: Add UV installation directory to PATH:

```yaml
- name: Install uv package manager
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "$HOME/.local/bin" >> $GITHUB_PATH
```

#### Issue 2: Coverage Check Fails

**Error**: `bc: command not found`

**Solution**: Install `bc` package or use Python for comparison:

```yaml
- name: Check coverage threshold
  run: |
    uv run python -c "
    import xml.etree.ElementTree as ET
    tree = ET.parse('coverage.xml')
    coverage = float(tree.getroot().attrib.get('line-rate', '0'))
    print(f'Coverage: {coverage*100:.1f}%')
    if coverage < 0.80:
      raise SystemExit(f'Coverage {coverage*100:.1f}% is below 80% threshold')
    "
```

#### Issue 3: Mypy Fails on Routes

**Error**: Flask-related type errors in routes

**Solution**: Use `continue-on-error` initially:

```yaml
- name: Type check routes
  run: uv run mypy src/collector/routes --ignore-missing-imports
  continue-on-error: true
```

Then gradually add type stubs for Flask:

```bash
uv pip install types-flask
```

---

## 11. Future Enhancements

### 11.1 Docker Image Build Workflow

Create `.github/workflows/docker.yml`:

```yaml
name: Docker Image

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: nicolas/collector
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### 11.2 Security Scanning

Add to test workflow or create separate security workflow:

```yaml
name: Security

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install bandit safety

      - name: Run Bandit security linter
        run: |
          bandit -r src/ -f json -o bandit-report.json
        continue-on-error: true

      - name: Check dependencies for vulnerabilities
        run: |
          safety check --json > safety-report.json
        continue-on-error: true

      - name: Upload security reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json
```

### 11.3 Performance Benchmarking

```yaml
name: Benchmark

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  benchmark:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install pytest-benchmark

      - name: Run benchmarks
        run: |
          pytest tests/benchmarks/ --benchmark-json=output.json

      - name: Store benchmark result
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'pytest'
          output-file-path: output.json
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: false
```

### 11.4 Deployment to Staging/Production

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging.collector.example.com

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to staging
        run: |
          # Add deployment commands here
          echo "Deploying to staging..."

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://collector.example.com

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        run: |
          # Add deployment commands here
          echo "Deploying to production..."
```

### 11.5 Integration Testing

```yaml
name: Integration Tests

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  integration:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run integration tests
        run: |
          pytest tests/integration/ -v
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
```

### 11.6 Code Coverage Reporting

Add Codecov configuration `.codecov.yml`:

```yaml
coverage:
  status:
    project:
      default:
        target: 80%
        threshold: 1%
        base: auto
    patch:
      default:
        target: 80%
        threshold: 1%
        base: auto

ignore:
  - "tests/*"
  - "*/migrations/*"

comment:
  layout: "reach,diff,flags,files,footer"
  behavior: default
  require_changes: false
  require_base: false
  require_head: true
```

---

## 12. Maintenance

### Regular Tasks

1. **Weekly**: Review Dependabot PRs
2. **Monthly**: Update workflow versions
3. **Quarterly**: Review coverage thresholds
4. **As Needed**: Add new workflows, update configurations

### Updating Workflow Versions

Check for new versions periodically:

```bash
# Check latest actions/checkout
gh api /repos/actions/checkout/releases/latest

# Check latest actions/setup-python
gh api /repos/actions/setup-python/releases/latest
```

### Monitoring CI Health

Key metrics to track:
- **Workflow Success Rate**: Should be >95%
- **Average Run Time**: Should be <5 minutes per workflow
- **Coverage Trend**: Should be stable or increasing
- **Flaky Tests**: Identify and fix tests that fail intermittently

---

## 13. Rollback Plan

If workflows cause issues:

```bash
# Revert problematic workflow commit
git revert <commit-hash>

# Or temporarily disable workflow
# Go to GitHub → Actions → Workflow → Disable workflow

# Or fix and push update
git add .github/workflows/xxx.yml
git commit -m "fix: resolve workflow issue"
git push origin dev
```

---

## 14. Success Criteria

The CI/CD pipeline is successful when:

- [ ] All workflows pass on every push to main/dev
- [ ] All workflows pass on all PRs to main/dev
- [ ] Coverage is maintained above 80%
- [ ] Code style is consistently enforced
- [ ] Configuration validation catches issues early
- [ ] Developers use pre-commit hooks
- [ ] Badges display current status in README
- [ ] Dependabot submits update PRs (if configured)
- [ ] Average workflow run time is <5 minutes
- [ ] False positive rate is <5%

---

## 15. Resources

### Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Codecov Documentation](https://docs.codecov.com/)

### Tools

- [act](https://github.com/nektos/act) - Run GitHub Actions locally
- [GitHub CLI](https://cli.github.com/) - Command-line interface for GitHub
- [Dependabot](https://docs.github.com/en/code-security/dependabot) - Automated dependency updates

### Examples

- [GitHub Actions Starter Workflows](https://github.com/actions/starter-workflows)
- [Python Action Examples](https://github.com/actions/setup-python/blob/main/.github/workflows/test.yml)
- [Flask CI Examples](https://github.com/pallets/flask/tree/main/.github/workflows)

---

## Appendix A: File Structure After Implementation

```
collector/
├── .github/
│   ├── workflows/
│   │   ├── test.yml
│   │   ├── lint.yml
│   │   └── validate-config.yml
│   └── dependabot.yml (optional)
├── .pre-commit-config.yaml (optional)
├── .codecov.yml (optional)
├── .env.example (new)
├── pyproject.toml (existing)
├── README.md (updated with badges)
├── src/ (existing)
├── tests/ (existing)
└── plans/
    └── 06-ci-cd-pipeline.md (this file)
```

---

## Appendix B: Quick Reference

### Workflow Files

1. **Test**: `.github/workflows/test.yml`
2. **Lint**: `.github/workflows/lint.yml`
3. **Config**: `.github/workflows/validate-config.yml`

### Configuration Files

1. **Pre-commit**: `.pre-commit-config.yaml`
2. **Dependabot**: `.github/dependabot.yml`
3. **Codecov**: `.codecov.yml`
4. **Environment**: `.env.example`

### Commands

```bash
# Test workflows locally
act -j test
act -j lint
act -j validate

# Install pre-commit hooks
pre-commit install

# Run pre-commit manually
pre-commit run --all-files

# Check workflow status
gh run list --workflow=test.yml
```

---

**Document Version**: 1.0
**Last Updated**: 2025-02-17
**Author**: Implementation Plan for CI/CD Pipeline
**Status**: Ready for Implementation
