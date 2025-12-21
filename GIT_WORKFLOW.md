# Git Branching Strategy - Complete Setup

**Status**: ✅ CONFIGURED AND READY

---

## Branch Structure

### `main` (Stable Release)
- **Purpose**: Production-ready code
- **Direct commits**: ❌ NOT ALLOWED (PR only)
- **Who can merge**: Approved PRs only
- **Releases**: Create releases from this branch
- **CI/CD**: PR validation (tests run on PR)
- **Installer builds**: Trigger on release creation

### `nightly` (Development/Testing)
- **Purpose**: Latest development code with new features
- **Direct commits**: ✅ ALLOWED
- **Auto builds**: Yes, on every push or PR
- **Release type**: Pre-release (nightly tag)
- **CI/CD**: Automatic on every commit
- **Installer builds**: No installer, just executable

### Feature Branches (as needed)
- **Naming**: `feature/my-feature`, `bugfix/issue-name`, etc.
- **Branches from**: `nightly`
- **PR to**: `nightly`
- **CI/CD**: Automatic build on PR

---

## Workflow Diagram

```
Feature Development:
  Feature Branch
       ↓
    Commit
       ↓
  PR to nightly → Auto build (test + exe)
       ↓
  Merge to nightly → Auto build (nightly release)
       ↓
  Ready for production?
       ↓ YES
   PR to main → Auto test validation
       ↓
  Code review & approval
       ↓
  Merge to main → No build (not yet released)
       ↓
  Create release tag (v1.0.1)
       ↓
  Auto build installer → Upload to release
       ↓
  Users download XLTickers-Installer.exe
```

---

## GitHub Actions Workflows

| Workflow | Trigger | Action | Output |
|----------|---------|--------|--------|
| `nightly-build.yml` | Push/PR to `nightly` | Test + build exe | Nightly pre-release |
| `pr-validation.yml` | PR to `main` | Run tests | Pass/fail comment on PR |
| `release-build.yml` | Create GitHub release | Build exe + installer | Release with .exe and .zip |

---

## How to Use

### Option 1: Small Changes (Direct to nightly)

```bash
git checkout nightly
git pull origin nightly

# Make changes
git add .
git commit -m "Fix: small bug fix"
git push origin nightly

# GitHub Actions auto-builds nightly release
```

### Option 2: Features (Feature Branch → nightly → main)

```bash
# Create feature branch
git checkout nightly
git pull origin nightly
git checkout -b feature/my-feature

# Make changes
git add .
git commit -m "Feature: add new capability"
git push origin feature/my-feature

# Create PR on GitHub: feature/my-feature → nightly
# Auto build runs, test the nightly executable
# Once tested and approved, merge to nightly

# Later, when ready for production:
# Create PR: nightly → main
# Must pass tests and get approval
# Merge to main
# Create release tag from main
# Auto build creates installer
```

### Option 3: Release (Create release from main)

```bash
# Everything is merged to main already
# Go to GitHub Releases
# Click "Create new release"
# Tag: v1.0.1
# Title: XLTickers v1.0.1
# Description: Release notes
# Publish

# GitHub Actions auto-builds installer
# Users can download from releases page
```

---

## Branch Protection Details

### What's Blocked on `main`

- ❌ Direct commits (no `git push` directly)
- ❌ Force pushes
- ❌ Merging without PR
- ❌ Merging without tests passing
- ❌ Merging without approval

### How to Add to `main` (Only Way)

1. Create PR to `main`
2. Tests auto-run (pr-validation.yml)
3. Must pass tests
4. Must get code review
5. Request approval
6. Maintainer approves and merges

### What's Allowed on `nightly`

- ✅ Direct commits
- ✅ Force pushes
- ✅ Rapid iteration
- ✅ Experimental features
- ✅ Auto builds on every change

---

## Setting Up Branch Protection

**To set branch protection rules (if not already done):**

1. Go to: https://github.com/VoxLight/XLTickers/settings/branches

2. Click "Add rule"

