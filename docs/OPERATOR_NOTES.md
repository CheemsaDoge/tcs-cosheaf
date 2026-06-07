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

On the current Windows environment, `tcs-cosheaf 0.1.1` has been installed for
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

## Windows `make` Fallback

In this Windows environment, the literal `make` command may be unavailable even
when repository checks can be run through MinGW Make. If a required command says
`make lint`, first run the literal command when the PR checklist requires it.
If it fails because `make` is missing, report that exact failure and then use
the repository-supported fallback where available:

```powershell
mingw32-make lint
mingw32-make typecheck
mingw32-make test
mingw32-make validate
mingw32-make gate
```

Do not describe `mingw32-make` as if it were the literal `make` command. PR
summaries should distinguish the unavailable command from the successful
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

## Public KB Review Boundary

For `tcs-kb-public`, CI and gate success are not human review. Public KB policy
changes, accepted public artifacts, source-note conventions, and accepted
promotion semantics require maintainer review before merge or promotion. Do not
use a green check to justify accepted public knowledge.
