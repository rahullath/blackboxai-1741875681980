import os
import json
import logging
import requests
from datetime import datetime
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
    "makerdao": ["maker", "makerdao"]
}

CHAINS = ["ethereum", "solana", "sonic", "arbitrum", "optimism", "polygon", "mantle", "scroll", "base", "avalanche", "bsc", "tron", "hyperliquid-l1", "op-mainnet", "moonbeam", "moonriver"]

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

    def fetch_protocol_fees(self, protocol: str, data_type: str = "dailyFees") -> Optional[Dict]:
        """
        Fetch fees and revenue data for a specific protocol.
        
        Args:
            protocol (str): Protocol identifier
            data_type (str): Type of data to fetch (dailyFees, dailyRevenue)
            
        Returns:
            Optional[Dict]: Fee data or None if request fails
        """
        return self._make_request(f"/summary/fees/{protocol}?dataType={data_type}")

    def fetch_chain_data(self, chain: str, data_type: str = "dailyRevenue") -> Optional[Dict]:
        """
        Fetch fees and revenue data for a specific chain.
        
        Args:
            chain (str): Chain identifier
            data_type (str): Type of data to fetch (dailyFees, dailyRevenue)
            
        Returns:
            Optional[Dict]: Chain data or None if request fails
        """
        return self._make_request(f"/overview/fees/{chain}?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true&dataType={data_type}")

    def aggregate_monthly_revenue(self, daily_data: List[List]) -> Dict:
        """
        Aggregate daily revenue data by month.
        
        Args:
            daily_data (List[List]): Daily revenue data
            
        Returns:
            Dict: Monthly aggregated revenue data
        """
        monthly_revenue = {}

        for entry in daily_data:
            timestamp = entry[0]
            revenue = entry[1]  # Assuming revenue is part of the entry
            
            # Convert timestamp to datetime object
            date = datetime.utcfromtimestamp(timestamp)
            year_month = f"{date.year}-{date.month:02d}"  # String (year-month)

            # Aggregate revenue
            if year_month not in monthly_revenue:
                monthly_revenue[year_month] = 0
            monthly_revenue[year_month] += revenue

        return monthly_revenue

    def fetch_all_data(self) -> Dict:
        """
        Fetch all required data for supported protocols and chains.
        
        Returns:
            Dict: Combined protocol and chain data
        """
        all_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "protocols": {},
            "chains": {}
        }

        for protocol_group, protocol_ids in PROTOCOLS.items():
            all_data["protocols"][protocol_group] = {
                "versions": {},
                "aggregated": {
                    "tvl": 0,
                    "fees": 0,
                    "revenue": 0
                },
                "monthly_revenue": {}
            }
            
            for protocol_id in protocol_ids:
                logging.info(f"Fetching data for {protocol_id}")
                
                # Fetch TVL and general protocol data
                protocol_data = self.fetch_protocol_data(protocol_id)
                if protocol_data:
                    # Fetch daily fees and daily revenue data
                    daily_fees_data = self.fetch_protocol_fees(protocol_id, "dailyFees")
                    daily_revenue_data = self.fetch_protocol_fees(protocol_id, "dailyRevenue")
                    
                    # Log the structure of the fetched data
                    logging.info(f"Daily fees data for {protocol_id}: {daily_fees_data}")
                    logging.info(f"Daily revenue data for {protocol_id}: {daily_revenue_data}")
                    
                    # Handle TVL data which might be a dict with chain breakdown
                    tvl_data = protocol_data.get("tvl", 0)
                    if isinstance(tvl_data, dict):
                        tvl_value = sum(tvl_data.values())
                    elif isinstance(tvl_data, list) and tvl_data:
                        tvl_value = tvl_data[-1]  # Take the latest TVL value
                    else:
                        tvl_value = float(tvl_data) if isinstance(tvl_data, (int, float, str)) else 0

                    # Handle fees and revenue data which might be in different formats
                    fees = sum([day[1] for day in daily_fees_data["totalDataChart"]]) if daily_fees_data and "totalDataChart" in daily_fees_data else 0
                    revenue = sum([day[1] for day in daily_revenue_data["totalDataChart"]]) if daily_revenue_data and "totalDataChart" in daily_revenue_data else 0
                    
                    # Convert fees and revenue to float
                    fees = float(fees) if isinstance(fees, (int, float, str)) else 0
                    revenue = float(revenue) if isinstance(revenue, (int, float, str)) else 0

                    # Aggregate monthly revenue
                    monthly_revenue = self.aggregate_monthly_revenue(daily_revenue_data["totalDataChart"]) if daily_revenue_data and "totalDataChart" in daily_revenue_data else {}

                    # Create protocol metrics dictionary
                    protocol_metrics = {
                        "name": protocol_data.get("name", protocol_id),
                        "symbol": protocol_data.get("symbol", ""),
                        "chains": protocol_data.get("chains", []),
                        "tvl": tvl_value,
                        "fees": fees,
                        "revenue": revenue,
                        "mcap": protocol_data.get("mcap", 0)
                    }

                    # Store individual version data
                    all_data["protocols"][protocol_group]["versions"][protocol_id] = protocol_metrics
                    
                    # Update aggregated metrics with numeric values
                    if isinstance(tvl_value, (int, float)):
                        all_data["protocols"][protocol_group]["aggregated"]["tvl"] += tvl_value
                    elif isinstance(tvl_value, dict):
                        all_data["protocols"][protocol_group]["aggregated"]["tvl"] += sum(tvl_value.values())
                    else:
                        logging.warning(f"Unexpected TVL format for {protocol_id}: {tvl_value}")
                    
                    all_data["protocols"][protocol_group]["aggregated"]["fees"] += fees
                    all_data["protocols"][protocol_group]["aggregated"]["revenue"] += revenue

                    # Store monthly revenue data
                    all_data["protocols"][protocol_group]["monthly_revenue"][protocol_id] = monthly_revenue
                
                else:
                    logging.error(f"Failed to fetch data for {protocol_id}")

        for chain in CHAINS:
            logging.info(f"Fetching data for chain {chain}")
            
            # Fetch daily revenue data for the chain
            daily_revenue_data = self.fetch_chain_data(chain, "dailyRevenue")
            
            # Log the structure of the fetched data
            logging.info(f"Daily revenue data for chain {chain}: {daily_revenue_data}")
            
            # Aggregate monthly revenue
            monthly_revenue = self.aggregate_monthly_revenue(daily_revenue_data["totalDataChart"]) if daily_revenue_data and "totalDataChart" in daily_revenue_data else {}

            # Ensure we have at least 12 months of data
            if len(monthly_revenue) < 12:
                last_30_days_revenue = sum(list(monthly_revenue.values())[-1:])
                annualized_revenue = last_30_days_revenue * 12
                monthly_revenue = {f"{datetime.utcnow().year}-{i:02d}": annualized_revenue / 12 for i in range(1, 13)}

            # Store chain data
            all_data["chains"][chain] = {
                "monthly_revenue": monthly_revenue
            }

        return all_data

    def save_data(self, data: Dict):
        """
        Save the collected data to a JSON file.
        
        Args:
            data (Dict): Data to save
        """
        try:
            # Convert tuple keys to strings for JSON serialization
            data_str_keys = json.loads(json.dumps(data, default=str))
            
            filepath = 'data/raw/protocol_data.json'
            with open(filepath, 'w') as f:
                json.dump(data_str_keys, f, indent=2)
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
