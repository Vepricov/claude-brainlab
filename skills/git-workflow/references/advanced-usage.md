```
MAJOR.MINOR.PATCH[-PRERELEASE]
```

| :------- | :----------------- | :---------------- |

```
```

```bash

```

```bash
git push origin v1.0.0

git push origin --tags
```

```bash
git tag
git tag -l "v1.*"
git show v1.0.0
```

```bash
git tag -d v1.0.0

git push origin :refs/tags/v1.0.0
```

```bash
git clone --depth 1 https://github.com/repo/project.git

git clone --filter=blob:none https://github.com/repo/project.git

git clone --filter=blob:none --sparse https://github.com/repo/project.git
cd project
git sparse-checkout init --cone
git sparse-checkout set src/frontend
```

```bash
git count-objects -vH

git gc --aggressive --prune=now

git remote prune origin

git branch --merged master | grep -v "\\*\\|master\\|develop" | xargs -n 1 git branch -d
```

```bash
git config --global core.fscache true

git config --global fetch.parallel 4

git config --global core.untrackedCache true
```

```bash
git log -p | grep -E "(password|secret|api_key)"

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config/secrets.yml' \
  --prune-empty --tag-name-filter cat -- --all

git secrets --install
git secrets --register-aws
```

```bash
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true

git log --show-signature
```

| :--------------- | :----- | :------ | :-------- |

```bash
git submodule add https://github.com/user/repo.git libs/repo

git clone --recurse-submodules https://github.com/user/project.git

git submodule init
git submodule update
```

```bash
cd libs/repo
git pull origin main

git submodule update --remote

cd ..
git add libs/repo
```

```bash
git submodule deinit -f libs/repo

rm -rf .git/modules/libs/repo

git rm -f libs/repo
```

```bash
git add forgotten-file.ts
git commit --amend --no-edit

git reset --soft HEAD~1
```

```bash
git pull origin master
git push origin master

git pull --rebase origin master
git push origin master
```

```bash
git reset --hard abc123

git revert abc123
```

```bash
git reflog

git checkout -b feature/xxx def456
```

```bash
git rebase -i HEAD~5

```

```bash
git stash list
git stash pop
git stash apply stash@{0}
```

```bash
```

```bash
git lfs install
git lfs track "*.zip"
git add .gitattributes
```

```bash
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.lg "log --graph --oneline --all"
```

```bash
git log --graph --oneline --all

git log -S"function_name"
```

```bash
git reset --hard HEAD

git checkout -- filename

git clean -fd

git branch --merged master | grep -v "\* master" | xargs -n 1 git branch -d
```

```bash
git push --dry-run

git push --force-with-lease

git branch backup-master master
```

```bash
git bisect start
```

```bash
pnpm install -D conventional-changelog-cli

npx conventional-changelog -p angular -i CHANGELOG.md -s
```

```markdown

## [1.2.0] - 2024-01-15

## [1.1.0] - 2024-01-01
...
```
