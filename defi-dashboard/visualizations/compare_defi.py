import os
import json
import logging
import plotly.graph_objects as go
import plotly.subplots as sp
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('visualizations.log')
    ]
)

class DeFiVisualizer:
    def __init__(self):
        self.data_path = 'data/processed/processed_data.json'
        self.output_dir = 'visualizations/output'
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def load_data(self) -> Dict:
        """
        Load the processed data from JSON file.
        
        Returns:
            Dict: Processed protocol data
        """
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            logging.info("Processed data loaded successfully")
            return data
            
        except FileNotFoundError:
            logging.error(f"Processed data file not found: {self.data_path}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON data: {str(e)}")
            raise

    def create_market_cap_chart(self, protocols: List[Dict]) -> go.Figure:
        """
        Create a bar chart comparing market caps.
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            go.Figure: Plotly figure object
        """
        names = [p["displayName"] for p in protocols]
        market_caps = [p["metrics"]["marketCap"] / 1e6 for p in protocols]  # Convert to millions
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=market_caps,
                text=[f"${x:.2f}M" for x in market_caps],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Market Cap Comparison",
            xaxis_title="Protocol",
            yaxis_title="Market Cap (Millions USD)",
            template="plotly_white"
        )
        
        return fig

    def create_revenue_chart(self, protocols: List[Dict]) -> go.Figure:
        """
        Create a bar chart comparing annual revenues.
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            go.Figure: Plotly figure object
        """
        names = [p["displayName"] for p in protocols]
        revenues = [p["metrics"]["revenue"] / 1e6 for p in protocols]  # Convert to millions
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=revenues,
                text=[f"${x:.2f}M" for x in revenues],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Annual Revenue Comparison",
            xaxis_title="Protocol",
            yaxis_title="Annual Revenue (Millions USD)",
            template="plotly_white"
        )
        
        return fig

    def create_qoq_growth_chart(self, protocols: List[Dict]) -> go.Figure:
        """
        Create a bar chart comparing QoQ revenue growth.
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            go.Figure: Plotly figure object
        """
        names = [p["displayName"] for p in protocols]
        growth_rates = [p["metrics"]["qoq_growth"] * 100 for p in protocols]  # Convert to percentage
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=growth_rates,
                text=[f"{x:.1f}%" for x in growth_rates],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Quarter-over-Quarter Revenue Growth",
            xaxis_title="Protocol",
            yaxis_title="QoQ Growth (%)",
            template="plotly_white"
        )
        
        return fig

    def create_dashboard(self) -> None:
        """Create and save the complete dashboard."""
        try:
            # Load data
            data = self.load_data()
            protocols = data["protocols"]
            
            # Create subplot figure
            fig = sp.make_subplots(
                rows=3, cols=1,
                subplot_titles=(
                    "Market Cap Comparison",
                    "Annual Revenue Comparison",
                    "Quarter-over-Quarter Revenue Growth"
                ),
                vertical_spacing=0.2
            )
            
            # Add market cap chart
            market_cap_fig = self.create_market_cap_chart(protocols)
            fig.add_trace(market_cap_fig.data[0], row=1, col=1)
            
            # Add revenue chart
            revenue_fig = self.create_revenue_chart(protocols)
            fig.add_trace(revenue_fig.data[0], row=2, col=1)
            
            # Add QoQ growth chart
            growth_fig = self.create_qoq_growth_chart(protocols)
            fig.add_trace(growth_fig.data[0], row=3, col=1)
            
            # Update layout
            fig.update_layout(
                height=1200,
                width=900,
                showlegend=False,
                title_text="DeFi Protocol Comparison Dashboard",
                template="plotly_white"
            )
            
            # Save dashboard
            output_path = os.path.join(self.output_dir, 'defi_dashboard.html')
            fig.write_html(output_path)
            
            logging.info(f"Dashboard saved to {output_path}")
            
        except Exception as e:
            logging.error(f"Error creating dashboard: {str(e)}")
            raise

def main():
    """Main execution function."""
    try:
        visualizer = DeFiVisualizer()
        visualizer.create_dashboard()
        logging.info("Dashboard creation completed successfully")
        
    except Exception as e:
        logging.error(f"Unexpected error during execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
