#!/usr/bin/env python3
"""
Backup Management Utilities for KosXER

Provides automatic backup creation, retention management,
and restore functionality for configuration files.
"""

import os
import shutil
import glob
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
import tkinter as tk
from tkinter import messagebox


class BackupManager:
    """
    Manages file backups before editing.
    
    Features:
    - Automatic backup creation (.bak or ~ files)
    - Configurable backup retention (keep last N backups)
    - Restore from backup functionality
    - Timestamped backups for history
    """
    
    def __init__(self, backup_dir: Optional[str] = None, max_backups: int = 5):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups (None for same dir as original)
            max_backups: Maximum number of backups to keep per file
        """
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        self.backup_suffixes = ['.bak', '~']
    
    def create_backup(self, filepath: str, use_timestamp: bool = True) -> Optional[str]:
        """
        Create a backup of the given file.
        
        Args:
            filepath: Path to the file to backup
            use_timestamp: If True, append timestamp to backup name
            
        Returns:
            Path to the backup file or None if source doesn't exist
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        # Determine backup path
        if self.backup_dir:
            backup_root = Path(self.backup_dir)
            backup_root.mkdir(parents=True, exist_ok=True)
        else:
            backup_root = filepath.parent
        
        filename = filepath.name
        
        if use_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filename}.{timestamp}.bak"
        else:
            backup_name = f"{filename}.bak"
        
        backup_path = backup_root / backup_name
        
        # Copy file to backup
        shutil.copy2(filepath, backup_path)
        
        # Clean old backups
        self._cleanup_old_backups(filepath)
        
        return str(backup_path)
    
    def create_simple_backup(self, filepath: str) -> Optional[str]:
        """
        Create a simple .bak backup (no timestamp).
        
        Args:
            filepath: Path to the file to backup
            
        Returns:
            Path to the backup file
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        backup_path = filepath.parent / f"{filepath.name}.bak"
        shutil.copy2(filepath, backup_path)
        
        return str(backup_path)
    
    def create_tilde_backup(self, filepath: str) -> Optional[str]:
        """
        Create a tilde backup (file~).
        
        Args:
            filepath: Path to the file to backup
            
        Returns:
            Path to the backup file
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        backup_path = filepath.parent / f"{filepath.name}~"
        shutil.copy2(filepath, backup_path)
        
        return str(backup_path)
    
    def _cleanup_old_backups(self, filepath: Path):
        """
        Remove old backups, keeping only max_backups most recent.
        
        Args:
            filepath: Original file path
        """
        if self.backup_dir:
            search_dir = Path(self.backup_dir)
        else:
            search_dir = filepath.parent
        
        # Find all timestamped backups for this file
        pattern = f"{filepath.name}.*.bak"
        backups = list(search_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove excess backups
        for old_backup in backups[self.max_backups:]:
            try:
                old_backup.unlink()
            except OSError:
                pass
    
    def list_backups(self, filepath: str) -> List[Tuple[str, datetime]]:
        """
        List all backups for a file.
        
        Args:
            filepath: Original file path
            
        Returns:
            List of tuples (backup_path, timestamp)
        """
        filepath = Path(filepath)
        
        if self.backup_dir:
            search_dir = Path(self.backup_dir)
        else:
            search_dir = filepath.parent
        
        backups = []
        
        # Find timestamped backups
        pattern = f"{filepath.name}.*.bak"
        for backup in search_dir.glob(pattern):
            timestamp = datetime.fromtimestamp(backup.stat().st_mtime)
            backups.append((str(backup), timestamp))
        
        # Find simple backups
        simple_backup = search_dir / f"{filepath.name}.bak"
        if simple_backup.exists():
            timestamp = datetime.fromtimestamp(simple_backup.stat().st_mtime)
            backups.append((str(simple_backup), timestamp))
        
        # Find tilde backups
        tilde_backup = search_dir / f"{filepath.name}~"
        if tilde_backup.exists():
            timestamp = datetime.fromtimestamp(tilde_backup.stat().st_mtime)
            backups.append((str(tilde_backup), timestamp))
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x[1], reverse=True)
        
        return backups
    
    def restore_backup(self, filepath: str, backup_path: Optional[str] = None) -> bool:
        """
        Restore file from backup.
        
        Args:
            filepath: Path to file to restore
            backup_path: Specific backup to restore from (None for most recent)
            
        Returns:
            True if restore successful
        """
        filepath = Path(filepath)
        
        if backup_path is None:
            # Find most recent backup
            backups = self.list_backups(filepath)
            if not backups:
                return False
            backup_path = backups[0][0]
        
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            return False
        
        try:
            # Create backup of current state first (if file exists)
            if filepath.exists():
                self.create_tilde_backup(filepath)
            
            # Restore from backup
            shutil.copy2(backup_path, filepath)
            return True
            
        except OSError:
            return False
    
    def confirm_restore(self, filepath: str, parent_widget=None) -> bool:
        """
        Show confirmation dialog and restore if confirmed.
        
        Args:
            filepath: Path to file to restore
            parent_widget: Parent widget for dialog
            
        Returns:
            True if restore was performed
        """
        backups = self.list_backups(filepath)
        
        if not backups:
            messagebox.showwarning(
                "No Backups",
                f"No backups found for:\n{filepath}",
                parent=parent_widget
            )
            return False
        
        # Show most recent backups
        backup_list = "\n".join([
            f"  {i+1}. {b[1].strftime('%Y-%m-%d %H:%M:%S')}"
            for i, b in enumerate(backups[:5])
        ])
        
        response = messagebox.askyesno(
            "Restore Backup",
            f"Restore from most recent backup?\n\n"
            f"File: {filepath}\n\n"
            f"Available backups:\n{backup_list}\n\n"
            f"Current file will be backed up before restore.",
            parent=parent_widget
        )
        
        if response:
            return self.restore_backup(filepath)
        
        return False
    
    def delete_all_backups(self, filepath: str) -> int:
        """
        Delete all backups for a file.
        
        Args:
            filepath: Original file path
            
        Returns:
            Number of backups deleted
        """
        backups = self.list_backups(filepath)
        count = 0
        
        for backup_path, _ in backups:
            try:
                Path(backup_path).unlink()
                count += 1
            except OSError:
                pass
        
        return count
    
    def get_backup_size(self, filepath: str) -> int:
        """
        Get total size of all backups for a file.
        
        Args:
            filepath: Original file path
            
        Returns:
            Total size in bytes
        """
        backups = self.list_backups(filepath)
        total_size = 0
        
        for backup_path, _ in backups:
            try:
                total_size += Path(backup_path).stat().st_size
            except OSError:
                pass
        
        return total_size


