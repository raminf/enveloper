# JSON/YAML Details

## Overview

`enveloper` supports importing and exporting secrets in JSON and YAML formats, making it easy to integrate with Docker, CDK, and other project formats.

## Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| JSON | `.json` | JavaScript Object Notation |
| YAML | `.yaml`, `.yml` | YAML Ain't Markup Language |

## Import Formats

### JSON

**Flat format:**
```json
{
  "KEY1": "value1",
  "KEY2": "value2"
}
```

**Nested with domain:**
```json
{
  "prod": {
    "KEY1": "value1",
    "KEY2": "value2"
  }
}
```

**Nested with domain and project:**
```json
{
  "prod": {
    "myapp": {
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

**Complex nested structure:**
```json
{
  "prod": {
    "myapp": {
      "DATABASE_URL": "postgres://...",
      "API_KEY": "secret123"
    },
    "staging": {
      "DATABASE_URL": "postgres://staging...",
      "API_KEY": "staging123"
    }
  }
}
```

### YAML

**Flat format:**
```yaml
KEY1: value1
KEY2: value2
```

**Nested with domain:**
```yaml
prod:
  KEY1: value1
  KEY2: value2
```

**Nested with domain and project:**
```yaml
prod:
  myapp:
    KEY1: value1
    KEY2: value2
```

**Complex nested structure:**
```yaml
prod:
  myapp:
    DATABASE_URL: "postgres://..."
    API_KEY: "secret123"
  staging:
    DATABASE_URL: "postgres://staging..."
    API_KEY: "staging123"
```

## Import Commands

### Import JSON

```bash
# Import flat JSON
enveloper import secrets.json --format json -d prod

# Import nested JSON (domain in file)
enveloper import secrets.json --format json
```

### Import YAML

```bash
# Import flat YAML
enveloper import secrets.yaml --format yaml -d prod

# Import nested YAML (domain in file)
enveloper import secrets.yaml --format yaml
```

## Export Formats

### JSON

Export produces a flat key-value object for the chosen domain:

```bash
enveloper export -d prod --format json
```

Output:
```json
{
  "KEY1": "value1",
  "KEY2": "value2"
}
```

### YAML

```bash
enveloper export -d prod --format yaml
```

Output:
```yaml
KEY1: value1
KEY2: value2
```

## Use Cases

### Docker Integration

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  app:
    image: myapp:latest
    env_file:
      - .env
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY}
```

**Export for Docker:**
```bash
enveloper export -d prod --format dotenv -o .env
docker-compose up
```

### CDK / Terraform

**Export for infrastructure:**
```bash
enveloper export -d prod --format json -o config.json
```

**Use in CDK:**
```python
import json
from aws_cdk import aws_lambda

with open('config.json') as f:
    config = json.load(f)

lambda_fn = lambda_.Function(
    self, "MyFunction",
    environment=config
)
```

### Kubernetes

**Export for Kubernetes:**
```bash
enveloper export -d prod --format yaml -o secrets.yaml
```

**Kubernetes Secret:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  KEY1: {{ env.KEY1 | b64enc }}
  KEY2: {{ env.KEY2 | b64enc }}
```

### CI/CD Configuration

**GitHub Actions:**
```yaml
- name: Export secrets
  run: |
    enveloper export -d prod --format dotenv > $GITHUB_ENV
```

**GitLab CI:**
```yaml
- name: Export secrets
  run: |
    eval "$(enveloper export -d prod --format unix)"
```

## Format Comparison

| Feature | JSON | YAML |
|---------|------|------|
| Readability | Good | Excellent |
| Comments | No | Yes |
| Nested data | Good | Excellent |
| Size | Smaller | Larger |
| Parsing speed | Faster | Slower |
| Type support | Limited | Better |

## Best Practices

1. **Use JSON for CI/CD** - Faster parsing, less ambiguity
2. **Use YAML for human editing** - More readable, supports comments
3. **Keep files versioned** - Track changes in git
4. **Validate before import** - Use `jq` or `yamllint`
5. **Use consistent structure** - Follow project conventions

## Validation

### JSON Validation

```bash
# Validate JSON syntax
jq . secrets.json

# Or use Python
python -m json.tool secrets.json
```

### YAML Validation

```bash
# Validate YAML syntax (requires PyYAML)
python -c "import yaml; yaml.safe_load(open('secrets.yaml'))"

# Or use yamllint
yamllint secrets.yaml
```

## Troubleshooting

### Invalid JSON

```bash
# Check for syntax errors
jq . secrets.json

# Common issues:
# - Trailing commas
# - Unquoted keys
# - Single quotes instead of double
```

### Invalid YAML

```bash
# Check indentation consistency
# YAML is sensitive to spacing

# Common issues:
# - Mixed tabs/spaces
# - Incorrect indentation
# - Unescaped special characters
```

### Format Mismatch

```bash
# Ensure format matches file type
enveloper import secrets.json --format json
enveloper import secrets.yaml --format yaml