"""
Forescout Plugin Main File.
"""

import traceback
from typing import List, Dict, Tuple

from netskope.integrations.iot.models.asset import Asset
from netskope.integrations.iot.plugin_base import (
    IotPluginBase,
    ValidationResult,
)

from .utils.forescout_constants import (
    MODULE_NAME,
    PLUGIN_NAME,
    PLUGIN_VERSION,
    API_ENDPOINTS,
)
from .utils.forescout_helper import ForescoutPluginHelper

class ForescoutPlugin(IotPluginBase):
    """ForescoutPlugin class."""

    def __init__(
        self,
        name,
        *args,
        **kwargs,
    ):
        """Init method."""
        super().__init__(
            name,
            *args,
            **kwargs,
        )
        self.proxy = kwargs.get("proxy", {})
        self.plugin_name, self.plugin_version = self._get_plugin_info()
        self.log_prefix = f"{MODULE_NAME} {self.plugin_name} [{name}]"
        self.forescout_helper = ForescoutPluginHelper(
            logger=self.logger,
            log_prefix=self.log_prefix,
            plugin_name=self.plugin_name,
            plugin_version=self.plugin_version,
            configuration=self.configuration,
        )

    def _get_plugin_info(self) -> Tuple[str, str]:
        """Get plugin name and version from metadata."""
        try:
            metadata_json = ForescoutPlugin.metadata
            plugin_name = metadata_json.get("name", PLUGIN_NAME)
            plugin_version = metadata_json.get("version", PLUGIN_VERSION)
            return plugin_name, plugin_version
        except Exception as exp:
            self.logger.error(
                message=(
                    f"{MODULE_NAME} {PLUGIN_NAME}: Error occurred while"
                    f" getting plugin details. Error: {exp}"
                ),
                details=str(traceback.format_exc()),
            )
        return PLUGIN_NAME, PLUGIN_VERSION

    def pull(self):
        """Pull assets from Forescout."""
        self.logger.info(f"{self.log_prefix}: Fetching assets.")
        
        try:
            base_url = self.configuration.get("base_url", "").strip().rstrip("/")
            url = API_ENDPOINTS["hosts"].format(base_url)
            
            # Placeholder for headers/auth
            headers = {
                "Authorization": f"Bearer {self.configuration.get('api_token')}"
            }

            response = self.forescout_helper.api_helper(
                url=url,
                method="GET",
                headers=headers,
                proxies=self.proxy,
                verify=self.ssl_validation,
                logger_msg="fetching assets",
            )
            
            # DEBUG LOGGING
            self.logger.info(f"{self.log_prefix}: Raw API Response: {response}")
            
            assets = []
            
            # Handle different possible response structures
            if isinstance(response, dict):
                hosts = response.get("hosts", response.get("data", []))
            elif isinstance(response, list):
                hosts = response
            else:
                hosts = []
                self.logger.error(f"{self.log_prefix}: Unexpected API response format: {type(response)}")

            for item in response:
                asset = Asset(
                    mac_address=item.get("mac"),
                    ip=item.get("ip"),
                    hostname=item.get("hostname"),
                    os=item.get("os"),
                    manufacturer=item.get("vendor"),
                    use_asset=True
                )
                assets.append(asset)

            self.logger.info(f"{self.log_prefix}: Successfully fetched {len(assets)} assets.")
            
            # Yield tuple as per IotPluginBase requirements
            # (assets, is_first_page, is_last_page, count, total_count_placeholder)
            yield assets, True, True, len(assets), 0

        except Exception as exp:
            self.logger.error(
                message=f"{self.log_prefix}: Error fetching assets: {exp}",
                details=str(traceback.format_exc())
            )
            raise exp

    def validate(self, configuration: Dict) -> ValidationResult:
        """Validate configuration."""
        base_url = configuration.get("base_url", "").strip()
        api_token = configuration.get("api_token", "").strip()

        if not base_url:
            return ValidationResult(success=False, message="Base URL is required.")
        
        if not api_token:
             return ValidationResult(success=False, message="API Token is required.")

        return ValidationResult(success=True, message="Validation successful.")


