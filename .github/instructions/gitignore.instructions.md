---
applyTo: '.gitignore, **/.gitignore'
description: 'This file specifies intentionally untracked files that Git should ignore. It helps to avoid committing sensitive information, build artifacts, and other unnecessary files to the repository.'
---

Add the following patterns to the .gitignore file to ensure that certain files and directories are not tracked by Git:

# Ignore Python bytecode files
__pycache__/
*.pyc
# Ignore SQLite database files
data/*.db
# Ignore environment variable files
.env
# Ignore OS files
.DS_Store
Thumbs.db