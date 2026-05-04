## Merge vs Rebase

| :------- | :------------------------- | :----------------------- |

```bash
git checkout feature/user-management
git rebase develop
```

```bash
git checkout develop
git merge --no-ff feature/user-management
```

```bash
git checkout master
git merge --no-ff develop
```

```bash
git checkout develop
```

## Fast-Forward vs No-Fast-Forward

```bash
git merge feature/xxx
```

```
# A---B---C  (master)
#          \
#           D---E  (feature)
```

```bash
git merge --no-ff feature/xxx
```

```
# A---B---C---------M  (master)
#          \       /
#           D---E    (feature)
```

```bash
git checkout develop
git merge --squash feature/user-management
```

### Squash vs Merge --no-ff

| :---------- | :----------------------- | :----------------------- | :--------------------- |

```bash
git rebase -i HEAD~5
```

```bash
git rebase develop
git add <file>
git rebase --continue
git rebase --abort
```
