"""
Utilities module for KosXER.

Contains backup management, validation, and helper functions.
"""

from .backup import (
    BackupManager,
    SafeFileWriter,
    create_backup_before_edit,
    restore_from_backup,
    safe_write
)

from .validation import (
    ValidationManager,
    SyntaxValidator,
    XResourcesValidator,
    OpenBoxMenuValidator,
    KeyValueValidator,
    ValidationError,
    validate_before_save,
    quick_validate
)

__all__ = [
    # Backup
    'BackupManager',
    'SafeFileWriter',
    'create_backup_before_edit',
    'restore_from_backup',
    'safe_write',
    
    # Validation
    'ValidationManager',
    'SyntaxValidator',
    'XResourcesValidator',
    'OpenBoxMenuValidator',
    'KeyValueValidator',
    'ValidationError',
    'validate_before_save',
    'quick_validate',
]
