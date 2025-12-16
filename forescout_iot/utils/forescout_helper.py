"""
Forescout Plugin Helper.
"""

import time
import traceback
import requests
from typing import Dict, Union

from .forescout_constants import (
    MODULE_NAME,
    PLUGIN_NAME,
    MAX_RETRIES,
    RETRY_BACKOFF,
)

class ForescoutPluginHelper:
    """ForescoutPluginHelper class.

    Args:
        logger (logger): Logger object.
        log_prefix (str): Log prefix.
        plugin_name (str): Plugin name.
        plugin_version (str): Plugin version.
    """

    def __init__(
        self,
        logger,
        log_prefix: str,
        plugin_name: str,
        plugin_version: str,
        configuration: Dict,
    ):
        self.logger = logger
        self.log_prefix = log_prefix
        self.plugin_name = plugin_name
        self.plugin_version = plugin_version
        self.configuration = configuration

    def _add_user_agent(self, headers: Union[Dict, None] = None) -> Dict:
        """Add User-Agent to the headers.

        Args:
            headers (Dict): Headers dictionary.

        Returns:
            Dict: Headers dictionary with User-Agent.
        """
        if headers is None:
            headers = {}
        try:
            from netskope.common.utils import add_user_agent
            headers = add_user_agent(headers)
        except ImportError:
            # Fallback if netskope.common.utils is not available (e.g. in local test)
            headers["User-Agent"] = "netskope-ce"

        ce_added_agent = headers.get("User-Agent", "netskope-ce")
        user_agent = "{}-{}-{}-v{}".format(
            ce_added_agent,
            MODULE_NAME.lower(),
            self.plugin_name.lower().replace(" ", "-"),
            self.plugin_version,
        )
        headers.update({"User-Agent": user_agent})
        return headers

    def api_helper(
        self,
        url: str,
        method: str,
        params: Dict = None,
        data: Dict = None,
        headers: Dict = None,
        json: Dict = None,
        is_handle_error_required: bool = True,
        logger_msg: str = None,
        proxies: Dict = None,
        verify: bool = True,
    ) -> Union[Dict, requests.Response]:
        """API Helper to perform API request.

        Args:
            url (str): URL to perform request.
            method (str): Method to perform request.
            params (Dict, optional): Parameters. Defaults to None.
            data (Dict, optional): Data. Defaults to None.
            headers (Dict, optional): Headers. Defaults to None.
            json (Dict, optional): JSON. Defaults to None.
            is_handle_error_required (bool, optional): Handle error. Defaults to True.
            logger_msg (str, optional): Logger message. Defaults to None.
            proxies (Dict, optional): Proxies. Defaults to None.
            verify (bool, optional): Verify. Defaults to True.

        Returns:
            Union[Dict, requests.Response]: Response.
        """
        try:
            headers = self._add_user_agent(headers)
            for retry in range(MAX_RETRIES):
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    headers=headers,
                    json=json,
                    proxies=proxies,
                    verify=verify,
                )
                if response.status_code == 429:
                    if retry == MAX_RETRIES - 1:
                        self.logger.error(
                            f"{self.log_prefix}: Max retries reached for 429 error."
                        )
                        raise requests.exceptions.HTTPError(response=response)
                    time.sleep(RETRY_BACKOFF * (2 ** retry))
                    continue
                
                if is_handle_error_required:
                    self.handle_error(response, logger_msg)
                
                if response.status_code in [200, 201]:
                    try:
                        return response.json()
                    except ValueError:
                        return response
                
                return response
        except requests.exceptions.RequestException as exp:
            self.logger.error(
                message=(
                    f"{self.log_prefix}: Error occurred while {logger_msg}. "
                    f"Error: {exp}"
                ),
                details=str(traceback.format_exc()),
            )
            raise exp

    def handle_error(self, response: requests.Response, logger_msg: str):
        """Handle error.

        Args:
            response (requests.Response): Response object.
            logger_msg (str): Logger message.
        """
        if response.status_code in [200, 201]:
            return

        self.logger.error(
            message=(
                f"{self.log_prefix}: Error occurred while {logger_msg}. "
                f"Status Code: {response.status_code}. "
                f"Response: {response.text}"
            ),
            details=str(traceback.format_exc()),
        )
        raise requests.exceptions.HTTPError(response=response)
