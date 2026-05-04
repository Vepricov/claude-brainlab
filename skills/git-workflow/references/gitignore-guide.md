```

```

```
# ============================================
# ============================================
node_modules/
vendor/

# ============================================
# ============================================
dist/
build/
target/

# ============================================
# ============================================
.idea/
.vscode/
*.sw?

# ============================================
# ============================================
.env
.env.local
.env.*.local

# ============================================
# ============================================
logs/
*.log
npm-debug.log*

# ============================================
# ============================================
.DS_Store
Thumbs.db

# ============================================
# ============================================
.cache/
.eslintcache
.stylelintcache
```

```
# VitePress
docs/.vitepress/dist
docs/.vitepress/cache

# Node.js
package-lock.json
yarn.lock
pnpm-lock.yaml
```

```
# Maven
target/
pom.xml.tag
*.jar
!**/src/main/**/target/

application-local.yml
application-dev.yml
```

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.pytest_cache/

# Jupyter Notebook
.ipynb_checkpoints

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype
.pytype/
```

```
# Binaries for programs and plugins
*.exe
*.exe~
*.dll
*.so
*.dylib

# Test binary, built with `go test -c`
*.test

# Output of the go coverage tool
*.out

# Dependency directories
vendor/

# Go workspace file
go.work
```

```
# Rust
/target/
**/*.rs.bk
*.pdb
Cargo.lock
```

```
logs/*
!logs/.gitkeep
```

```bash
git check-ignore -v filename
```

```bash
git rm --cached filename
```

```bash
git check-ignore -v path/to/file

git ls-files --others --ignored --exclude-standard
```

```
config/local.json
secrets.yaml
```

```
*.log

*.tmp
*.temp
```

```
node_modules/

/build/

**/build/
```

```
*.a

!lib.a

TODO*

!TODO.md
```

```
*.log

**/temp/

file?.txt

file[0-9].txt
```

```bash
git config --global core.excludesfile ~/.gitignore_global

echo "secrets.yaml" >> .git/info/exclude
```
