# Qwen Ecosystem Repository Setup and Maintenance Guide

## Overview

This document describes the setup and maintenance procedures for the qwen-ecosystem repository, which serves as a meta-repository containing multiple UTCP-related projects as git submodules.

## Repository Structure

The repository follows this structure:

- `.bootstrap/` - Bootstrap package for meta-systems ecosystem implementation
- `.utcp-kb/` - Knowledge base focused on UTCP, created from upstream clones and optimized for AI
- `UPSTREAM/` - Local upstream clones of relevant remote repositories (managed as git submodules)
- `.gitignore` - Comprehensive ignore file to exclude large files and temporary data
- `.gitmodules` - Configuration file for git submodules

## Git Workflow

This repository uses Git Flow branching model:

- `master` - Production-ready code
- `develop` - Development branch
- `feature/*` - Feature branches
- `release/*` - Release preparation branches
- `hotfix/*` - Hotfix branches

## Git Submodules Management

The UPSTREAM directory contains git submodules that track the upstream repositories. Here are common operations:

### Initialize Submodules After Cloning

```bash
git clone https://github.com/jcmrs/qwen-ecosystem.git
cd qwen-ecosystem
git submodule update --init --recursive
```

### Update All Submodules to Latest Commit

```bash
git submodule update --remote --merge
```

### Update Specific Submodule

```bash
cd UPSTREAM/<repository-name>
git pull origin main  # or master, depending on the repository
cd ../..  # return to main repository
git add UPSTREAM/<repository-name>
git commit -m "Update submodule <repository-name>"
```

### Add New Submodule

```bash
git submodule add <repository-url> UPSTREAM/<repository-name>
git commit -m "Add submodule <repository-name>"
```

## Repository Maintenance

### Handling Large Files

The `.gitignore` file is configured to exclude large files from the knowledge base:

- `.utcp-kb/ai-optimized/` - AI-optimized data files
- `.utcp-kb/processed-knowledge/` - Processed knowledge files
- `.utcp-kb/raw-extractions/` - Raw extraction files

These files should NOT be committed to git as they can be very large and change frequently.

### Updating UPSTREAM Repositories

To update all UPSTREAM repositories to their latest versions:

```bash
# Update all submodules to latest remote commits
git submodule foreach git pull origin main

# Commit the updated submodule references
git add .
git commit -m "Update all submodules to latest"
git push origin develop
```

## Automation Scripts

The repository includes a script for managing upstream repositories:

- `UPSTREAM/manage_upstream.py` - Python script for managing upstream repositories

## Development Workflow

1. Create a feature branch:
   ```bash
   git flow feature start <feature-name>
   ```

2. Make your changes, being careful not to commit large files

3. Commit your changes:
   ```bash
   git add <files>
   git commit -m "Description of changes"
   ```

4. Finish the feature:
   ```bash
   git flow feature finish <feature-name>
   ```

5. Push to the remote repository:
   ```bash
   git push origin develop
   ```

## CI/CD Integration

The repository is configured for continuous integration. When pushing changes:

1. Ensure all tests pass before pushing
2. Update submodules if necessary
3. Update documentation if APIs or interfaces change
4. Create pull requests for code review when appropriate

## Troubleshooting

### Submodule Issues

If submodules appear as empty directories after cloning:

```bash
git submodule update --init --recursive
```

### Large File Warnings

If you receive large file warnings during push, check your `.gitignore` settings and remove the files from git history:

```bash
git rm --cached <large-file-path>
git commit -m "Remove large file from history"
```

### Syncing Forks

If maintaining a fork of this repository:

```bash
git remote add upstream https://github.com/jcmrs/qwen-ecosystem.git
git fetch upstream
git checkout develop
git merge upstream/develop
```

## Best Practices

1. Always update submodules when updating dependencies
2. Don't commit large binary files or processed data
3. Use feature branches for new development
4. Keep the bootstrap and knowledge base directories organized
5. Regularly sync with upstream repositories to stay current
6. Document significant changes in the README.md file