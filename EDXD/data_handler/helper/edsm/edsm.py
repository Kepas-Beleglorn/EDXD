import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

EDSM_BASE_URL: str = "https://www.edsm.net/"
EDSM_SYSTEM_BODIES_API: str = EDSM_BASE_URL + "api-system-v1/bodies"


class EdsmHelper:
    """Helper class for querying the EDSM (Elite Dangerous Star Map) API."""

    def __init__(self):
        self._user_agent = "EDXD (Python)"

    def get_star_class_from_edsm(self, system_id: int) -> Optional[str]:
        """
        Query EDSM for the spectral class of the star in the given system.
        
        Args:
            system_id: The id64 (SystemAddress) of the star system.
            
        Returns:
            The spectral class string (e.g., "G2", "K5", "N") or None if not found.
        """
        url = EDSM_SYSTEM_BODIES_API
        params = {"systemId64": system_id}
        headers = {"User-Agent": self._user_agent}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            return None

        try:
            data = response.json()
            bodies = data.get("bodies", [])
            
            for body in bodies:
                if body.get("type") == "Star":
                    spectral_class = body.get("spectralClass")
                    if spectral_class:
                        # Extract only the alphabetic characters (e.g., "G2" -> "G")
                        return "".join(char for char in spectral_class if char.isalpha())
                    else:
                        # Fallback: try to extract from subType, similar to Spansh logic
                        sub_type = body.get("subType", "")
                        if sub_type:
                            if "(" in sub_type:
                                class_part = sub_type.split("(")[1].split(")")[0]
                                return "".join(char for char in class_part if char.isalpha())
                            elif sub_type == "Neutron Star":
                                return "N"
                            else:
                                return sub_type
            return None
        except (KeyError, TypeError, IndexError):
            return None
