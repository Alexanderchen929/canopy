import logging
import os

import requests

logger = logging.getLogger(__name__)


class AIFirewallError(ValueError):
    pass


class AIFirewall:

    def __init__(self) -> None:
        """Initialize the AI Firewall using required RI environment variables."""
        self.firewall_api_key = self._get_env_var("FIREWALL_API_KEY")
        self.firewall_url = self._get_env_var("FIREWALL_URL")
        self.firewall_instance_id = self._get_env_var("FIREWALL_INSTANCE_ID")
        self.firewall_instance_url = (
            f"{self.firewall_url}/v1-beta/firewall/{self.firewall_instance_id}/validate"
        )
        self.firewall_headers = {
            "X-Firewall-Api-Key": self.firewall_api_key.strip(),
        }

    @staticmethod
    def _get_env_var(var_name: str) -> str:
        env_var = os.environ.get(var_name)
        if not env_var:
            raise RuntimeError(
                f"{var_name} environment variable "
                f"is required to use security scanning."
            )
        return env_var

    def scan_text(self, text: str) -> bool:
        """Scan the input text for potential prompt injection attacks.

        Returns True if prompt injection attack is detected, False otherwise.

        This method sends the input text to the AI Firewall via REST
        API for security scanning. Documentation for the Validate
        endpoint on the Firewall can be found [here]
        (https://docs.robustintelligence.com/en/latest/reference/python-sdk.html#rime_sdk.FirewallClient)
        """
        stripped_text = text.replace("\n", " ")
        firewall_response = requests.put(
            self.firewall_instance_url,
            headers=self.firewall_headers,
            json={"user_input_text": stripped_text},
        )
        if not firewall_response.ok:
            raise AIFirewallError(
                f"AI Firewall returned status code "
                f"{firewall_response.status_code} "
                f"with reason: {firewall_response.reason}."
            )
        fw_result = firewall_response.json()["inputResults"]
        if (
                fw_result["FIREWALL_RULE_TYPE_PROMPT_INJECTION"]["action"]
                == "FIREWALL_ACTION_FLAG"
        ):
            return True
        else:
            logger.info("Document text passed security scanning.")
            return False
