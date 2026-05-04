---
name: create_project
description: Create a new project from template with uv and Git initialization
arguments:
  - name: project_name
    required: true
  - name: path
    required: false
  - name: template_repo
    required: false
  - name: local
    required: false
---

```bash
PROJECT_NAME="{{project_name}}"
PROJECT_PATH="${path:-$HOME/Code}"
FULL_PATH="$PROJECT_PATH/$PROJECT_NAME"
TEMPLATE_REPO="{{template_repo:-gaoruizhang/template}}"
USE_LOCAL="{{local}}"
INITIAL_TAG="v0.1.0"

if [ "$USE_LOCAL" = "true" ]; then
  TEMPLATE_PATH="$HOME/Code/template"
  USE_LOCAL_TEMPLATE=true
else
  if [[ "$TEMPLATE_REPO" == https://github.com/* ]] || [[ "$TEMPLATE_REPO" == git@github.com:* ]]; then
    TEMPLATE_URL="$TEMPLATE_REPO"
  else
    TEMPLATE_URL="https://github.com/$TEMPLATE_REPO"
  fi
  USE_LOCAL_TEMPLATE=false
fi

echo ""

if [ "$USE_LOCAL_TEMPLATE" = true ]; then
  if [ ! -d "$TEMPLATE_PATH" ]; then
    exit 1
  fi
else
fi

if [ -d "$FULL_PATH" ]; then
  exit 1
fi

mkdir -p "$FULL_PATH"

if [ "$USE_LOCAL_TEMPLATE" = true ]; then
  rsync -av --exclude='.git' \
            --exclude='.idea' \
            --exclude='.DS_Store' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            "$TEMPLATE_PATH/" "$FULL_PATH/"
else
  TEMP_TEMPLATE_DIR=$(mktemp -d)
  git clone --depth 1 "$TEMPLATE_URL" "$TEMP_TEMPLATE_DIR"

  rsync -av --exclude='.git' \
            --exclude='.idea' \
            --exclude='.DS_Store' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            "$TEMP_TEMPLATE_DIR/" "$FULL_PATH/"

  rm -rf "$TEMP_TEMPLATE_DIR"
fi

cd "$FULL_PATH"

if [ -f "README.md" ]; then
  FIRST_LINE=$(head -n 1 README.md)
  if [[ "$FIRST_LINE" == "#"* ]]; then
    echo "# $PROJECT_NAME" > README.md.new
    tail -n +2 README.md >> README.md.new
    mv README.md.new README.md
  fi
fi

if [ -f "pyproject.toml" ]; then
  sed -i.bak "s/name = \".*\"/name = \"$PROJECT_NAME\"/" pyproject.toml
  rm -f pyproject.toml.bak
fi

uv sync

git init

git add .

git checkout -b develop

echo ""
echo ""
echo ""
echo "   cd $FULL_PATH"
echo ""

echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  if ! command -v gh &> /dev/null; then
  else
    cd "$FULL_PATH"

    gh repo create "$PROJECT_NAME" --private --source=. --remote=origin

    git checkout master
    git push -u origin master
    git push origin "$INITIAL_TAG"
    git push -u origin develop
    git checkout develop

    echo ""

    REPO_URL=$(git config --get remote.origin.url)
    if [[ "$REPO_URL" == "git@github.com"* ]]; then
      # SSH URL
      REPO_URL="https://github.com/$(git config --get user.name)/$PROJECT_NAME"
    fi
    echo "   👉 $REPO_URL"
  fi
else
  echo "   cd $FULL_PATH && gh repo create $PROJECT_NAME --private --source=. --remote=origin"
fi

echo ""
echo ""
echo ""
echo ""
echo ""
echo "   cd $FULL_PATH"
echo ""
