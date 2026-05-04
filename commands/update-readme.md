---
description: Update README documentation and push changes to GitHub.
---

# Update README

Update README.md file with latest project information and push to GitHub.

## Instructions

1. **Analyze Current State**
   - Read existing README.md
   - Check recent code changes (git log)
   - Identify documentation gaps

2. **Determine Updates Needed**
   Check for:
   - New features added
   - Configuration changes
   - Dependencies updated
   - Installation instructions
   - Usage examples
   - API changes

3. **Propose README Updates**
   Show sections that need updating:
   ```markdown
   Proposed changes:
   - [ ] Update Installation section (new dependencies)
   - [ ] Add usage example for feature X
   - [ ] Update API documentation
   - [ ] Fix broken links
   ```

4. **Update README**
   - Apply proposed changes
   - Maintain markdown formatting
   - Preserve structure

5. **Commit and Push**
   - Run `/update-github` with `docs(readme):` type

## Example Usage

```
User: /update-readme

1. Analyzing repository state...

Recent changes:

2. Checking README.md...

Current README sections:
- Installation
- Usage
- API Reference
- Contributing

3. Proposed updates:

4. Applying updates...

   Updating Installation:
   + pip install torch>=2.0.0
   + pip install transformers>=4.30.0

   Adding usage example:
   ```python
   from data import DataLoader
   loader = DataLoader(batch_size=32)
   ```

5. Review changes before committing...
   [Show diff]

6. Proceed with commit?
   > yes

   Co-Authored-By: Claude <noreply@anthropic.com>

✅ README updated and pushed to GitHub!
```

## README Structure Template

When updating README, follow this structure:

```markdown

- Python >= 3.8

```bash
uv sync
```

```python
```

```bash
pytest
```

MIT License
```

## Arguments

$ARGUMENTS can be:
- `--full` - Complete README rewrite
- `--quick` - Only update critical sections (installation, usage)
- `<section>` - Update specific section only

## Integration

After updating README, this command automatically invokes `/update-github` with `docs(readme):` commit type.
