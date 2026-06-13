# Operator Notes

These notes record local workflow pitfalls that can affect future development
or PR handling. Check this file before re-debugging GitHub authentication,
Windows command lookup, local validation command availability, or generated
runtime output.

Do not treat these notes as proof that a command succeeded. Always run the
current command and report the current output.

## GitHub CLI And Git Credentials

When GitHub operations fail, distinguish PATH problems from authentication
problems before changing anything:

```powershell
Get-Command gh -All
where.exe gh
gh --version
gh auth status --hostname github.com
```

On the current Windows environment, `gh` has normally resolved to:

```text
C:\Program Files\GitHub CLI\gh.exe
```

As of 2026-06-08, `Get-Command gh -All` showed only that executable, and
`gh auth status --hostname github.com` with the local proxy set reported the
`CheemsaDoge` account as logged in via `keyring`.

If `Get-Command gh -All` and `where.exe gh` show only one GitHub CLI but
`gh auth status` reports an invalid token, the problem is authentication, not
multiple `gh` binaries. Do not delete credentials or log out accounts unless
the maintainer explicitly asks for that action.

In managed Codex runs, sandboxed GitHub CLI checks can report a stale or
invalid token even after the maintainer has completed `gh auth login` in the
real Windows session. Re-check from a shell that can access the Windows keyring
before treating the token as broken. A valid full-access check looks like:

```powershell
gh auth status --hostname github.com
```

and should report the `CheemsaDoge` account as logged in via `keyring`.

`gh auth login -h github.com` is interactive. If it times out or is interrupted,
it may leave a waiting `gh.exe` process. Before retrying or starting another
GitHub operation, inspect the residual process and terminate only the command
that this session started:

```powershell
Get-Process | Where-Object { $_.ProcessName -eq 'gh' }
Get-CimInstance Win32_Process -Filter "Name='gh.exe'" |
  Select-Object ProcessId,CommandLine,ExecutablePath
```

Git operations use Git Credential Manager separately from `gh`. A stale or
invalid `gh` token does not necessarily mean `git push` will fail. If `gh auth
status` is invalid, it is still reasonable to try a normal `git push` and report
the actual result. If the branch is pushed but `gh` remains unusable, use an
available authenticated GitHub connector or ask the maintainer to reauthenticate
instead of faking PR creation.

For GitHub CLI or Git network diagnostics on this machine, explicitly set the
local proxy before blaming credentials or deleting configuration:

```powershell
$env:HTTP_PROXY='http://127.0.0.1:3067'
$env:HTTPS_PROXY='http://127.0.0.1:3067'
$env:http_proxy='http://127.0.0.1:3067'
$env:https_proxy='http://127.0.0.1:3067'
```

The proxy setting is a diagnostic and transport setup step only. It does not
prove that authentication is valid; still run the current `gh auth status`, API,
or Git command and report the real output.

Some older or packaged GitHub CLI builds do not support newer output flags on
every command. On this Windows environment, `gh issue create --json ...` failed
with `unknown flag: --json`. Create the issue with the plain command, capture
the printed URL, then inspect it separately if structured fields are needed:

```powershell
gh issue create --repo CheemsaDoge/tcs-cosheaf --title "<title>" --body "<body>"
gh issue view <number> --repo CheemsaDoge/tcs-cosheaf --json number,title,url
```

When using `gh issue list --search` from PowerShell, pass the search string as
one argument with quotes or avoid the search flag and filter JSON output
afterward. If the command reports `unknown arguments` followed by words from
the issue title, the shell split the search query; this is not an
authentication failure.

## GitHub Actions Stuck Check Runs

Sometimes a GitHub Actions job can show every step completed successfully while
the job and PR check-run still report `in_progress`. This blocks protected
branch merges even though the visible job steps look green. Treat that as a
GitHub Actions/check-run state problem, not as a passing required check.

First verify the exact state from both PR checks and the Actions job:

```powershell
gh pr checks <number> --repo CheemsaDoge/tcs-cosheaf
gh pr view <number> --repo CheemsaDoge/tcs-cosheaf `
  --json mergeStateStatus,statusCheckRollup
