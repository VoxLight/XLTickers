# Branch Protection Rules Configuration

This document describes the branch protection rules for XLTickers GitHub repository.

## Main Branch Protection

To enable branch protection for the `main` branch:

1. Go to: https://github.com/VoxLight/XLTickers/settings/branches

2. Add rule for `main` branch with:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (1 or more)
   - ✅ Require status checks to pass:
     - `test (3.11)` (PR Validation workflow)
   - ✅ Require branches to be up to date before merging
   - ✅ Dismiss stale pull request approvals
   - ✅ Require code owner reviews
   - ✅ Restrict who can push to matching branches (admins only)

3. Nightly branch:
   - Allow direct commits
   - No PR required
   - Builds on every push

## Workflow Summary

```
Developer → Feature Branch → PR to nightly → Auto build nightly
Maintainer → PR to main → Run tests → Approve → Merge → Triggers release
Release Manager → Create GitHub Release → Auto builds installer
```

## How to Contribute

1. Create feature branch from `nightly`
2. Commit and push to your branch
3. Create PR to `nightly`
4. PR automatically triggers nightly build
5. Test the build
6. Once stable, PR from `nightly` to `main`
7. Must pass all tests and get approval
8. Once merged to main, can create release

## Automation

- **Nightly commits**: Auto build (test + executable)
- **Main PRs**: Auto validate (tests only)
- **Main merges**: Ready for release creation
- **Release creation**: Auto builds installer
