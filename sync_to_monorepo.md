# Ntfy Lite: Monorepo Sync Guide

This document describes the workflow for keeping the standalone `ntfy_lite` repository in sync with the `dll-danda-ibp-scripts` monorepo.

> [!IMPORTANT]
> This fork has been restructured to a clean top-level package (`ntfy_lite`). When syncing back to the monorepo, ensure you are merging into the `libs/ntfy_lite` directory.

## 1. Prerequisites
You should have both repositories cloned locally and configured as remotes in your working environment.

In your **monorepo** folder:
```bash
git remote add ntfy_standalone https://github.com/MCRE-BE/ntfy_lite.git
```

## 2. Pushing Changes to Monorepo
To push changes from this standalone repository back into the monorepo's subfolder:

1.  In the **monorepo**, pull the latest changes from the standalone repo:
    ```bash
    git subtree pull --prefix=libs/ntfy_lite ntfy_standalone master --squash
    ```
2.  Resolve any conflicts and commit.

## 3. Pulling Changes from Monorepo
If changes are made to `libs/ntfy_lite` inside the monorepo and you want to bring them here:

1.  In the **monorepo**, push the subfolder changes to a temporary branch:
    ```bash
    git subtree push --prefix=libs/ntfy_lite ntfy_standalone feature/from-monorepo
    ```
2.  In **this standalone repo**, merge that branch:
    ```bash
    git fetch origin
    git merge feature/from-monorepo
    ```

## 4. Modernization Note
Since the standalone version has moved away from the `dll_etl` intermediate folder, the `git subtree` commands might require path adjustments if the monorepo hasn't been restructured yet. Once the monorepo is restructured to match this repo's vertical history, the commands above will work seamlessly.
