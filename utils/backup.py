"""Backup management utilities for KosXER."""

import os
import shutil
from datetime import datetime
from config.constants import BACKUP_DIR


class BackupManager:
    """Manages file backups before editing."""
    
    def __init__(self, max_backups: int = 5):
        """Initialize backup manager.
        
        Args:
            max_backups: Maximum number of backups to keep per file
        """
        self.max_backups = max_backups
    
    def create_backup(self, filepath: str) -> str:
        """Create a backup of the given file.
        
        Args:
            filepath: Path to the file to backup
            
        Returns:
            Path to the backup file
        """
        if not os.path.exists(filepath):
            return None
        
        # Generate backup filename with timestamp
        filename = os.path.basename(filepath)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filename}.{timestamp}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        # Copy file to backup
        shutil.copy2(filepath, backup_path)
        
        # Cleanup old backups for this file
        self._cleanup_old_backups(filename)
        
        return backup_path
    
    def _cleanup_old_backups(self, filename: str):
        """Remove old backups keeping only max_backups."""
        backups = self._get_backups_for_file(filename)
        if len(backups) > self.max_backups:
            # Sort by modification time and remove oldest
            backups.sort(key=lambda x: os.path.getmtime(x))
            for old_backup in backups[:-self.max_backups]:
                try:
                    os.remove(old_backup)
                except OSError:
                    pass
    
    def _get_backups_for_file(self, filename: str) -> list:
        """Get all backup files for a given filename."""
        if not os.path.exists(BACKUP_DIR):
            return []
        
        backups = []
        for f in os.listdir(BACKUP_DIR):
            if f.startswith(filename) and f.endswith('.bak'):
                backups.append(os.path.join(BACKUP_DIR, f))
        return backups
    
    def list_backups(self, filename: str = None) -> list:
        """List available backups.
        
        Args:
            filename: If provided, only list backups for this file
            
        Returns:
            List of backup file paths
        """
        if not os.path.exists(BACKUP_DIR):
            return []
        
        if filename:
            return self._get_backups_for_file(filename)
        
        return [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR)
                if f.endswith('.bak')]
    
    def restore_backup(self, backup_path: str, target_path: str = None) -> bool:
        """Restore a backup file.
        
        Args:
            backup_path: Path to the backup file
            target_path: Where to restore (defaults to original location)
            
        Returns:
            True if successful
        """
        if not os.path.exists(backup_path):
            return False
        
        if target_path is None:
            # Extract original filename from backup name
            basename = os.path.basename(backup_path)
            # Remove timestamp and .bak
            parts = basename.rsplit('.', 2)
            if len(parts) >= 3:
                target_path = os.path.join(os.path.dirname(backup_path), parts[0])
        
        if target_path:
            shutil.copy2(backup_path, target_path)
            return True
        return False
