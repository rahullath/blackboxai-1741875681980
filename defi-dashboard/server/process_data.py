import os
import json
import logging
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('process_data.log')
    ]
)

class DataProcessor:
    def __init__(self):
        self.raw_data_path = 'data/raw/protocol_data.json'
        self.processed_data_path = 'data/processed/processed_data.json'
        
        # Ensure processed directory exists
        os.makedirs('data/processed', exist_ok=True)

    def load_raw_data(self) -> Dict:
        """
        Load the raw data from JSON file.
        
        Returns:
            Dict: Raw protocol data
        """
        try:
            with open(self.raw_data_path, 'r') as f:
                data = json.load(f)
            logging.info("Raw data loaded successfully")
            return data
            
        except FileNotFoundError:
            logging.error(f"Raw data file not found: {self.raw_data_path}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON data: {str(e)}")
            raise

    def process_protocol_data(self, raw_data: Dict) -> Dict:
        """
        Process raw protocol data into a structured format.
        
        Args:
            raw_data (Dict): Raw protocol data
            
        Returns:
            Dict: Processed protocol data
        """
        processed_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "protocols": []
        }

        for protocol_name, protocol_data in raw_data["protocols"].items():
            # Calculate aggregated metrics
            aggregated = protocol_data["aggregated"]
            
            # Get the main protocol version data (usually the latest version)
            main_version = list(protocol_data["versions"].values())[0]
            
            protocol_info = {
                "name": protocol_name,
                "displayName": main_version["name"],
                "symbol": main_version["symbol"],
                "chains": main_version["chains"],
                "metrics": {
                    "tvl": aggregated["tvl"],
                    "fees": aggregated["fees"],
                    "revenue": aggregated["revenue"],
                    "marketCap": main_version.get("mcap", 0)  # Default to 0 if not available
                }
            }
            
            processed_data["protocols"].append(protocol_info)

        return processed_data

    def calculate_qoq_growth(self, protocols: List[Dict]) -> List[Dict]:
        """
        Calculate quarter-over-quarter revenue growth for each protocol.
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            List[Dict]: Protocol data with QoQ growth metrics added
        """
        for protocol in protocols:
            current_revenue = protocol["metrics"]["revenue"]
            
            # In a real implementation, we would fetch historical data
            # For now, we'll use a placeholder calculation
            protocol["metrics"]["qoq_growth"] = 0.0
            
        return protocols

    def rank_protocols(self, protocols: List[Dict]) -> List[Dict]:
        """
        Rank protocols by market cap and ensure Sonic is included.
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            List[Dict]: Top 5 protocols by market cap (including Sonic)
        """
        # Sort protocols by market cap
        sorted_protocols = sorted(
            protocols,
            key=lambda x: x["metrics"]["marketCap"],
            reverse=True
        )
        
        # Get top 5 protocols
        top_protocols = sorted_protocols[:5]
        
        # Check if Sonic is in top 5, if not add it
        sonic_protocol = next(
            (p for p in protocols if p["name"].lower() == "sonic"),
            None
        )
        
        if sonic_protocol and sonic_protocol not in top_protocols:
            top_protocols.append(sonic_protocol)
            
        return top_protocols

    def process_data(self) -> None:
        """Process the raw data and save the results."""
        try:
            # Load raw data
            raw_data = self.load_raw_data()
            
            # Process protocol data
            processed_data = self.process_protocol_data(raw_data)
            
            # Calculate QoQ growth
            processed_data["protocols"] = self.calculate_qoq_growth(
                processed_data["protocols"]
            )
            
            # Rank protocols and ensure Sonic is included
            processed_data["protocols"] = self.rank_protocols(
                processed_data["protocols"]
            )
            
            # Save processed data
            with open(self.processed_data_path, 'w') as f:
                json.dump(processed_data, f, indent=2)
                
            logging.info(f"Processed data saved to {self.processed_data_path}")
            
        except Exception as e:
            logging.error(f"Error processing data: {str(e)}")
            raise

def main():
    """Main execution function."""
    try:
        processor = DataProcessor()
        processor.process_data()
        logging.info("Data processing completed successfully")
        
    except Exception as e:
        logging.error(f"Unexpected error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
