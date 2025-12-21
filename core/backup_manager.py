"""
File backup and management module.

Handles creating timestamped backups of Excel files and managing
backup retention policies.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
import os

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Manages Excel file backups with timestamped filenames.
    
    Features:
    - Creates new files with timestamp suffix instead of overwriting originals
    - Preserves original file unchanged
    - Manages backup retention (keeps N recent versions)
    - Returns path to the new backup file
    """
    
    def __init__(self, keep_backups: int = 5):
        """
        Initialize backup manager.
        
        Args:
            keep_backups: Number of recent backups to keep (0 = keep all)
        """
        self.keep_backups = keep_backups
    
    @staticmethod
    def generate_backup_filename(original_path: str) -> str:
        """
        Generate timestamped backup filename from original.
        
        Args:
            original_path: Path to original file (e.g., "data.xlsx")
        
        Returns:
            New filename with timestamp (e.g., "data_2025-12-21_143052.xlsx")
        """
        path = Path(original_path)
        
        # Get timestamp with seconds precision
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # Create new filename: name_TIMESTAMP.ext
        name_part = path.stem  # "data" from "data.xlsx"
        ext_part = path.suffix  # ".xlsx"
        
        new_filename = f"{name_part}_{timestamp}{ext_part}"
        
        # Return full path in same directory as original
        new_path = path.parent / new_filename
        
        return str(new_path)
    
    def save_backup(self, workbook, original_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        Save workbook to a timestamped backup file.
        
        Args:
            workbook: openpyxl Workbook object
            original_path: Path to original Excel file
        
        Returns:
            Tuple of (success: bool, backup_path: str, error: Optional[str])
                success: True if save succeeded
                backup_path: Path to the new backup file
                error: Error message if failed, None otherwise
        """
        try:
            # Generate timestamped backup filename
            backup_path = self.generate_backup_filename(original_path)
            
            # Cleanup old backups BEFORE saving to ensure we don't lose them
            # if the new save fails
            self._cleanup_old_backups(original_path)
            
            # Save to backup location with error handling
            try:
                workbook.save(backup_path)
            except Exception as save_error:
                # If save failed, log detailed error
                error_msg = f"Failed to save backup file: {str(save_error)}"
                logger.error(error_msg)
                # Try to remove the partial/corrupted file
                try:
                    Path(backup_path).unlink()
                except:
                    pass
                return False, "", error_msg
            
            logger.info(f"Saved backup to: {backup_path}")
            return True, backup_path, None
        
        except PermissionError:
            error_msg = (
                f"Cannot save backup file. "
                f"Is the original file open in Excel?"
            )
            logger.error(error_msg)
            return False, "", error_msg
        
        except Exception as e:
            error_msg = f"Backup operation failed: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def _cleanup_old_backups(self, original_path: str) -> None:
        """
        Remove old backup files, keeping only recent ones.
        
        Args:
            original_path: Path to original file (used to find related backups)
        """
        if self.keep_backups == 0:
            return  # Keep all backups
        
        try:
            path = Path(original_path)
            name_stem = path.stem
            ext = path.suffix
            
            # Find all backup files for this original
            # Pattern: name_YYYY-MM-DD_HHMMSS.ext
            backups = []
            for file in path.parent.glob(f"{name_stem}_*{ext}"):
                # Check if filename matches backup pattern
                if "_" in file.stem and len(file.stem) > len(name_stem):
                    backups.append(file)
            
            # Sort by modification time, newest first
            backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove old backups beyond keep_backups limit
            for old_backup in backups[self.keep_backups:]:
                try:
                    old_backup.unlink()  # Delete file
                    logger.info(f"Deleted old backup: {old_backup}")
                except Exception as e:
                    logger.warning(f"Could not delete old backup {old_backup}: {e}")
        
        except Exception as e:
            logger.warning(f"Backup cleanup failed: {e}")
    
    def list_backups(self, original_path: str) -> list:
        """
        List all backup files for an original file.
        
        Args:
            original_path: Path to original file
        
        Returns:
            List of backup file paths, sorted newest first
        """
        try:
            path = Path(original_path)
            name_stem = path.stem
            ext = path.suffix
            
            backups = []
            for file in path.parent.glob(f"{name_stem}_*{ext}"):
                if "_" in file.stem and len(file.stem) > len(name_stem):
                    backups.append(str(file))
            
            # Sort newest first
            backups.sort(reverse=True)
            return backups
        
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []


# Singleton instance
_backup_manager = None


def get_backup_manager(keep_backups: int = 5) -> BackupManager:
    """
    Get or create the global backup manager instance.
    
    Args:
        keep_backups: Number of recent backups to keep
    
    Returns:
        BackupManager instance
    """
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager(keep_backups=keep_backups)
    return _backup_manager
