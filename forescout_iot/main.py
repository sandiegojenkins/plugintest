"""
Forescout Plugin Main File.
"""

import requests
import traceback
import time
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
    DEFAULT_LOOKBACK_MINS,
    REM_ASSET_FIELDS,
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
            url = API_ENDPOINTS["rem_assets"].format(base_url)
            
            headers = {
                "Authorization": f"Bearer {self.configuration.get('api_token')}",
                "Content-Type": "application/json"
            }

            # Determine time window
            current_time_ms = int(time.time() * 1000)
            lookback_ms = DEFAULT_LOOKBACK_MINS * 60 * 1000
            
            page_number = 0
            has_more_data = True
            
            while has_more_data:
                payload = {
                     "from_utc_millis": current_time_ms - lookback_ms,
                     "to_utc_millis": current_time_ms,
                     "selected_fields": REM_ASSET_FIELDS,
                     "page_number": page_number
                }
                
                self.logger.info(f"{self.log_prefix}: Fetching page {page_number}.")

                response = self.forescout_helper.api_helper(
                    url=url,
                    method="POST",
                    headers=headers,
                    proxies=self.proxy,
                    verify=self.ssl_validation,
                    logger_msg=f"fetching assets page {page_number}",
                    json=payload
                )

                if isinstance(response, dict):
                    results = response.get("results", [])
                else:
                    self.logger.error(f"{self.log_prefix}: Unexpected API response format: {type(response)}")
                    results = []

                if not results:
                    self.logger.info(f"{self.log_prefix}: No more results found on page {page_number}.")
                    break

                assets = []
                for item in results:
                    ip_list = item.get("ip_addresses", [])
                    mac_list = item.get("mac_addresses", [])
                    
                    ip_address = ip_list[0] if ip_list else None
                    mac_address = mac_list[0] if mac_list else None
                    
                    # We need at least an IP or MAC/Hostname to create an asset
                    if ip_address or mac_address:
                        
                        asset_tags = []
                        if item.get("rem_function"):
                             asset_tags.append(f"Function: {item.get('rem_function')}")
                        if "risk_score" in item:
                             asset_tags.append(f"Risk Score: {item.get('risk_score')}")

                        asset = Asset(
                            ip=ip_address,
                            mac_address=mac_address,
                            tags=asset_tags,
                            use_asset=True
                        )
                        
                        # Add extended attributes
                        if item.get("rem_os"):
                            asset.os = item.get("rem_os")
                        
                        if item.get("rem_vendor"):
                            asset.manufacturer = item.get("rem_vendor")
                        
                        if item.get("rem_category"):
                            asset.category = item.get("rem_category")
                            
                        assets.append(asset)
                
                self.logger.info(f"{self.log_prefix}: Successfully fetched {len(assets)} assets from page {page_number}.")
                
                # Yield tuple: (assets, is_first_page, is_last_page, count, total_count_placeholder)
                # Since we don't know total count or if this is the last page definitively until we get empty results next time, defines logic here.
                # Actually for this iterator pattern we can just yield.
                # If we received less than we asked for (implied batch size), maybe we are done? 
                # The API doesn't seem to document page size in the request provided, assuming server side default.
                
                yield assets, page_number == 0, False, len(assets), 0
                
                page_number += 1
                
                # Sanity check to prevent infinite loops if API is misbehaving
                if page_number > 1000:
                    self.logger.warning(f"{self.log_prefix}: Reached maximum page limit.")
                    break

        except requests.exceptions.RequestException as exp:
            self.logger.error(
                message=f"{self.log_prefix}: API Error fetching assets: {exp}",
                details=str(traceback.format_exc())
            )
            raise exp
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