3. Branch name pattern: `main`

4. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - Select: `test (3.11)` workflow
   - ✅ Require branches to be up to date before merging
   - ✅ Dismiss stale pull request approvals
   - ✅ Restrict who can push (Optional)

5. Save

---

## CI/CD Pipeline Summary

### Nightly Branch (Dev Cycle)
```
Push to nightly
    ↓
nightly-build.yml runs
    ↓
Tests run
    ↓
PyInstaller builds exe
    ↓
Upload to GitHub Releases (nightly pre-release)
    ↓
Users can test latest dev build
```

### PR to Main (QA Cycle)
```
Create PR: ? → main
    ↓
pr-validation.yml runs
    ↓
Tests run (auto-comment results)
    ↓
If passed → Approve and merge
    ↓
No build triggered (not released yet)
```

### Release (Production Cycle)
```
Create release tag (v1.0.1)
    ↓
release-build.yml runs
    ↓
Tests run (full suite)
    ↓
PyInstaller builds exe
    ↓
NSIS builds installer
    ↓
Upload to GitHub Releases
    ↓
Users download installer
```

---

## Typical Day-to-Day Workflow

### Developer Working on Feature

```bash
# Start
git checkout nightly
git pull origin nightly
git checkout -b feature/cool-thing

# Work on feature
# ... make changes ...
git add .
git commit -m "Add cool feature"

# Push to GitHub
git push origin feature/cool-thing

# Create PR on GitHub
# → PR auto builds, tests
# → You test the build
# → Get approval
# → Merge to nightly

# Continue next day
git checkout nightly
git pull origin nightly
git checkout -b feature/next-thing
```

### Release Manager (Once a week)

```bash
# Create PR from nightly → main
# Review and merge (tests auto-pass)

# Create release
# Go to GitHub Releases
# Create new release v1.0.X
# Publish

# Auto build creates installer
# Update announcement/changelog
# Done!
```

---

## File Structure

```
.github/workflows/
├── nightly-build.yml      (Trigger: push/PR to nightly)
├── pr-validation.yml      (Trigger: PR to main)
└── release-build.yml      (Trigger: GitHub release)

Main files:
├── main.py               (Entry point)
├── core/                 (Core modules)
├── libs/                 (Library adapters)
├── scripts/              (Scripts for updates)
└── tests/                (Test suite)
```

---

## Next Steps

1. ✅ **GitHub Settings**:
   - Set `main` as default branch
   - Delete `master` branch
   - (Optional) Set branch protection rules

2. ✅ **Test the Workflow**:
   - Push a small change to `nightly`
   - Watch GitHub Actions build
   - Verify nightly release created

3. ✅ **First Main PR**:
   - Create PR: `nightly` → `main`
   - Watch tests run
   - Merge when green

4. ✅ **First Production Release**:
   - Go to Releases
   - Create v1.0.0
   - Watch installer build
   - Download and test

---

## Troubleshooting

### Can't push to main directly
**This is correct!** Use PR instead:
1. Create feature branch
2. PR to main
3. Tests run
4. Get approval
5. Merge

### Build failed on nightly
- Check GitHub Actions log
- Fix locally on feature branch
- Push again
- PR to nightly
- Auto rebuilds

### Can't merge PR to main
- Tests must pass (check pr-validation.yml)
- Needs approval
- Must be up to date with main

### Release didn't trigger build
- Must create release from web UI
- Tag must match format (v1.0.0)
- Release must be published (not draft)

---

## Key Takeaways

| Item | Nightly | Main |
|------|---------|------|
| **Stability** | Testing | Stable |
| **Direct commits** | ✅ Yes | ❌ No |
| **Auto build** | Every push | On release |
| **Release type** | Pre-release | Production |
| **Protection** | None | Full protection |
| **Update channel** | nightly | production |

---

**You now have a professional Git workflow!** 🚀

- Developers can commit freely to nightly
- Main branch is protected
- All changes validated by tests
- Releases are automated
- Clear separation of concerns
