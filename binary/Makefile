# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

# Makefile for building enveloper standalone binaries
# Supports macOS, Linux, and Windows with x86_64 and arm64 architectures

SHELL := /bin/bash
.PHONY: help build-all build-mac build-linux build-win build-mac-x86 build-mac-arm build-linux-deb build-linux-rpm build-win-x86 build-win-arm test test-all sign sign-all upload upload-all release clean homebrew version

# Configuration
VERSION := $(shell grep '^version = ' ../pyproject.toml | sed 's/.*"\([^"]*\)".*/\1/')
PROJECT_NAME := enveloper
PYTHON := python3

# Colors for output
BLUE := \033[1;34m
GREEN := \033[1;32m
RED := \033[1;31m
NC := \033[0m

help: ## Show this help message
	@echo "$(BLUE)enveloper Binary Build System$(NC)"
	@echo "Version: $(VERSION)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Environment Variables:"
	@echo "  GITHUB_TOKEN    GitHub token for uploading releases"
	@echo "  MAC_CERT_IDENTITY macOS code signing identity"
	@echo "  WIN_CERT_PATH   Windows certificate path (.pfx)"
	@echo ""

# --- Build Targets ---

build-all: ## Build for all platforms (mac, linux, win) and architectures
	@echo "$(BLUE)Building for all platforms...$(NC)"
	$(PYTHON) build.py --platform all

build-mac: ## Build for macOS (x86_64 and arm64)
	@echo "$(BLUE)Building for macOS...$(NC)"
	$(PYTHON) build.py --platform mac

build-linux: ## Build for Linux (x86_64 and arm64)
	@echo "$(BLUE)Building for Linux...$(NC)"
	$(PYTHON) build.py --platform linux

build-win: ## Build for Windows (x86_64 and arm64)
	@echo "$(BLUE)Building for Windows...$(NC)"
	$(PYTHON) build.py --platform win

build-mac-x86: ## Build for macOS x86_64 only
	@echo "$(BLUE)Building for macOS x86_64...$(NC)"
	$(PYTHON) build.py --platform mac --arch x86_64

build-mac-arm: ## Build for macOS arm64 only
	@echo "$(BLUE)Building for macOS arm64...$(NC)"
	$(PYTHON) build.py --platform mac --arch arm64

build-linux-x86: ## Build for Linux x86_64 only
	@echo "$(BLUE)Building for Linux x86_64...$(NC)"
	$(PYTHON) build.py --platform linux --arch x86_64

build-linux-arm: ## Build for Linux arm64 only
	@echo "$(BLUE)Building for Linux arm64...$(NC)"
	$(PYTHON) build.py --platform linux --arch arm64

build-win-x86: ## Build for Windows x86_64 only
	@echo "$(BLUE)Building for Windows x86_64...$(NC)"
	$(PYTHON) build.py --platform win --arch x86_64

build-win-arm: ## Build for Windows arm64 only
	@echo "$(BLUE)Building for Windows arm64...$(NC)"
	$(PYTHON) build.py --platform win --arch arm64

# --- Test Targets ---

test: ## Test all built binaries
	@echo "$(BLUE)Testing binaries...$(NC)"
	$(PYTHON) test.py

test-all: ## Test all binaries (alias for test)
	@echo "$(BLUE)Testing all binaries...$(NC)"
	$(PYTHON) test.py

test-mac: ## Test macOS binaries
	@echo "$(BLUE)Testing macOS binaries...$(NC)"
	$(PYTHON) test.py --platform mac

test-linux: ## Test Linux binaries
	@echo "$(BLUE)Testing Linux binaries...$(NC)"
	$(PYTHON) test.py --platform linux

test-win: ## Test Windows binaries
	@echo "$(BLUE)Testing Windows binaries...$(NC)"
	$(PYTHON) test.py --platform win

# --- Sign Targets ---

sign: ## Sign all built binaries
	@echo "$(BLUE)Signing binaries...$(NC)"
	$(PYTHON) sign.py

sign-all: ## Sign all binaries (alias for sign)
	@echo "$(BLUE)Signing all binaries...$(NC)"
	$(PYTHON) sign.py

sign-mac: ## Sign macOS binaries
	@echo "$(BLUE)Signing macOS binaries...$(NC)"
	$(PYTHON) sign.py --platform mac

sign-win: ## Sign Windows binaries
	@echo "$(BLUE)Signing Windows binaries...$(NC)"
	$(PYTHON) sign.py --platform win

# --- Upload Targets ---

upload: ## Upload all binaries to GitHub Releases
	@echo "$(BLUE)Uploading binaries to GitHub Releases...$(NC)"
	$(PYTHON) upload.py

upload-all: ## Upload all binaries (alias for upload)
	@echo "$(BLUE)Uploading all binaries...$(NC)"
	$(PYTHON) upload.py

upload-release: ## Upload binaries to a specific release
	@echo "$(BLUE)Uploading to release...$(NC)"
	$(PYTHON) upload.py --release v$(VERSION)

# --- Release Targets ---

release: build-all test-all sign upload ## Full release pipeline: build, test, sign, upload
	@echo "$(GREEN)Release complete!$(NC)"
	@echo "Version: $(VERSION)"
	@echo "Check GitHub Releases for your binaries."

release-mac: build-mac test-mac sign-mac upload ## Release macOS binaries only
	@echo "$(GREEN)macOS release complete!$(NC)"

release-linux: build-linux test-linux sign upload ## Release Linux binaries only
	@echo "$(GREEN)Linux release complete!$(NC)"

release-win: build-win test-win sign upload ## Release Windows binaries only
	@echo "$(GREEN)Windows release complete!$(NC)"

# --- Homebrew Targets ---

homebrew: ## Generate Homebrew formula
	@echo "$(BLUE)Generating Homebrew formula...$(NC)"
	$(PYTHON) homebrew.py --output ../$(PROJECT_NAME).rb
	@echo "$(GREEN)Formula written to ../$(PROJECT_NAME).rb$(NC)"

homebrew-check: ## Check Homebrew formula (dry run)
	@echo "$(BLUE)Checking Homebrew formula...$(NC)"
	$(PYTHON) homebrew.py

# --- Utility Targets ---

version: ## Show current version
	@echo "Version: $(VERSION)"

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf releases/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

distclean: clean ## Clean everything including virtual environments
	@echo "$(BLUE)Cleaning everything...$(NC)"
	rm -rf .venv/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	@echo "$(GREEN)Distclean complete!$(NC)"

# --- Debug Targets ---

debug: ## Show debug information
	@echo "$(BLUE)Debug Information$(NC)"
	@echo "Version: $(VERSION)"
	@echo "Project: $(PROJECT_NAME)"
	@echo "Python: $(PYTHON)"
	@echo "Build Dir: build/"
	@echo "Dist Dir: dist/"
	@echo "Releases Dir: releases/"
	@ls -la dist/ 2>/dev/null || echo "No binaries built yet"

# --- CI/CD Targets ---

ci-build-all: ## Build for CI/CD (all platforms)
	$(PYTHON) build.py --platform all

ci-test-all: ## Test for CI/CD (all platforms)
	$(PYTHON) test.py

ci-release: ## Full CI/CD release pipeline
	$(PYTHON) build.py --platform all
	$(PYTHON) test.py
	$(PYTHON) sign.py
	$(PYTHON) upload.py --release v$(VERSION)