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
        self.raw_data_path = r'C:\Users\rahul\blackboxai-1741875681980\defi-dashboard\data\raw\protocol_data.json'
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
            "protocols": [],
            "chains": {}
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
                    "marketCap": main_version.get("mcap", 0),
                    "qoq_growth": self.calculate_qoq_growth(protocol_data["monthly_revenue"])
                },
                "monthly_revenue": self.aggregate_monthly_revenue(protocol_data["monthly_revenue"])
            }

            processed_data["protocols"].append(protocol_info)

        for chain_name, chain_data in raw_data["chains"].items():
            processed_data["chains"][chain_name] = {
                "monthly_revenue": self.aggregate_chain_revenue(chain_data["monthly_revenue"])
            }

        return processed_data

    def aggregate_monthly_revenue(self, monthly_revenue: Dict) -> Dict:
        """
        Aggregate monthly revenue data from all versions of a protocol or chain.
        
        Args:
            monthly_revenue (Dict): Monthly revenue data for all versions
            
        Returns:
            Dict: Aggregated monthly revenue data
        """
        aggregated_revenue = {}
        if isinstance(monthly_revenue, dict):
            for version_revenue in monthly_revenue.values():
                if isinstance(version_revenue, dict):
                    for month, revenue in version_revenue.items():
                        if month not in aggregated_revenue:
                            aggregated_revenue[month] = 0
                        aggregated_revenue[month] += revenue
                elif isinstance(version_revenue, (int, float)):
                    aggregated_revenue = version_revenue
        return aggregated_revenue

    def aggregate_chain_revenue(self, monthly_revenue: Dict) -> Dict:
        """
        Aggregate chain revenue data considering only data until February 2025.
        If not available, use the last 30 days' data multiplied by 12.
        
        Args:
            monthly_revenue (Dict): Monthly revenue data for the chain
            
        Returns:
            Dict: Aggregated chain revenue data
        """
        relevant_months = [f"{year}-{month:02d}" for year in range(2024, 2026) for month in range(1, 13)]
        relevant_months = relevant_months[1:13]  # Only include months from February 2024 to February 2025
        filtered_revenue = {month: monthly_revenue.get(month, 0) for month in relevant_months}

        # If not enough data, use the last 30 days' data multiplied by 12
        if sum(filtered_revenue.values()) == 0:
            last_30_days_revenue = sum(list(monthly_revenue.values())[-1:])
            annualized_revenue = last_30_days_revenue * 12
            filtered_revenue = {f"{datetime.utcnow().year}-{i:02d}": annualized_revenue / 12 for i in range(1, 13)}

        return filtered_revenue

    def calculate_qoq_growth(self, monthly_revenue: Dict) -> float:
        """
        Calculate the quarter-over-quarter (QoQ) growth rate from monthly revenue data.
        
        Args:
            monthly_revenue (Dict): Monthly revenue data
            
        Returns:
            float: QoQ growth rate
        """
        # Aggregate monthly revenue across all versions
        aggregated_revenue = self.aggregate_monthly_revenue(monthly_revenue)
        
        # Extract the last 12 months of revenue data
        sorted_months = sorted(aggregated_revenue.keys(), reverse=True)
        if len(sorted_months) < 12:
            return 0.0
        
        def get_quarter_revenue(months):
            revenue = sum(aggregated_revenue.get(month, 0) for month in months)
            if revenue == 0:
                # If no data for the quarter, use last 30 days' data multiplied by 4
                last_30_days_revenue = sum(list(aggregated_revenue.values())[-1:])
                revenue = last_30_days_revenue * 4
            return revenue

        last_quarter_months = sorted_months[:3]
        previous_quarter_months = sorted_months[3:6]

        last_quarter = get_quarter_revenue(last_quarter_months)
        previous_quarter = get_quarter_revenue(previous_quarter_months)
        
        if previous_quarter == 0:
            return 0.0
        
        return (last_quarter - previous_quarter) / previous_quarter

    def save_processed_data(self, data: Dict):
        """
        Save the processed data to a JSON file.
        
        Args:
            data (Dict): Data to save
        """
        try:
            with open(self.processed_data_path, 'w') as f:
                json.dump(data, f, indent=2)
            logging.info(f"Processed data successfully saved to {self.processed_data_path}")
            
        except IOError as e:
            logging.error(f"Error saving processed data: {str(e)}")

    def process_data(self):
        """
        Load raw data, process it, and save the processed data.
        """
        raw_data = self.load_raw_data()
        processed_data = self.process_protocol_data(raw_data)
        self.save_processed_data(processed_data)

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
