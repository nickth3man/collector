# Prettier Setup Guide

This document explains how Prettier is configured for the Content Collector
project and how to use it effectively.

## Overview

Prettier is an opinionated code formatter that ensures consistent code style
across the project. It's configured to work with:

- JavaScript/TypeScript files
- HTML templates (Jinja2)
- CSS files
- JSON configuration files
- Markdown documentation

## Configuration Files

### `.prettierrc.json`

Main Prettier configuration with:

- 100 character line width (matches Ruff)
- 2-space indentation
- Double quotes (matches project style)
- ES5 trailing commas
- LF line endings
- Language-specific overrides

### `.prettierignore`

Excludes from formatting:

- Dependencies and build artifacts
- Python cache files
- Minified vendor files
- Database files
- IDE and OS generated files

### `.vscode/settings.json`

VS Code integration:

- Prettier as default formatter
- Format on save enabled
- Language-specific formatter assignments
- Auto-import and organization settings

## Installation

### Development Dependencies

Prettier is included in the `dev` dependency group in `pyproject.toml`:

```bash
uv add --dev prettier
```

### VS Code Extension

Install the
[Prettier - Code formatter](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
extension.

## Usage

### Command Line

Format all files:

```bash
uv run prettier --write .
```

Check formatting without changes:

```bash
uv run prettier --check .
```

Format specific files:

```bash
uv run prettier --write src/collector/templates/**/*.html
```

### VS Code Integration

1. **Automatic Formatting**: Files are formatted automatically on save
2. **Manual Formatting**: Use `Shift+Alt+F` or `Ctrl+Shift+I` to format
   selection
3. **Format on Paste**: Enabled by default

### Git Integration (Optional)

Add pre-commit hook to enforce formatting:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, html, css, json, markdown]
```

## File-Specific Configuration

### HTML Templates

- Parser: `html`
- Whitespace sensitivity: `ignore`
- 2-space indentation
- Handles Jinja2 syntax gracefully

### JavaScript/TypeScript

- ES5+ syntax support
- Arrow functions with parentheses
- Consistent quote style
- Proper import/export formatting

### CSS

- Standard CSS formatting
- Proper selector and rule organization
- 2-space indentation

### JSON

- Sorted keys (where appropriate)
- Consistent spacing
- 2-space indentation

## Integration with Existing Tools

### Ruff (Python)

- Both tools use 100-character line width
- Ruff handles Python files, Prettier handles web files
- Consistent indentation and quote styles

### Project Structure

Prettier focuses on:

- `src/collector/static/` - CSS, JS
- `src/collector/templates/` - HTML templates
- Configuration files (JSON, YAML)
- Documentation (Markdown)

## Troubleshooting

### Common Issues

1. **Prettier not formatting on save**
   - Check VS Code settings
   - Ensure Prettier extension is installed
   - Verify `.prettierrc.json` is valid

2. **Conflicts with other formatters**
   - Disable other formatting extensions
   - Check language-specific formatter settings

3. **HTML formatting issues**
   - Jinja2 syntax is preserved
   - Use `htmlWhitespaceSensitivity: "ignore"`

### Debugging

Check Prettier configuration:

```bash
uv run prettier --find-config-path
uv run prettier --debug-check
```

Validate configuration:

```bash
uv run prettier --find-config-path .prettierrc.json
```

## Best Practices

1. **Team Consistency**: All team members should use the same Prettier
   configuration
2. **CI/CD Integration**: Add formatting checks to your pipeline
3. **Editor Integration**: Use editor-specific plugins for seamless experience
4. **Selective Formatting**: Use `.prettierignore` for files that shouldn't be
   formatted
5. **Version Control**: Commit configuration files to ensure consistency

## Migration Guide

For existing codebases:

1. **Initial Format**: Run `uv run prettier --write .` to format all files
2. **Review Changes**: Check git diff for unexpected changes
3. **Commit Separately**: Commit formatting changes separately from functional
   changes
4. **Enable Integration**: Set up VS Code and Git hooks for ongoing consistency

## Performance Considerations

- Prettier is fast, but exclude large directories with `.prettierignore`
- Use `--cache` for repeated formatting operations
- Consider incremental formatting in large projects

## Resources

- [Official Prettier Documentation](https://prettier.io/docs/en/)
- [Prettier VS Code Extension](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
- [Configuration Options](https://prettier.io/docs/en/options.html)
- [Ignoring Code](https://prettier.io/docs/en/ignore.html)