gh run view <run-id> --repo CheemsaDoge/tcs-cosheaf --json status,conclusion,jobs
gh api repos/CheemsaDoge/tcs-cosheaf/actions/runs/<run-id>/jobs
```

Do not bypass branch protection and do not merge while a required check remains
pending. If the job has been stuck after its final step completed, a low-risk
recovery path is:

```powershell
gh run cancel <run-id> --repo CheemsaDoge/tcs-cosheaf
git commit --allow-empty -m "Retry CI for <short task name>"
git push
gh pr checks <number> --repo CheemsaDoge/tcs-cosheaf
```

Use the empty commit only to trigger a fresh CI run when no file change is
needed. After the rerun is green and `mergeStateStatus` is clean, squash merge
with an explicit subject, body, and author email so the retry commit does not
become a separate default-branch commit:

```powershell
gh pr merge <number> --repo CheemsaDoge/tcs-cosheaf --squash `
  --delete-branch `
  --author-email cheemsadoge@gmail.com `
  --subject "<title>" `
  --body " "
```

## Git Path

Confirm the Git executable when debugging remote or credential behavior:

```powershell
Get-Command git -All
where.exe git
```

On the current Windows environment, `git` has normally resolved to:

```text
C:\Program Files\Git\cmd\git.exe
```

Do not assume the outer `H:\ai4tcs` directory is a repository. It is the
container for multiple repository worktrees. Run repository commands from the
specific checkout or worktree path.

## Git Index Lock Contention

Do not run Git index-writing commands in parallel with other Git commands in
the same checkout. Commands such as `git add`, `git commit`, `git merge`,
`git switch`, `git branch -D`, and `git reset` can contend for `.git/index.lock`
when another Git command is reading or writing repository state. Keep these
operations serial.

If Git reports:

```text
fatal: Unable to create '<repo>/.git/index.lock': File exists.
```

first check whether a Git process is still running:

```powershell
Get-Process | Where-Object {
  $_.ProcessName -eq 'git' -or $_.ProcessName -eq 'git-remote-https'
}
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -like 'git*.exe' } |
  Select-Object ProcessId,Name,CommandLine
```

If a Git process is still running, wait for it or investigate that process
instead of deleting the lock. If no Git process remains and the lock file still
exists, inspect the lock path and remove only that stale lock file:

```powershell
Get-Item -LiteralPath '<repo>\.git\index.lock'
Remove-Item -LiteralPath '<repo>\.git\index.lock' -Force
```

After removing a stale lock, rerun `git status --short --branch` before
continuing. Do not remove any other `.git` files or directories as part of this
recovery.

## Git Commit Identity

Before creating local commits in this repository family, verify the Git author
identity. The expected identity is:

```text
CheemsaDoge <cheemsadoge@gmail.com>
```

Check both global and repository-local config:

```powershell
git config --global --get user.name
git config --global --get user.email
git config --get user.name
git config --get user.email
```

If either config resolves to another name or email, correct it before
committing:

```powershell
git config --global user.name "CheemsaDoge"
git config --global user.email "cheemsadoge@gmail.com"
git config user.name "CheemsaDoge"
git config user.email "cheemsadoge@gmail.com"
```

After committing, inspect the actual commit metadata instead of assuming the
config was applied:

```powershell
git show -s --format=fuller HEAD
```

Do not add `Co-authored-by` trailers unless the maintainer explicitly asks for
them.

## GitHub Squash Merge Attribution

GitHub squash merges can preserve commit-message trailers from the PR body or
from commits included in the PR. This can happen even when the local commit
author and committer are both correct. A bad trailer such as:

```text
Co-authored-by: cheemsadoge <ywjh.net@qq.com>
```

can create an unwanted anonymous contributor entry on GitHub. Before merging a
PR with `gh pr merge --squash`, inspect the PR commits and avoid inheriting a
default squash body that contains stale attribution:

```powershell
gh pr view <number> --json commits
git log origin/main..HEAD --pretty=fuller
git log origin/main..HEAD --format=%B | Select-String -Pattern "Co-authored-by"
```

When the PR should attribute only the maintainer, merge with an explicit body
and author email:

```powershell
gh pr merge <number> --squash --delete-branch `
  --author-email cheemsadoge@gmail.com `
  --subject "<title>" `
  --body " "
```

After merging, verify the resulting default-branch commit:

```powershell
git fetch origin --prune
git log -1 origin/main --pretty=fuller
git log -1 origin/main --format=%B | Select-String -Pattern "Co-authored-by"
```

If unwanted authors or trailers already exist on the default branch, deleting
feature branches is not enough. Contributor cleanup then requires the
default-branch history-cleanup procedure below.

## Default Branch History Cleanup

GitHub contributor cleanup can require history cleanup when the default branch
contains an unwanted commit author, committer, or commit-message trailer such
as `Co-authored-by`. A normal revert removes content from the current tree but
does not remove historical contributor attribution from the default branch.

Use this only when the maintainer explicitly authorizes default-branch history
rewriting:

