"""
Crowdstrike CTE Plugin implementation.
"""

from netskope.integrations.cte.plugin_base import PluginBase, ValidationResult, PushResult
from netskope.integrations.cte.models import Indicator, IndicatorType
from typing import Dict, List, Tuple
from .utils.constants import (
    PLUGIN_NAME,
    PLUGIN_VERSION,
    MODULE_NAME,
    PLATFORM_NAME
)
from .utils.helper import CrowdstrikePluginHelper, CrowdstrikePluginException

class CrowdstrikePlugin(PluginBase):
    """The Crowdstrike CTE plugin implementation."""

    def __init__(self, name, *args, **kwargs):
        """Init."""
        super().__init__(name, *args, **kwargs)
        self.plugin_name, self.plugin_version = self._get_plugin_info()
        self.log_prefix = f"{MODULE_NAME} {self.plugin_name}"
        if name:
            self.log_prefix = f"{self.log_prefix} [{name}]"
        self.helper = CrowdstrikePluginHelper(
            self.logger, self.log_prefix, self.plugin_name, self.plugin_version
        )

    def _get_plugin_info(self) -> Tuple[str, str]:
        """Get plugin name and version from manifest."""
        try:
            manifest_json = CrowdstrikePlugin.metadata
            plugin_name = manifest_json.get("name", PLUGIN_NAME)
            plugin_version = manifest_json.get("version", PLUGIN_VERSION)
            return plugin_name, plugin_version
        except Exception as exp:
            self.logger.error(f"Error getting plugin details: {exp}")
        return PLUGIN_NAME, PLUGIN_VERSION

    def pull(self) -> List[Indicator]:
        """Pull indicators from Crowdstrike."""
        indicators = []
        try:
            base_url = self.configuration.get("base_url").strip().rstrip("/")
            client_id = self.configuration.get("client_id")
            client_secret = self.configuration.get("client_secret")
            
            token = self.helper.get_auth_token(base_url, client_id, client_secret, proxies=self.proxy, verify=self.ssl_validation)
            headers = {"Authorization": f"Bearer {token}"}
            
            # Step 1: Get IOC IDs
            query_url = f"{base_url}/iocs/queries/indicators/v1"
            # Logic to handle pages/limits would go here. For now, basic implementation.
            
            # Placeholder for pulling logic using helper
            # ...
            
            self.logger.info(f"{self.log_prefix}: Pulled {len(indicators)} indicators.")
        except Exception as e:
            self.logger.error(f"{self.log_prefix}: Error pulling indicators: {e}")
            raise
        
        return indicators

    def push(self, indicators: List[Indicator], action_dict: Dict) -> PushResult:
        """Push indicators to Crowdstrike."""
        try:
            # Push logic here
            return PushResult(success=True, message="Success")
        except Exception as e:
            self.logger.error(f"{self.log_prefix}: Error pushing indicators: {e}")
            return PushResult(success=False, message=str(e))

    def validate(self, configuration: Dict) -> ValidationResult:
        """Validate configuration."""
        try:
            base_url = configuration.get("base_url", "").strip().rstrip("/")
            client_id = configuration.get("client_id")
            client_secret = configuration.get("client_secret")
            
            if not base_url or not client_id or not client_secret:
                return ValidationResult(success=False, message="Missing required fields.")
            
            token = self.helper.get_auth_token(base_url, client_id, client_secret, proxies=self.proxy, verify=self.ssl_validation)
            if token:
                return ValidationResult(success=True, message="Validation Successful.")
            else:
                return ValidationResult(success=False, message="Validation Failed.")
                
        except Exception as e:
            self.logger.error(f"{self.log_prefix}: Validation error: {e}")
            return ValidationResult(success=False, message=str(e))
