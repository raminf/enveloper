# Copyright (c) 2026 Ramin Firoozye
# SPDX-License-Identifier: AGPL-3.0-or-later

# Makefile for building enveloper standalone binaries using cx_Freeze
# Supports macOS, Linux, and Windows with x86_64 and arm64 architectures
# cx_Freeze provides faster startup times than PyInstaller

SHELL := /bin/bash
.PHONY: help build-all build-mac build-linux build-win build-mac-x86 build-mac-arm build-mac-dmg test test-all sign sign-all upload upload-all release clean homebrew version init

# Configuration
VERSION := $(shell grep '^version = ' ../pyproject.toml | sed 's/.*"\([^"]*\)".*/\1/')
PROJECT_NAME := enveloper
PYTHON := python3
UV := uv

# Colors for output
BLUE := \033[1;34m
GREEN := \033[1;32m
RED := \033[1;31m
NC := \033[0m

help: ## Show this help message
	@printf "$(BLUE)enveloper Binary Build System (cx_Freeze)$(NC)\n"
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

# --- Initialization ---

init: ## Initialize the binary build environment (install dependencies and icon)
	@printf "$(BLUE)Initializing binary build environment...$(NC)\n"
	$(UV) sync
	@mkdir -p icon
	@if [ -f ../media/envelope.svg ]; then cp ../media/envelope.svg icon/; printf "$(GREEN)Copied icon from media/$(NC)\n"; fi
	@printf "$(GREEN)Environment initialized!$(NC)\n"

# --- Build Targets ---

build-all: init ## Build for all platforms (mac, linux, win) and architectures
	@printf "$(BLUE)Building for all platforms...$(NC)\n"
	$(PYTHON) build.py --platform all

build-mac: init ## Build for macOS (x86_64 and arm64)
	@printf "$(BLUE)Building for macOS...$(NC)\n"
	$(PYTHON) build.py --platform mac

build-linux: init ## Build for Linux (x86_64 and arm64)
	@printf "$(BLUE)Building for Linux...$(NC)\n"
	$(PYTHON) build.py --platform linux

build-win: init ## Build for Windows (x86_64 and arm64)
	@printf "$(BLUE)Building for Windows...$(NC)\n"
	$(PYTHON) build.py --platform win

build-mac-x86: init ## Build for macOS x86_64 only
	@printf "$(BLUE)Building for macOS x86_64...$(NC)\n"
	$(PYTHON) build.py --platform mac --arch x86_64

build-mac-arm: init ## Build for macOS arm64 only
	@printf "$(BLUE)Building for macOS arm64...$(NC)\n"
	$(PYTHON) build.py --platform mac --arch arm64

build-mac-dmg: init ## Build macOS .pkg and .dmg installer (run after build-mac or build-mac-arm)
	@printf "$(BLUE)Building macOS DMG installer...$(NC)\n"
	$(PYTHON) build.py --platform mac --dmg
	@printf "$(GREEN)DMG and PKG are in dist/$(NC)\n"

build-mac-arm-dmg: init ## Build macOS arm64 and then .pkg + .dmg installer
	@printf "$(BLUE)Building macOS arm64 and DMG installer...$(NC)\n"
	$(PYTHON) build.py --platform mac --arch arm64 --dmg
	@printf "$(GREEN)DMG: dist/enveloper-$(VERSION)-macos-arm64.dmg$(NC)\n"

build-linux-x86: init ## Build for Linux x86_64 only
	@printf "$(BLUE)Building for Linux x86_64...$(NC)\n"
	$(PYTHON) build.py --platform linux --arch x86_64

build-linux-arm: init ## Build for Linux arm64 only
	@printf "$(BLUE)Building for Linux arm64...$(NC)\n"
	$(PYTHON) build.py --platform linux --arch arm64

build-win-x86: init ## Build for Windows x86_64 only
	@printf "$(BLUE)Building for Windows x86_64...$(NC)\n"
	$(PYTHON) build.py --platform win --arch x86_64

build-win-arm: init ## Build for Windows arm64 only
	@printf "$(BLUE)Building for Windows arm64...$(NC)\n"
	$(PYTHON) build.py --platform win --arch arm64

# --- Test Targets ---

test: init ## Test all built binaries
	@printf "$(BLUE)Testing binaries...$(NC)\n"
	$(PYTHON) test.py

test-all: init ## Test all binaries (alias for test)
	@printf "$(BLUE)Testing all binaries...$(NC)\n"
	$(PYTHON) test.py

test-mac: init ## Test macOS binaries
	@printf "$(BLUE)Testing macOS binaries...$(NC)\n"
	$(PYTHON) test.py --platform mac

test-linux: init ## Test Linux binaries
	@printf "$(BLUE)Testing Linux binaries...$(NC)\n"
	$(PYTHON) test.py --platform linux

test-win: init ## Test Windows binaries
	@printf "$(BLUE)Testing Windows binaries...$(NC)\n"
	$(PYTHON) test.py --platform win

# --- Sign Targets ---

sign: init ## Sign all built binaries
	@printf "$(BLUE)Signing binaries...$(NC)\n"
	$(PYTHON) sign.py

sign-all: init ## Sign all binaries (alias for sign)
	@printf "$(BLUE)Signing all binaries...$(NC)\n"
	$(PYTHON) sign.py

sign-mac: init ## Sign macOS binaries
	@printf "$(BLUE)Signing macOS binaries...$(NC)\n"
	$(PYTHON) sign.py --platform mac

sign-win: init ## Sign Windows binaries
	@printf "$(BLUE)Signing Windows binaries...$(NC)\n"
	$(PYTHON) sign.py --platform win

# --- Upload Targets ---

upload: init ## Upload all binaries to GitHub Releases
	@printf "$(BLUE)Uploading binaries to GitHub Releases...$(NC)\n"
	$(PYTHON) upload.py

upload-all: init ## Upload all binaries (alias for upload)
	@printf "$(BLUE)Uploading all binaries...$(NC)\n"
	$(PYTHON) upload.py

upload-release: init ## Upload binaries to a specific release
	@printf "$(BLUE)Uploading to release...$(NC)\n"
	$(PYTHON) upload.py --release v$(VERSION)

# --- Release Targets ---

release: init build-all test-all sign upload ## Full release pipeline: build, test, sign, upload
	@printf "$(GREEN)Release complete!$(NC)\n"
	@echo "Version: $(VERSION)"
	@echo "Check GitHub Releases for your binaries."

release-mac: init build-mac test-mac sign-mac upload ## Release macOS binaries only
	@printf "$(GREEN)macOS release complete!$(NC)\n"

release-linux: init build-linux test-linux sign upload ## Release Linux binaries only
	@printf "$(GREEN)Linux release complete!$(NC)\n"

release-win: init build-win test-win sign upload ## Release Windows binaries only
	@printf "$(GREEN)Windows release complete!$(NC)\n"

# --- Homebrew Targets ---

homebrew: init ## Generate Homebrew formula
	@printf "$(BLUE)Generating Homebrew formula...$(NC)\n"
	$(PYTHON) homebrew.py --output ../$(PROJECT_NAME).rb
	@printf "$(GREEN)Formula written to ../$(PROJECT_NAME).rb$(NC)\n"

homebrew-check: init ## Check Homebrew formula (dry run)
	@printf "$(BLUE)Checking Homebrew formula...$(NC)\n"
	$(PYTHON) homebrew.py

# --- Utility Targets ---

version: ## Show current version
	@echo "Version: $(VERSION)"

clean: ## Clean build artifacts
	@printf "$(BLUE)Cleaning build artifacts...$(NC)\n"
	rm -rf build/
	rm -rf dist/
	rm -rf releases/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@printf "$(GREEN)Clean complete!$(NC)\n"

distclean: clean ## Clean everything including virtual environments
	@printf "$(BLUE)Cleaning everything...$(NC)\n"
	rm -rf .venv/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	@printf "$(GREEN)Distclean complete!$(NC)\n"

# --- Debug Targets ---

debug: ## Show debug information
	@printf "$(BLUE)Debug Information$(NC)\n"
	@echo "Version: $(VERSION)"
	@echo "Project: $(PROJECT_NAME)"
	@echo "Python: $(PYTHON)"
	@echo "Build Dir: build/"
	@echo "Dist Dir: dist/"
	@echo "Releases Dir: releases/"
	@ls -la dist/ 2>/dev/null || echo "No binaries built yet"

# --- CI/CD Targets ---

ci-build-all: init ## Build for CI/CD (all platforms)
	$(PYTHON) build.py --platform all

ci-test-all: init ## Test for CI/CD (all platforms)
	$(PYTHON) test.py

ci-release: init ## Full CI/CD release pipeline
	$(PYTHON) build.py --platform all
	$(PYTHON) test.py
	$(PYTHON) sign.py
	$(PYTHON) upload.py --release v$(VERSION)