1. Record the current `origin/main` commit.
2. Create a remote backup branch pointing at that exact commit.
3. Build a replacement history in an isolated worktree.
4. Verify the replacement tree with the full command ladder.
5. Confirm `git log --grep <unwanted-name> -i` has no unwanted matches.
6. Temporarily allow force pushes on `main` only if branch protection blocks the
   update.
7. Push with `--force-with-lease=refs/heads/main:<old-main-commit>`.
8. Immediately restore branch protection.
9. Re-check `origin/main`, branch protection, and the GitHub contributors API.

Never force-push `main` without a backup branch and an explicit old-commit
lease.

## `cosheaf` Command Lookup

The framework package may be installed even when `cosheaf.exe` is not on the
current PowerShell PATH. Before reinstalling the package, inspect Python and
script lookup:

```powershell
where.exe python
python --version
python -m pip show tcs-cosheaf
where.exe cosheaf
Get-ChildItem "$env:APPDATA\Python\Python313\Scripts" -Filter "cosheaf*"
python -m cosheaf.cli --help
```

On the current Windows environment, `tcs-cosheaf 0.2.1` has been installed for
Python 3.13 under the user site-packages, with the console script at:

```text
C:\Users\ywjhn\AppData\Roaming\Python\Python313\Scripts\cosheaf.exe
```

If `cosheaf.exe` exists there but is not on PATH, temporarily prepend that
Scripts directory for the current verification command and record the PATH
issue in the PR summary:

```powershell
$env:Path = 'C:\Users\ywjhn\AppData\Roaming\Python\Python313\Scripts;' + $env:Path
cosheaf validate
```

Do not claim the original `cosheaf ...` command passed if it first failed due
to PATH. Report both the initial failure and the verified rerun.

As of 2026-06-08, this Scripts directory has been added to the user PATH:

```text
C:\Users\ywjhn\AppData\Roaming\Python\Python313\Scripts
```

If a later shell still cannot find `cosheaf`, open a new shell or inspect the
current process PATH before reinstalling.

## Windows `make` Lookup

In this Windows environment, `D:\Code\mingw64\bin` is on `PATH` and contains
`mingw32-make.exe`. A local hardlink has been added in that directory so the
literal `make` command resolves directly to MinGW Make without going through
PowerShell or `cmd.exe` script wrappers:

```text
D:\Code\mingw64\bin\make.exe -> D:\Code\mingw64\bin\mingw32-make.exe
```

Before falling back manually, check the current command lookup:

```powershell
Get-Command make -All
make --version
```

If this executable is present, run the required literal commands normally:

```powershell
make lint
make typecheck
make test
make validate
make gate
```

If `make` is missing in a future session, report that exact failure and then use
the repository-supported fallback where available:

```powershell
mingw32-make lint
mingw32-make typecheck
mingw32-make test
mingw32-make validate
mingw32-make gate
```

Do not describe `mingw32-make` as if it were the literal `make` command unless
`Get-Command make` shows that the `make.exe` hardlink is what actually ran. PR
summaries should distinguish an unavailable literal command from any successful
fallback.

## Runtime Outputs

Framework and KB commands may generate reports, indexes, context packs, or logs
under `.cosheaf/`. These are runtime outputs unless the task explicitly asks to
persist a particular report. They should remain ignored and uncommitted:

```powershell
git check-ignore -v .cosheaf
git status --short
```

If runtime files appear outside ignored locations, move the runtime target under
`.cosheaf/` or document the issue before opening a PR. Do not commit generated
reports just because a verification command produced them.

## Patch Tool Base Directory

In this Codex environment, `apply_patch` uses the session current working
directory as its path base, not the `workdir` used by the most recent shell
command. When the session starts in the parent container `H:\ai4tcs` but the
active task is inside an isolated worktree such as
`H:\ai4tcs\tcs-cosheaf-phase4-task-dag-planner-stub`, patch paths must include
the worktree directory prefix:

```text
tcs-cosheaf-phase4-task-dag-planner-stub/path/inside/repo.py
```

Before running tests, confirm new files landed in the intended worktree with:

```powershell
git status --short
```

If a file is accidentally created under the parent container, delete only the
misplaced file you created and re-apply the patch inside the intended worktree
path. Do not clean broad parent directories or unrelated worktrees.

## Public KB Review Boundary

For `tcs-kb-public`, CI and gate success are not human review. Public KB policy
changes, accepted public artifacts, source-note conventions, and accepted
promotion semantics require maintainer review before merge or promotion. Do not
use a green check to justify accepted public knowledge.
