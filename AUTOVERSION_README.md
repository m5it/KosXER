# AUTOVERSION for KosXER

Automatic version incrementing on git commits.

## How It Works

`AUTOVERSION.py` is the **single source of truth** for the version number.

Every time you make a git commit:
1. Version increments (1.0.0 → 1.0.1)
2. AUTOVERSION.py is updated
3. config/constants.py is updated
4. config/VERSION is updated
5. All files are automatically staged

## Usage

Import version anywhere in your code:
```python
from AUTOVERSION import VERSION
print(f"Version: {VERSION}")  # "1.0.5"
```

## Files

| File | Purpose |
|------|---------|
| `AUTOVERSION.py` | **Single source of truth** - contains VERSION constant |
| `config/constants.py` | Imports VERSION from AUTOVERSION |
| `config/VERSION` | Plain text backup of version |
| `.git/hooks/pre-commit` | Git hook that runs AUTOVERSION |

## Test It

```bash
# Check current version
python3 AUTOVERSION.py --show

# Make a commit (version auto-increments)
git add -A
git commit -m "Your changes"
cat AUTOVERSION.py | grep VERSION
```

## Disable

```bash
# Skip auto-version for one commit
git commit --no-verify -m "Your message"

# Or remove the hook entirely
rm .git/hooks/pre-commit
```
