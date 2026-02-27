# Makefile Integration

## Overview

`enveloper` integrates seamlessly with Makefiles, providing a clean way to manage secrets in your build process.

## Basic Integration

### Three-Tier Fallback

The recommended approach uses a three-tier fallback system:

1. **CI environment variables** (highest priority)
2. **enveloper** (medium priority)
3. **.env file** (lowest priority)

```makefile
# Three-tier fallback: CI env vars > enveloper > .env file
ifneq ($(CI),)
  # CI: env vars pre-set
else ifneq ($(shell command -v enveloper 2>/dev/null),)
  $(shell enveloper export -d prod --format dotenv > /tmp/.enveloper-$(USER).env 2>/dev/null)
  -include /tmp/.enveloper-$(USER).env
else ifneq (,$(wildcard .env))
  -include .env
endif
export
```

### Simple Integration

For simpler projects:

```makefile
# Load secrets from enveloper
include /tmp/.enveloper.env

# Generate secrets file
/tmp/.enveloper.env:
	@enveloper export -d prod --format dotenv > $@

# Clean up
clean:
	rm -f /tmp/.enveloper.env
```

## Advanced Integration

### Project-Specific Configuration

```makefile
# Project settings
PROJECT ?= myapp
DOMAIN ?= prod
SERVICE ?= local

# Load secrets
-include /tmp/.enveloper-$(PROJECT)-$(DOMAIN).env

# Generate secrets
/tmp/.enveloper-$(PROJECT)-$(DOMAIN).env:
	@enveloper export -d $(DOMAIN) --service $(SERVICE) --format dotenv > $@

# Clean up
.PHONY: clean
clean:
	rm -f /tmp/.enveloper-$(PROJECT)-$(DOMAIN).env
```

### Environment-Specific Targets

```makefile
# Environment targets
dev:
	$(MAKE) build DOMAIN=dev

staging:
	$(MAKE) build DOMAIN=staging

prod:
	$(MAKE) build DOMAIN=prod

# Build target
build:
	@echo "Building for $(DOMAIN) environment"
	@echo "DATABASE_URL=$(DATABASE_URL)"
	@make -f Makefile.build
```

### Conditional Loading

```makefile
# Check if enveloper is available
HAS_ENVELOPER := $(shell command -v enveloper 2>/dev/null)

# Load secrets if available
ifeq ($(HAS_ENVELOPER),)
  # enveloper not available, use .env file
  -include .env
else
  # enveloper available, use it
  $(shell enveloper export -d prod --format dotenv > /tmp/.enveloper.env 2>/dev/null)
  -include /tmp/.enveloper.env
endif
export
```

## Common Patterns

### Database Migration

```makefile
# Database migration with secrets
migrate:
	@echo "Running database migration..."
	@export DATABASE_URL=$(DATABASE_URL) && \
		python -m alembic upgrade head

# Or using enveloper directly
migrate:
	@eval "$$(enveloper export -d prod --format unix)"
	@python -m alembic upgrade head
```

### Testing

```makefile
# Run tests with secrets
test:
	@eval "$$(enveloper export -d test --format unix)"
	@pytest tests/

# Or with specific service
test-aws:
	@eval "$$(enveloper export -d test --service aws --format unix)"
	@pytest tests/
```

### Docker Build

```makefile
# Build with secrets
docker-build:
	@eval "$$(enveloper export -d prod --format unix)"
	@docker build --build-arg DATABASE_URL=$$DATABASE_URL \
		--build-arg API_KEY=$$API_KEY \
		-t myapp:latest .

# Or using .env file
docker-build:
	@enveloper export -d prod --format dotenv > .env.docker
	@docker build --env-file .env.docker -t myapp:latest .
	@rm -f .env.docker
```

### Deployment

```makefile
# Deploy with secrets
deploy:
	@eval "$$(enveloper export -d prod --format unix)"
	@aws ecs update-service \
		--cluster myapp \
		--service myapp \
		--force-new-deployment

# Or using GitHub Actions
deploy:
	@enveloper push --service github -d prod --repo owner/repo
```

## Complete Example

```makefile
# Makefile with enveloper integration

# Project settings
PROJECT ?= myapp
DOMAIN ?= prod
SERVICE ?= local

# Three-tier fallback
ifneq ($(CI),)
  # CI: env vars pre-set
else ifneq ($(shell command -v enveloper 2>/dev/null),)
  $(shell enveloper export -d $(DOMAIN) --service $(SERVICE) --format dotenv > /tmp/.enveloper-$(USER).env 2>/dev/null)
  -include /tmp/.enveloper-$(USER).env
else ifneq (,$(wildcard .env))
  -include .env
endif
export

# Targets
.PHONY: all
all: build

.PHONY: build
build:
	@echo "Building $(PROJECT) for $(DOMAIN)..."
	@echo "DATABASE_URL=$(DATABASE_URL)"
	@make -f Makefile.build

.PHONY: test
test:
	@eval "$$(enveloper export -d test --format unix)"
	@pytest tests/

.PHONY: deploy
deploy:
	@eval "$$(enveloper export -d prod --format unix)"
	@aws ecs update-service \
		--cluster $(PROJECT) \
		--service $(PROJECT) \
		--force-new-deployment

.PHONY: clean
clean:
	rm -f /tmp/.enveloper-$(USER).env
```

## Best Practices

1. **Use environment-specific domains** - Separate dev, staging, prod
2. **Clean up temp files** - Remove generated .env files
3. **Handle missing secrets** - Provide fallback values
4. **Use CI detection** - Different behavior in CI vs local
5. **Document secrets** - Keep .env.example in repo

## Troubleshooting

### Secret Not Found

```makefile
# Check if secret exists
check-secrets:
	@if [ -z "$(DATABASE_URL)" ]; then \
		echo "DATABASE_URL not set"; \
		exit 1; \
	fi
```

### Enveloper Not Available

```makefile
# Check if enveloper is installed
check-enveloper:
	@command -v enveloper >/dev/null 2>&1 || { \
		echo "enveloper not installed. Install with: pip install enveloper"; \
		exit 1; \
	}
```

### Permission Denied

```makefile
# Check credentials
check-credentials:
	@aws sts get-caller-identity || { \
		echo "AWS credentials not set"; \
		exit 1; \
	}