# Professional Git Workflow - Setup Checklist

## Completed ✅

- [x] Renamed `master` → `main`
- [x] Created `nightly` branch
- [x] Updated nightly-build.yml to trigger on nightly
- [x] Created pr-validation.yml for main PRs
- [x] release-build.yml already configured for releases
- [x] All 14 tests passing
- [x] Documentation complete

## TO DO on GitHub Web UI

### 1. Set Default Branch
- [ ] Go to https://github.com/VoxLight/XLTickers/settings/branches
- [ ] Click the branch switcher icon
- [ ] Select `main` as default
- [ ] Confirm

### 2. Delete Old Master Branch
- [ ] Go to https://github.com/VoxLight/XLTickers/settings/branches
- [ ] Find `master` in list
- [ ] Click delete icon
- [ ] Confirm

### 3. (Optional) Set Branch Protection
- [ ] Go to https://github.com/VoxLight/XLTickers/settings/branches
- [ ] Click "Add rule"
- [ ] Branch pattern: `main`
- [ ] Check: ✅ Require pull request before merging
- [ ] Check: ✅ Require status checks to pass
- [ ] Select: `test (3.11)` from dropdown
- [ ] Check: ✅ Require branches up to date
- [ ] Check: ✅ Dismiss stale PR approvals
- [ ] Click "Create"

## Test the Workflow

### Test 1: Nightly Build
- [ ] Verify nightly-build.yml triggered on push
- [ ] Go to https://github.com/VoxLight/XLTickers/actions
- [ ] Look for "Nightly Build (Dev)" workflow
- [ ] Should show: ✅ Tests passed, ✅ Executable built
- [ ] Check https://github.com/VoxLight/XLTickers/releases/tag/nightly
- [ ] Should have nightly executable zipped

### Test 2: Create Production Release
- [ ] Go to https://github.com/VoxLight/XLTickers/releases
- [ ] Click "Create new release"
- [ ] Tag: `v1.0.0`
- [ ] Title: `XLTickers v1.0.0 - Phase 1.1 Release`
- [ ] Description: Copy from v1.0.0 release notes
- [ ] Click "Publish release"
- [ ] Watch workflow at Actions tab
- [ ] Should build installer (~10 mins)
- [ ] Verify download: `XLTickers-Installer.exe`

### Test 3: PR to Main
- [ ] Create feature branch from nightly
- [ ] Make a small change
- [ ] Push and create PR to main
- [ ] Watch pr-validation.yml run
- [ ] Should show: ✅ All tests passed
- [ ] Merge PR
- [ ] No build triggered (correct!)

## Verify Everything Works

### Nightly Branch
```bash
git checkout nightly
echo "Test" >> test.txt
git add test.txt
git commit -m "Test: verify nightly builds"
git push origin nightly

# Check GitHub Actions - should auto build
```

### Main Branch (PR Required)
```bash
git checkout main
git checkout -b test-feature
echo "Test" >> test.txt
git add test.txt
git commit -m "Test: verify PR validation"
git push origin test-feature

# Go to GitHub, create PR to main
# Should auto-run validation
# Tests should pass
```

### Release
```bash
# Go to GitHub releases
# Create new release: v1.0.1
# Watch Actions tab
# Should auto-build installer
```

## Documentation Files Created

- `GIT_WORKFLOW.md` - Complete workflow guide
- `BRANCH_PROTECTION.md` - Protection rules
- `WORKFLOW_SETUP_COMPLETE.md` - Setup summary
- `CI_CD_SETUP.md` - CI/CD configuration
- `CI_CD_RELEASE_SUMMARY.md` - Release reference

## Quick Reference

### Daily Development
```bash
# Get latest
git checkout nightly
git pull origin nightly

# Create feature
git checkout -b feature/my-feature

# Work and commit
git add .
git commit -m "Feature: description"
git push origin feature/my-feature

# On GitHub: Create PR to nightly
# Auto builds, test the nightly release
# Merge when ready
```

### Release to Production
```bash
# When nightly is stable, create PR: nightly → main
# Wait for tests to pass
# Merge to main
# Go to GitHub releases
# Create new release
# Tag: v1.0.1
# Publish
# Wait for installer build
# Done!
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't push to main | Use PR instead (correct!) |
| Nightly build didn't trigger | Push to nightly or create PR to nightly |
| PR validation won't run | Make sure PR is to main, not nightly |
| Release build failed | Check Actions logs, usually test failure |
| Installer missing from release | Wait longer (build takes ~10 mins) |

## Support

For questions about:
- **Git workflow**: See `GIT_WORKFLOW.md`
- **CI/CD setup**: See `CI_CD_SETUP.md`
- **Making releases**: See `CI_CD_RELEASE_SUMMARY.md`
- **Branch protection**: See `BRANCH_PROTECTION.md`

---

**Status**: Ready to proceed! ✅

Once you complete the GitHub web UI tasks above, your professional workflow is fully operational.

Next: Start working on GUI implementation using this stable branching strategy!
