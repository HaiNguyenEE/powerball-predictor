#!/usr/bin/env python3
"""
deploy_github.py — Publish the app to GitHub Pages.

Workflow
--------
1. Initializes git in this folder (if not already).
2. Adds all files (respecting .gitignore).
3. Creates a GitHub repo via `gh` CLI and pushes.
4. Enables GitHub Pages on the main branch.
5. Prints the live URL.

Requirements
------------
- `git`  (preinstalled on macOS)
- `gh`   GitHub CLI — install with: brew install gh
         then authenticate with:    gh auth login

Re-running this script after edits just commits + pushes the changes.
"""

import os
import sys
import subprocess
import shutil
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


def run(cmd, capture=True, check=True, **kw):
    """Run a shell command, return (rc, stdout)."""
    if isinstance(cmd, str):
        cmd_list = cmd
        shell = True
    else:
        cmd_list = cmd
        shell = False
    r = subprocess.run(cmd_list, shell=shell, capture_output=capture,
                       text=True, check=False, **kw)
    if check and r.returncode != 0:
        print(f"✗ Command failed: {cmd}")
        if r.stdout: print(r.stdout)
        if r.stderr: print(r.stderr)
        sys.exit(1)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def have(cmd):
    return shutil.which(cmd) is not None


def main():
    print("=" * 68)
    print("  Powerball Predictor — GitHub Pages Deployment")
    print("=" * 68)

    # 1. git
    if not have("git"):
        print("✗ git not installed. Install Xcode Command Line Tools:")
        print("  xcode-select --install")
        sys.exit(1)

    # 2. gh
    if not have("gh"):
        print("✗ GitHub CLI (gh) not installed.")
        print("  Install with:  brew install gh")
        print("  Then:          gh auth login")
        print()
        ans = input("Try `brew install gh` now? [Y/n] ").strip().lower()
        if ans in ("", "y", "yes"):
            run("brew install gh", capture=False)
        else:
            sys.exit(1)

    # 3. gh auth
    rc, out = run("gh auth status", check=False)
    if rc != 0:
        print("→ You need to authenticate gh first.")
        print("  Running: gh auth login --web --git-protocol https")
        print("  Pick: GitHub.com → HTTPS → Yes → Login with browser")
        print()
        run("gh auth login --web --git-protocol https", capture=False, check=False)
        rc, out = run("gh auth status", check=False)
        if rc != 0:
            print("✗ gh auth failed.")
            sys.exit(1)

    # 4. Init git repo
    if not os.path.isdir(".git"):
        print("→ Initializing git repo…")
        run("git init -b main")
    else:
        print("→ Git repo already exists.")

    # 5. Check / set git config
    rc, out = run("git config user.email", check=False)
    if rc != 0 or not out.strip():
        rc, who = run("gh api user --jq .email", check=False)
        email = who.strip() if rc == 0 and who.strip() and who.strip() != "null" else input("git user.email: ").strip()
        rc, who = run("gh api user --jq .login", check=False)
        name = who.strip() if rc == 0 else input("git user.name: ").strip()
        run(f'git config user.email "{email or name + "@users.noreply.github.com"}"')
        run(f'git config user.name "{name}"')

    # 5b. Pull first so we don't conflict with bot commits from GitHub Actions
    rc, _ = run("git remote", check=False)
    if "origin" in (_ or ""):
        print("→ Pulling latest from origin (auto-rebase)…")
        run("git pull --rebase origin main", check=False)

    # 6. Stage and commit
    print("→ Staging files…")
    run("git add -A")
    rc, status = run("git status --porcelain", check=False)
    if status.strip():
        msg = f"Deploy {time.strftime('%Y-%m-%d %H:%M')} — {sum(1 for _ in open('data/powerball_history.json') if 'date' in _)} draws"
        run(f'git commit -m "{msg}"')
        print(f"  committed: {msg}")
    else:
        print("  no changes to commit")

    # 7. Repo name
    default_repo = "powerball-predictor"
    repo = input(f"GitHub repo name [{default_repo}]: ").strip() or default_repo

    # 8. Detect username
    rc, user = run("gh api user --jq .login")
    user = user.strip()
    print(f"→ GitHub user: {user}")
    full_name = f"{user}/{repo}"

    # 9. Check if repo exists
    rc, _ = run(f"gh repo view {full_name}", check=False)
    if rc == 0:
        print(f"→ Repo {full_name} already exists. Pushing updates…")
        # Make sure remote is set
        rc, remotes = run("git remote", check=False)
        if "origin" not in remotes:
            run(f"git remote add origin https://github.com/{full_name}.git")
        run("git push -u origin main", capture=False)
    else:
        print(f"→ Creating public repo {full_name}…")
        run(f'gh repo create {full_name} --public --source=. --remote=origin --push --description "Powerball Predictor — Ensemble Lab (statistical research tool)"', capture=False)

    # 10. Enable Pages
    print("→ Enabling GitHub Pages…")
    pages_url = f"https://{user}.github.io/{repo}/"
    # Check if Pages already enabled
    rc, _ = run(f"gh api repos/{full_name}/pages", check=False)
    if rc != 0:
        # Create pages site from main / root
        rc, out = run(
            f'gh api repos/{full_name}/pages -X POST '
            f'-H "Accept: application/vnd.github+json" '
            f'-f "source[branch]=main" -f "source[path]=/"',
            check=False
        )
        if rc != 0:
            print("  ! API call failed — enable manually:")
            print(f"  https://github.com/{full_name}/settings/pages")
            print(f"  Set: Source = Deploy from a branch, Branch = main, Folder = /(root)")
    else:
        print("  Pages already enabled.")

    print()
    print("=" * 68)
    print("  ✓ DEPLOYED")
    print("=" * 68)
    print()
    print(f"  Repo:  https://github.com/{full_name}")
    print(f"  Live:  {pages_url}")
    print(f"  App:   {pages_url}app/index.html")
    print()
    print(f"  ⏱  GitHub Pages takes ~30-60 seconds for the first build.")
    print(f"     Refresh the live URL after a minute.")
    print()
    print(f"  📱 Share the Live URL — anyone, any device, any network.")
    print(f"     On iPhone: open in Safari → Share → Add to Home Screen.")
    print()
    print(f"  🔄 To redeploy after changes: just run `python3 deploy_github.py` again.")
    print()


if __name__ == "__main__":
    main()
