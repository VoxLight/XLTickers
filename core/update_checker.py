"""
Auto-update checker for XLTickers.

Checks GitHub releases for new versions and notifies user if update available.
"""

import logging
import requests
from typing import Tuple, Optional
from packaging import version as pkg_version
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)

GITHUB_REPO = "VoxLight/XLTickers"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"
UPDATE_CHECK_INTERVAL_DAYS = 7  # Check for updates once per week


class UpdateChecker:
    """Check for and manage application updates."""
    
    def __init__(self, current_version: str, app_data_dir: Optional[str] = None):
        """
        Initialize update checker.
        
        Args:
            current_version: Current app version (e.g., '1.0.0')
            app_data_dir: Directory to store update check cache (optional)
        """
        self.current_version = current_version
        self.app_data_dir = Path(app_data_dir) if app_data_dir else Path.home() / ".xltickers"
        self.cache_file = self.app_data_dir / "update_check.json"
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
    
    def should_check_for_updates(self) -> bool:
        """
        Determine if enough time has passed since last check.
        
        Returns:
            True if should check, False if recently checked
        """
        if not self.cache_file.exists():
            return True
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                last_check = datetime.fromisoformat(cache.get('last_check', ''))
                time_since_check = datetime.now() - last_check
                
                if time_since_check > timedelta(days=UPDATE_CHECK_INTERVAL_DAYS):
                    return True
        except Exception as e:
            logger.debug(f"Error reading cache: {e}")
            return True
        
        return False
    
    def check_for_updates(self, channel: str = 'production') -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check GitHub releases for available updates.
        
        Args:
            channel: 'production' or 'nightly'
        
        Returns:
            Tuple of (update_available: bool, version: str, download_url: str)
        """
        if not self.should_check_for_updates():
            logger.debug("Skipping update check (checked recently)")
            return (False, None, None)
        
        try:
            # Update cache with current time
            self._update_cache_timestamp()
            
            # Fetch latest release based on channel
            if channel == 'nightly':
                latest_release = self._get_latest_nightly_release()
            else:
                latest_release = self._get_latest_production_release()
            
            if not latest_release:
                logger.warning(f"No {channel} releases found")
                return (False, None, None)
            
            latest_version = latest_release.get('tag_name', '').lstrip('v')
            download_url = self._get_installer_url(latest_release)
            
            if not download_url:
                logger.warning("No installer found in release assets")
                return (False, None, None)
            
            # Compare versions
            try:
                if pkg_version.parse(latest_version) > pkg_version.parse(self.current_version):
                    logger.info(f"Update available: {latest_version}")
                    return (True, latest_version, download_url)
            except Exception as e:
                logger.error(f"Error comparing versions: {e}")
                return (False, None, None)
            
            logger.debug(f"Current version {self.current_version} is up to date")
            return (False, None, None)
        
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return (False, None, None)
    
    def _get_latest_production_release(self) -> Optional[dict]:
        """Get the latest production release from GitHub."""
        try:
            response = requests.get(
                f"{GITHUB_API_URL}/releases/latest",
                timeout=5,
            )
            response.raise_for_status()
            
            release = response.json()
            # Skip if it's a prerelease
            if release.get('prerelease'):
                return None
            
            return release
        except Exception as e:
            logger.error(f"Error fetching production release: {e}")
            return None
    
    def _get_latest_nightly_release(self) -> Optional[dict]:
        """Get the latest nightly release from GitHub."""
        try:
            response = requests.get(
                f"{GITHUB_API_URL}/releases",
                timeout=5,
            )
            response.raise_for_status()
            
            releases = response.json()
            # Find first nightly release
            for release in releases:
                if release.get('tag_name') == 'nightly' and release.get('prerelease'):
                    return release
            
            return None
        except Exception as e:
            logger.error(f"Error fetching nightly release: {e}")
            return None
    
    def _get_installer_url(self, release: dict) -> Optional[str]:
        """Extract installer URL from release assets."""
        try:
            assets = release.get('assets', [])
            
            # Look for installer exe first
            for asset in assets:
                if asset['name'].endswith('-Installer.exe'):
                    return asset['browser_download_url']
            
            # Fall back to zip
            for asset in assets:
                if asset['name'].endswith('.zip'):
                    return asset['browser_download_url']
            
            return None
        except Exception as e:
            logger.error(f"Error extracting installer URL: {e}")
            return None
    
    def _update_cache_timestamp(self) -> None:
        """Update the timestamp in the cache file."""
        try:
            cache = {}
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
            
            cache['last_check'] = datetime.now().isoformat()
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            logger.error(f"Error updating cache: {e}")


def check_and_notify_update(
    current_version: str,
    channel: str = 'production',
    interactive: bool = True
) -> Optional[str]:
    """
    Check for updates and optionally notify user.
    
    Args:
        current_version: Current app version
        channel: 'production' or 'nightly'
        interactive: Whether to show user prompts
    
    Returns:
        Download URL if update available, None otherwise
    """
    checker = UpdateChecker(current_version)
    update_available, latest_version, download_url = checker.check_for_updates(channel)
    
    if update_available:
        if interactive:
            print("\n" + "="*50)
            print("UPDATE AVAILABLE")
            print("="*50)
            print(f"Current version: {current_version}")
            print(f"Latest version: {latest_version}")
            print(f"Channel: {channel}")
            print("\nDownload from GitHub Releases:")
            print(f"https://github.com/{GITHUB_REPO}/releases")
            print("="*50 + "\n")
        
        return download_url
    
    return None
