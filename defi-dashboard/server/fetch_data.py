import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fetch_data.log')
    ]
)

# Constants
BASE_URL = "https://api.llama.fi"
PROTOCOLS = {
    "aave": ["aave", "aave-v2", "aave-v3"],
    "compound": ["compound-finance", "compound-v1", "compound-v2", "compound-v3"],
    "lido": ["lido"],
    "fluid": ["fluid", "fluid-lending"],
    "jupiter": ["jupiter", "jupiter-aggregator"],
    "sonic": ["sonic"]
}

class DefiLlamaAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'DeFi-Dashboard/1.0'
        })
        
        # Ensure data directories exist
        os.makedirs('data/raw', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)

    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """
        Make a GET request to the DefiLlama API with error handling.
        
        Args:
            endpoint (str): API endpoint to query
            
        Returns:
            Optional[Dict]: JSON response or None if request fails
        """
        try:
            url = f"{BASE_URL}{endpoint}"
            logging.info(f"Fetching data from: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching {endpoint}: {str(e)}")
            return None

    def fetch_protocol_data(self, protocol: str) -> Optional[Dict]:
        """
        Fetch TVL and other metrics for a specific protocol.
        
        Args:
            protocol (str): Protocol identifier
            
        Returns:
            Optional[Dict]: Protocol data or None if request fails
        """
        return self._make_request(f"/protocol/{protocol}")

    def fetch_protocol_fees(self, protocol: str) -> Optional[Dict]:
        """
        Fetch fees and revenue data for a specific protocol.
        
        Args:
            protocol (str): Protocol identifier
            
        Returns:
            Optional[Dict]: Fee data or None if request fails
        """
        return self._make_request(f"/summary/fees/{protocol}")

    def fetch_all_data(self) -> Dict:
        """
        Fetch all required data for supported protocols.
        
        Returns:
            Dict: Combined protocol data
        """
        all_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "protocols": {}
        }

        for protocol_group, protocol_ids in PROTOCOLS.items():
            all_data["protocols"][protocol_group] = {
                "versions": {},
                "aggregated": {
                    "tvl": 0,
                    "fees": 0,
                    "revenue": 0
                }
            }
            
            for protocol_id in protocol_ids:
                logging.info(f"Fetching data for {protocol_id}")
                
                # Fetch TVL and general protocol data
                protocol_data = self.fetch_protocol_data(protocol_id)
                if protocol_data:
                    # Fetch fees and revenue data
                    fee_data = self.fetch_protocol_fees(protocol_id)
                    
                    # Handle TVL data which might be a dict with chain breakdown
                    tvl_data = protocol_data.get("tvl", 0)
                    if isinstance(tvl_data, dict):
                        tvl_value = sum(tvl_data.values())
                    elif isinstance(tvl_data, list) and tvl_data:
                        tvl_value = tvl_data[-1]  # Take the latest TVL value
                    else:
                        tvl_value = float(tvl_data) if tvl_data else 0

                    # Handle fees and revenue data which might be in different formats
                    fees = fee_data.get("totalFees", 0) if fee_data else 0
                    revenue = fee_data.get("totalRevenue", 0) if fee_data else 0
                    
                    # Convert fees and revenue to float
                    fees = float(fees) if fees else 0
                    revenue = float(revenue) if revenue else 0
                    
                    
                    # Store individual version data
                    all_data["protocols"][protocol_group]["versions"][protocol_id] = protocol_metrics
                    
                    # Update aggregated metrics
                    all_data["protocols"][protocol_group]["aggregated"]["tvl"] += protocol_metrics["tvl"]
                    all_data["protocols"][protocol_group]["aggregated"]["fees"] += protocol_metrics["fees"]
                    all_data["protocols"][protocol_group]["aggregated"]["revenue"] += protocol_metrics["revenue"]
                
                else:
                    logging.error(f"Failed to fetch data for {protocol_id}")

        return all_data

    def save_data(self, data: Dict):
        """
        Save the collected data to a JSON file.
        
        Args:
            data (Dict): Data to save
        """
        try:
            filepath = 'data/raw/protocol_data.json'
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logging.info(f"Data successfully saved to {filepath}")
            
        except IOError as e:
            logging.error(f"Error saving data: {str(e)}")

def main():
    """Main execution function."""
    try:
        api = DefiLlamaAPI()
        data = api.fetch_all_data()
        api.save_data(data)
        logging.info("Data collection completed successfully")
        
    except Exception as e:
        logging.error(f"Unexpected error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
