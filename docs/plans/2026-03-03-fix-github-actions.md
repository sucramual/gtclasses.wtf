# Fix GitHub Actions Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all failing GitHub Actions workflows so CI passes consistently on every push to main.

**Architecture:** Two independent file changes (ci.yml and format-checker.yml) can be done in parallel worktrees and merged. The deploy workflow already uses up-to-date actions.

**Tech Stack:** GitHub Actions YAML, Go 1.22, Yarn 1.22, Node.js 18

---

## Root Causes Identified

| Workflow             | Problem                                      | Impact                                     |
| -------------------- | -------------------------------------------- | ------------------------------------------ |
| `ci.yml`             | Uses `npm ci` on a Yarn project              | Frontend build fails / installs wrong deps |
| `ci.yml`             | `actions/checkout@v2` — Node.js 12 EOL       | Workflow error on modern runners           |
| `ci.yml`             | `actions/setup-go@v3`, `setup-node@v3` — old | Deprecation warnings / failures            |
| `ci.yml`             | Go version `"1.20"` inconsistent with rest   | Minor inconsistency                        |
| `format-checker.yml` | `actions/checkout@v3` — slightly old         | Runner warnings                            |

---

### Task 1: Fix ci.yml — Go job

**Files:**

- Modify: `.github/workflows/ci.yml` (lines 13–24, the `go` job)

**Step 1: Apply the changes**

Replace the `go` job's steps with:

```yaml
jobs:
  go:
    name: Go build
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: "1.22"

      - run: go build
```

**Step 2: Verify the YAML is valid**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "YAML OK"
```

Expected: `YAML OK`

---

### Task 2: Fix ci.yml — Frontend job

**Files:**

- Modify: `.github/workflows/ci.yml` (lines 26–43, the `web` job)

**Step 1: Replace the web job steps**

```yaml
web:
  name: Frontend build
  runs-on: ubuntu-latest

  steps:
    - uses: actions/checkout@v4

    - uses: actions/setup-node@v4
      with:
        node-version: "18"

    - run: yarn install --frozen-lockfile

    - run: yarn format:check

    - run: yarn check

    - run: yarn build
```

**Step 2: Verify YAML is valid**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "YAML OK"
```

Expected: `YAML OK`

---

### Task 3: Fix ci.yml — Deploy job checkout

**Files:**

- Modify: `.github/workflows/ci.yml` (lines 45–61, the `deploy` job)

**Step 1: Update checkout in deploy job**

```yaml
deploy:
  name: Deploy
  runs-on: ubuntu-latest
  if: contains(fromJSON('["push", "workflow_dispatch"]'), github.event_name) && github.ref == 'refs/heads/main'
  needs: [go, web]
  concurrency:
    group: deploy
    cancel-in-progress: false

  steps:
    - uses: actions/checkout@v4

    - uses: superfly/flyctl-actions@master
      env:
        FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
      with:
        args: deploy --remote-only
```

---

### Task 4: Fix format-checker.yml — Update checkout

**Files:**

- Modify: `.github/workflows/format-checker.yml`

**Step 1: Update checkout version and add Go setup**

```yaml
name: Format checker
on: push
jobs:
  gofmt:
    name: gofmt
    runs-on: ubuntu-latest
    steps:
      - name: Check out
        uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: "1.22"

      - name: Run gofmt
        run: gofmt -s -w .

      - name: Ensure gofmt matches
        run: git diff --color --exit-code
```

**Step 2: Verify YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/format-checker.yml'))" && echo "YAML OK"
```

Expected: `YAML OK`

---

### Task 5: Commit and push

**Step 1: Stage and commit**

```bash
git add .github/workflows/ci.yml .github/workflows/format-checker.yml
git commit -m "fix: update GitHub Actions workflows to fix CI failures

- Replace npm ci with yarn install --frozen-lockfile (project uses Yarn)
- Update all actions/checkout to @v4 (v2/v3 use EOL Node.js 12)
- Update actions/setup-go to @v5 and go version to 1.22
- Update actions/setup-node to @v4
- Add explicit setup-go to format-checker workflow"
```

**Step 2: Push**

```bash
git push origin HEAD
```

**Step 3: Monitor GitHub Actions**

```bash
gh run list --limit 5
```

Watch for the CI run to complete green. If it fails, run:

```bash
gh run view <run-id> --log-failed
```

---

## Success Criteria

- `CI` workflow: all 3 jobs (Go build, Frontend build, Deploy) pass
- `Format checker` workflow passes
- No deprecation errors about Node.js 12 runtime
