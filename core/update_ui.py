"""
Update UI module - handles user prompting for updates.

This module is separate from update_checker.py so it can be used by both
CLI (prompts in terminal) and GUI (dialogs) without duplicating logic.

Usage:
    from core.update_ui import prompt_for_update
    download_url = prompt_for_update(current_version, channel='production')
"""

import logging
import webbrowser
import os
from typing import Optional
from core.update_checker import UpdateChecker

logger = logging.getLogger(__name__)


def prompt_for_update(
    current_version: str,
    channel: str = 'production',
    auto_download: bool = True
) -> Optional[str]:
    """
    Check for updates and prompt user if available.
    
    This is the main entry point for update checking. It:
    1. Checks GitHub for new releases
    2. If update found, prompts user with options
    3. Can auto-open browser to download if desired
    
    Args:
        current_version: Current app version
        channel: 'production' or 'nightly'
        auto_download: If True, open browser to download page
        
    Returns:
        Download URL if user wants to update, None otherwise
    """
    checker = UpdateChecker(current_version)
    update_available, latest_version, download_url = checker.check_for_updates(channel)
    
    if not update_available:
        logger.info(f"Current version {current_version} is up to date")
        return None
    
    # Update is available - prompt user
    return _prompt_update_available(
        current_version=current_version,
        latest_version=latest_version,
        download_url=download_url,
        channel=channel,
        auto_download=auto_download
    )


def _prompt_update_available(
    current_version: str,
    latest_version: str,
    download_url: str,
    channel: str,
    auto_download: bool
) -> Optional[str]:
    """
    Internal: Prompt user about available update.
    
    Returns:
        Download URL if user says yes, None if no/cancel
    """
    print("\n" + "="*60)
    print("🔄 UPDATE AVAILABLE")
    print("="*60)
    print(f"Current version:  {current_version}")
    print(f"Latest version:   {latest_version}")
    print(f"Release channel:  {channel.upper()}")
    print("="*60)
    
    # Get user response
    while True:
        response = input("\nWould you like to download and install the update? (y/n): ").strip().lower()
        
        if response in ('y', 'yes'):
            if auto_download:
                print("\nOpening download page in your browser...")
                webbrowser.open(download_url)
            else:
                print(f"\nDownload link: {download_url}")
            
            logger.info(f"User initiated update to {latest_version}")
            return download_url
        
        elif response in ('n', 'no'):
            print("\nYou can update manually from:")
            print(f"https://github.com/VoxLight/XLTickers/releases")
            logger.info(f"User skipped update to {latest_version}")
            return None
        
        else:
            print("Please enter 'y' or 'n'")


def get_version_info(current_version: str, channel: str = 'production') -> dict:
    """
    Get detailed version information for display.
    
    Useful for about dialogs and status displays.
    
    Args:
        current_version: Current app version
        channel: Release channel
        
    Returns:
        Dict with version info: {
            'current': str,
            'channel': str,
            'update_available': bool,
            'latest': str or None,
            'download_url': str or None
        }
    """
    checker = UpdateChecker(current_version)
    update_available, latest_version, download_url = checker.check_for_updates(channel)
    
    return {
        'current': current_version,
        'channel': channel,
        'update_available': update_available,
        'latest': latest_version if update_available else None,
        'download_url': download_url if update_available else None,
    }
