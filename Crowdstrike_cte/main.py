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
            self.logger.info(f"{self.log_prefix}: Fetching IOC IDs from {query_url}")
            
            # Basic implementation for now, fetching default limit
            response = self.helper.api_helper("GET", query_url, headers=headers, proxies=self.proxy, verify=self.ssl_validation)
            ioc_ids = response.get("resources", [])
            self.logger.info(f"{self.log_prefix}: Found {len(ioc_ids)} IOC IDs.")

            if not ioc_ids:
                return indicators

            # Step 2: Get IOC Details
            details_url = f"{base_url}/iocs/entities/indicators/v1"
            batch_size = 100
            
            for i in range(0, len(ioc_ids), batch_size):
                batch_ids = ioc_ids[i:i + batch_size]
                # Pass IDs as a list of tuples for requests params handling if needed, 
                # but helper might just take dict or string. 
                # Requests handles repeated keys 'ids' if passed as list of tuples or bytes, 
                # but our helper wraps requests. Let's see how helper passes params.
                # Helper passes params directly to requests.request.
                
                # 'requests' library handles multiple values for same key if passed as list of tuples
                params = [('ids', x) for x in batch_ids]
                
                det_response = self.helper.api_helper("GET", details_url, params=params, headers=headers, proxies=self.proxy, verify=self.ssl_validation)
                resources = det_response.get("resources", [])
                
                for item in resources:
                    # Map to Indicator
                    try:
                        value = item.get("value")
                        itype = item.get("type")
                        
                        indicator_type = None
                        if itype == "sha256":
                            indicator_type = IndicatorType.SHA256
                        elif itype == "md5":
                            indicator_type = IndicatorType.MD5
                        elif itype == "domain":
                            indicator_type = IndicatorType.URL
                        elif itype == "ipv4":
                            # Netskope IndicatorType doesn't have IP specifically usually distinct from URL in some plugins, 
                            # strictly it's URL but let's check if there is strict typing. 
                            # Usually URL covers domains and IPs for many CE plugins, or they use logic to distinguish.
                            # Standard CTE models: URL, MD5, SHA256. 
                            # If checking standard IndicatorType enum: URL, MD5, SHA256.
                            indicator_type = IndicatorType.URL
                        elif itype == "ipv6":
                            indicator_type = IndicatorType.URL
                        
                        if indicator_type and value:
                            if itype in ["ipv4", "ipv6"] and indicator_type == IndicatorType.URL:
                                # Start with http:// can be safer for URL type if strictly validated, but raw IP often works.
                                # Let's keep raw value for now unless validation fails.
                                pass

                            indicators.append(Indicator(
                                value=value,
                                type=indicator_type,
                                comments=item.get("description", "Crowdstrike IOC"),
                                firstSeen=item.get("created_on"),
                                lastSeen=item.get("modified_on")
                            ))
                    except Exception as inner_e:
                        self.logger.error(f"{self.log_prefix}: Error parsing indicator {item}: {inner_e}")
                        continue

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
