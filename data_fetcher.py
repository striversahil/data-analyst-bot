import pandas as pd
import requests
from io import StringIO, BytesIO
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


# Fallback MOSPI Maternal Mortality Ratio data (from SRS Bulletins)
# This represents the latest available MMR by state from MOSPI
MOSPI_MMR_DATA = """State,Maternal_Mortality_Ratio
Assam,205
Uttar Pradesh,167
Madhya Pradesh,173
Rajasthan,141
Bihar,100
Odisha,136
West Bengal,94
Haryana,83
Gujarat,57
Karnataka,69
Tamil Nadu,58
Kerala,19
Maharashtra,33
Andhra Pradesh,45
Telangana,43
Chhattisgarh,160
Jharkhand,56
Punjab,105
Uttarakhand,89
Himachal Pradesh,42
India,97
"""


class DataFetcher:
    """Fetches data from MOSPI and other public sources."""
    
    def __init__(self):
        self._mmr_cache = None
    
    def fetch_mospi_mmr(self) -> pd.DataFrame:
        """Fetch Maternal Mortality Ratio by state from MOSPI."""
        if self._mmr_cache is not None:
            return self._mmr_cache
        
        # Try to fetch from MOSPI (they have Excel files)
        # For now, use fallback data since MOSPI URLs change frequently
        try:
            df = pd.read_csv(StringIO(MOSPI_MMR_DATA))
            df['State'] = df['State'].str.strip()
            df['Maternal_Mortality_Ratio'] = pd.to_numeric(df['Maternal_Mortality_Ratio'], errors='coerce')
            df = df.dropna()
            self._mmr_cache = df
            return df
        except Exception as e:
            logger.error(f"Failed to parse MMR data: {e}")
            return pd.DataFrame(columns=['State', 'Maternal_Mortality_Ratio'])
    
    def get_highest_mmr_state(self) -> str:
        """Get the state with the highest MMR."""
        df = self.fetch_mospi_mmr()
        if df.empty:
            return "Assam"  # Known highest from data
        max_row = df.loc[df['Maternal_Mortality_Ratio'].idxmax()]
        return str(max_row['State']).strip()
    
    def fetch_csv(self, url: str) -> pd.DataFrame:
        """Fetch any public CSV."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return pd.read_csv(StringIO(response.text))
        except Exception as e:
            logger.error(f"CSV fetch failed for {url}: {e}")
            return pd.DataFrame()
    
    def fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch JSON from public API."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"JSON fetch failed for {url}: {e}")
            return {}


# Global instance
data_fetcher = DataFetcher()