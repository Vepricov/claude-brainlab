| :------- | :---------------- | :------------------------- | :------------- |

```
```

```
```

```
```

```
```

```bash
git checkout develop
git pull origin develop
git checkout -b feature/user-management
```

```bash
git checkout develop
git pull origin develop
git checkout -b bugfix/login-error
```

```bash
git checkout master
git pull origin master
git checkout -b hotfix/security-fix
```

```bash
```

```bash
git checkout develop
git pull origin develop

git checkout -b feature/user-management

git add .

git push -u origin feature/user-management

git branch -d feature/user-management
git push origin -d feature/user-management
```

```bash
git checkout master
git pull origin master
git checkout -b hotfix/critical-bug

git add .

git checkout master
git merge --no-ff hotfix/critical-bug
git push origin master --tags

git checkout develop
git merge --no-ff hotfix/critical-bug
git push origin develop

git branch -d hotfix/critical-bug
```

```bash
git checkout develop
git checkout -b release/v1.0.0

git add .

git checkout master
git merge --no-ff release/v1.0.0
git push origin master --tags

git checkout develop
git merge --no-ff release/v1.0.0
git push origin develop

git branch -d release/v1.0.0
```
