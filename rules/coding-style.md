# Code Style — ML Projects

## File size
- Target 200–400 lines per file. Split at 400+.
- Related files go in subdirectories, not flat.

## Key principles
- Config via `@dataclass(frozen=True)` — immutable, no global vars
- Type hints on all functions (`typing` module)
- `logger = logging.getLogger(__name__)` — no `print()` for debug
- Catch specific exceptions, never bare `except:`
- No mutable default arguments (`def f(a=[])` → `def f(a=None)`)
- No hardcoded hyperparameters — use cfg

## Naming
- Classes: `PascalCase`, functions/vars: `snake_case`, constants: `UPPER_SNAKE_CASE`, private: `_prefix`

## Import order
1. stdlib, 2. third-party, 3. local

## Factory & Registry pattern (required for models/datasets)
```python
FACTORY: Dict[str, Type[Base]] = {}
def register(name):
    def decorator(cls): FACTORY[name] = cls; return cls
    return decorator
```

## Model `__init__` — only accepts `cfg`
```python
@register_model('MyModel')
class MyModel(nn.Module):
    def __init__(self, cfg):
        self.hidden_dim = cfg.model.hidden_dim
```

## Log levels
- DEBUG: tensor shapes, config values
- INFO: epoch results, milestones
- WARNING: fallbacks, deprecations
- ERROR: failures needing attention

## `__init__.py` must define `__all__`

## Prohibited
Files > 800 lines, nesting > 4 levels, global variables, unused imports, `print()` debug