class SafeFileWriter:
    """
    Safely writes files with backup creation and error handling.
    
    Features:
    - Automatic backup before write
    - Confirm overwrite for read-only files
    - Atomic write (write to temp, then rename)
    - User-friendly error dialogs
    """
    
    def __init__(self, backup_manager: Optional[BackupManager] = None):
        """
        Initialize safe file writer.
        
        Args:
            backup_manager: BackupManager to use (creates default if None)
        """
        self.backup_manager = backup_manager or BackupManager()
    
    def write_file(self, filepath: str, content: str, 
                   parent_widget=None, create_backup: bool = True) -> bool:
        """
        Safely write content to file.
        
        Args:
            filepath: Path to file
            content: Content to write
            parent_widget: Parent widget for dialogs
            create_backup: Whether to create backup before writing
            
        Returns:
            True if write successful
        """
        filepath = Path(filepath)
        
        try:
            # Check if file exists and is read-only
            if filepath.exists():
                if not os.access(filepath, os.W_OK):
                    response = messagebox.askyesno(
                        "Read-Only File",
                        f"The file is read-only:\n{filepath}\n\n"
                        f"Attempt to make it writable?",
                        parent=parent_widget
                    )
                    if not response:
                        return False
                    
                    # Try to make writable
                    try:
                        os.chmod(filepath, 0o644)
                    except OSError as e:
                        messagebox.showerror(
                            "Error",
                            f"Cannot make file writable:\n{str(e)}",
                            parent=parent_widget
                        )
                        return False
                
                # Create backup
                if create_backup:
                    backup_path = self.backup_manager.create_backup(filepath)
                    if backup_path:
                        print(f"Created backup: {backup_path}")
            
            # Write to temporary file first (atomic write)
            temp_path = filepath.parent / f".{filepath.name}.tmp"
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Rename temp file to target (atomic on POSIX)
            temp_path.replace(filepath)
            
            return True
            
        except Exception as e:
            messagebox.showerror(
                "Write Error",
                f"Failed to write file:\n{filepath}\n\n"
                f"Error: {str(e)}",
                parent=parent_widget
            )
            return False
    
    def confirm_overwrite(self, filepath: str, parent_widget=None) -> bool:
        """
        Confirm overwriting an existing file.
        
        Args:
            filepath: Path to file
            parent_widget: Parent widget for dialog
            
        Returns:
            True if user confirms overwrite
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            return True
        
        response = messagebox.askyesno(
            "Confirm Overwrite",
            f"File already exists:\n{filepath}\n\n"
            f"Do you want to overwrite it?\n"
            f"(A backup will be created automatically)",
            parent=parent_widget
        )
        
        return response


# Convenience functions

def create_backup_before_edit(filepath: str, max_backups: int = 5) -> Optional[str]:
    """
    Create a backup before editing a file.
    
    Args:
        filepath: Path to file
        max_backups: Maximum backups to keep
        
    Returns:
        Path to backup file or None
    """
    manager = BackupManager(max_backups=max_backups)
    return manager.create_backup(filepath)


def restore_from_backup(filepath: str) -> bool:
    """
    Restore file from most recent backup.
    
    Args:
        filepath: Path to file
        
    Returns:
        True if restore successful
    """
    manager = BackupManager()
    return manager.confirm_restore(filepath)


def safe_write(filepath: str, content: str, parent_widget=None) -> bool:
    """
    Safely write content to file with backup.
    
    Args:
        filepath: Path to file
        content: Content to write
        parent_widget: Parent widget for dialogs
        
    Returns:
        True if write successful
    """
    writer = SafeFileWriter()
    return writer.write_file(filepath, content, parent_widget)
