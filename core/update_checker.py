"""
Auto-update checker for XLTickers.

Checks GitHub releases for new versions. This module handles fetching only.
For user prompting, use core.update_ui instead.
"""

import logging
import requests
from typing import Tuple, Optional
from packaging import version as pkg_version

logger = logging.getLogger(__name__)

GITHUB_REPO = "VoxLight/XLTickers"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"


class UpdateChecker:
    """Check for and manage application updates from GitHub."""
    
    def __init__(self, current_version: str):
        """
        Initialize update checker.
        
        Args:
            current_version: Current app version (e.g., '1.0.0')
        """
        self.current_version = current_version
    
    def check_for_updates(self, channel: str = 'production') -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check GitHub releases for available updates.
        
        Always checks, regardless of when last check occurred.
        
        Args:
            channel: 'production' or 'nightly'
        
        Returns:
            Tuple of (update_available: bool, version: str, download_url: str)
        """
        try:
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
    

