"""Crowdstrike Plugin Helper."""

import requests
import time
from .constants import PLUGIN_NAME

class CrowdstrikePluginException(Exception):
    """Crowdstrike Plugin Exception."""
    pass

class CrowdstrikePluginHelper(object):
    """Crowdstrike Plugin Helper Class."""

    def __init__(self, logger, log_prefix, plugin_name, plugin_version):
        """Initialize Helper."""
        self.logger = logger
        self.log_prefix = log_prefix
        self.plugin_name = plugin_name
        self.plugin_version = plugin_version

    def api_helper(
        self,
        method,
        url,
        params=None,
        headers=None,
        data=None,
        json=None,
        is_validation=False,
        logger_msg=None,
        proxies=None,
        verify=True,
    ):
        """API Helper to perform HTTP requests."""
        if logger_msg:
            self.logger.debug(f"{self.log_prefix}: {logger_msg}")

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                data=data,
                json=json,
                proxies=proxies,
                verify=verify,
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                self.logger.error(
                    f"{self.log_prefix}: HTTP Request Failed. Status: {response.status_code}. Response: {response.text}"
                )
                raise CrowdstrikePluginException(f"API Error {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"{self.log_prefix}: Request Exception: {e}")
            raise CrowdstrikePluginException(f"Request Error: {e}")
        except Exception as e:
            self.logger.error(f"{self.log_prefix}: Unexpected Error: {e}")
            raise CrowdstrikePluginException(f"Unexpected Error: {e}")

    def get_auth_token(self, base_url, client_id, client_secret, proxies=None, verify=True):
        """Get OAuth2 Token."""
        auth_url = f"{base_url}/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        # Using api_helper might be recursive or specific, but here simple call is better to separate auth logic
        try:
            response = requests.post(auth_url, headers=headers, data=data, proxies=proxies, verify=verify)
            if response.status_code in [200, 201]:
                 return response.json().get("access_token")
            else:
                 raise CrowdstrikePluginException(f"Auth Failed: {response.text}")
        except Exception as e:
             raise CrowdstrikePluginException(f"Auth Exception: {e}")
