# CI/CD Integration

## Overview

`enveloper` integrates seamlessly with various CI/CD platforms, enabling secure secret management in automated workflows.

## GitHub Actions

### Basic Workflow

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install enveloper
        run: pip install enveloper[aws]
        
      - name: Pull secrets from AWS SSM
        run: |
          enveloper pull --service aws -d prod --prefix /myapp/prod/
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          
      - name: Export secrets for build
        run: |
          eval "$(enveloper export -d prod --format unix)"
          
      - name: Build application
        run: make build
```

### Using GitHub Secrets Directly

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Push to GitHub Secrets
        run: |
          enveloper push --service github -d prod --repo ${{ github.repository }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Use secrets in workflow
        run: |
          echo "Using GitHub secret: ${{ secrets.MY_KEY }}"
```

### Self-Hosted Runner with Keychain

```yaml
name: Build with Keychain

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      
      - name: Export secrets from keychain
        run: |
          enveloper export -d prod --format dotenv > /tmp/.enveloper.env
          source /tmp/.enveloper.env
          
      - name: Build application
        run: make build
```

## AWS CodeBuild

### Using SSM Parameters

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.11
    commands:
      - pip install enveloper[aws]
      
  pre_build:
    commands:
      - |
        # Pull secrets from SSM
        enveloper pull --service aws -d prod --prefix /myapp/prod/
        
      - |
        # Generate CodeBuild environment snippet
        enveloper generate codebuild-env -d prod --prefix /myapp/prod/
        
  build:
    commands:
      - make build
```

### Using Environment Variables

```yaml
version: 0.2

phases:
  build:
    commands:
      - pip install enveloper
      - eval "$(enveloper export -d prod --format unix)"
      - make build
    environment:
      ENVELOPER_PROJECT: myapp
      ENVELOPER_DOMAIN: prod
      ENVELOPER_SERVICE: local
```

## GitLab CI

### Basic Workflow

```yaml
stages:
  - build
  - test
  - deploy

variables:
  ENVELOPER_PROJECT: myapp
  ENVELOPER_DOMAIN: prod

build:
  stage: build
  image: python:3.11
  script:
    - pip install enveloper[aws]
    - export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
    - export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
    - enveloper pull --service aws
    - eval "$(enveloper export --format unix)"
    - make build
  variables:
    AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
```

### Using GitLab CI Variables

```yaml
deploy:
  stage: deploy
  image: python:3.11
  script:
    - pip install enveloper
    - enveloper push --service github -d prod --repo $CI_PROJECT_PATH
    - GITHUB_TOKEN=$CI_JOB_TOKEN
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

## Azure DevOps

### YAML Pipeline

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  ENVELOPER_PROJECT: myapp
  ENVELOPER_DOMAIN: prod

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'
      
  - script: pip install enveloper[aws]
    displayName: 'Install enveloper'
    
  - script: |
      export AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID)
      export AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY)
      enveloper pull --service aws
      eval "$(enveloper export --format unix)"
    displayName: 'Pull and export secrets'
    
  - script: make build
    displayName: 'Build application'
```

## Jenkins

### Pipeline Script

```groovy
pipeline {
    agent any
    environment {
        ENVELOPER_PROJECT = 'myapp'
        ENVELOPER_DOMAIN = 'prod'
        AWS_ACCESS_KEY_ID = credentials('aws-access-key')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-key')
    }
    stages {
        stage('Install') {
            steps {
                sh 'pip install enveloper[aws]'
            }
        }
        stage('Pull Secrets') {
            steps {
                sh '''
                    enveloper pull --service aws
                    eval "$(enveloper export --format unix)"
                '''
            }
        }
        stage('Build') {
            steps {
                sh 'make build'
            }
        }
    }
}
```

## Docker / Docker Compose

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install enveloper
RUN pip install enveloper[aws]

# Set environment
ENV ENVELOPER_PROJECT=myapp
ENV ENVELOPER_DOMAIN=prod

# Copy application
COPY . /app
WORKDIR /app

# Run with secrets
CMD ["sh", "-c", "eval \"\$(enveloper export --format unix)\" && python app.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY}
```

## Best Practices

1. **Use environment-specific secrets** - Separate dev, staging, prod
2. **Rotate credentials regularly** - Update secrets in CI/CD
3. **Use secrets management** - Store CI/CD credentials securely
4. **Audit access** - Track who accessed secrets
5. **Fail securely** - Don't expose secrets in logs

## Troubleshooting

### Permission Denied

```bash
# Check credentials
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:4}..."

# Verify IAM permissions
aws sts get-caller-identity
```

### Connection Issues

```bash
# Test network connectivity
ping ssm.<region>.amazonaws.com

# Check firewall rules
curl -v https://ssm.<region>.amazonaws.com
```

### Secret Not Found

```bash
# Verify secret exists
enveloper list

# Check project/domain
enveloper list --project myapp --domain prod