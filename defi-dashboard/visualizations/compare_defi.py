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
            template="plotly_dark",
            paper_bgcolor='#0a0b0d',
            plot_bgcolor='#1a1b1e',
            font=dict(
                family="Space Mono, monospace",
                color="#e6e7e8"
            )
        )
        
        # Update bar colors
        fig.update_traces(
            marker_color='rgba(0, 246, 255, 0.7)',
            marker_line_color='rgba(0, 246, 255, 1)',
            marker_line_width=1,
            hovertemplate='%{x}<br>$%{y:.2f}M<extra></extra>'
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
        revenues = [self.calculate_last_12_months_revenue(p["monthly_revenue"]) / 1e6 for p in protocols]  # Aggregate last 12 months and convert to millions
        
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
            template="plotly_dark",
            paper_bgcolor='#0a0b0d',
            plot_bgcolor='#1a1b1e',
            font=dict(
                family="Space Mono, monospace",
                color="#e6e7e8"
            )
        )
        
        # Update bar colors
        fig.update_traces(
            marker_color='rgba(0, 246, 255, 0.7)',
            marker_line_color='rgba(0, 246, 255, 1)',
            marker_line_width=1,
            hovertemplate='%{x}<br>$%{y:.2f}M<extra></extra>'
        )
        
        return fig

    def calculate_last_12_months_revenue(self, monthly_revenue: Dict) -> float:
        """
        Calculate the total revenue for the last 12 months.
        
        Args:
            monthly_revenue (Dict): Monthly revenue data
            
        Returns:
            float: Total revenue for the last 12 months
        """
        sorted_months = sorted(monthly_revenue.keys(), reverse=True)
        last_12_months = sorted_months[:12]
        return sum(monthly_revenue[month] for month in last_12_months)

    def create_qoq_growth_chart(self, protocols: List[Dict]) -> go.Figure:
        """
        Create a bar chart comparing QoQ revenue growth.
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            go.Figure: Plotly figure object
        """
        names = []
        growth_rates = []
        for p in protocols:
            growth_rate = self.calculate_qoq_growth(p["monthly_revenue"]) * 100  # Convert to percentage
            if growth_rate == 0.0:
                # If no QoQ data, use monthly growth and mark with an asterisk
                growth_rate = self.calculate_monthly_growth(p["monthly_revenue"]) * 100
                names.append(f"{p['displayName']}*")
            else:
                names.append(p["displayName"])
            growth_rates.append(growth_rate)
        
        # Create color array based on growth rates
        colors = ['rgba(255, 82, 82, 0.7)' if x < 0 else 'rgba(0, 246, 255, 0.7)' for x in growth_rates]
        line_colors = ['rgba(255, 82, 82, 1)' if x < 0 else 'rgba(0, 246, 255, 1)' for x in growth_rates]
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=growth_rates,
                text=[f"{x:.2f}%" for x in growth_rates],
                textposition='auto',
                marker_color=colors,
                marker_line_color=line_colors,
                marker_line_width=1
            )
        ])
        
        fig.update_layout(
            title="QoQ Revenue Growth Comparison",
            xaxis_title="Protocol",
            yaxis_title="QoQ Revenue Growth (%)",
            template="plotly_dark",
            paper_bgcolor='#0a0b0d',
            plot_bgcolor='#1a1b1e',
            font=dict(
                family="Space Mono, monospace",
                color="#e6e7e8"
            )
        )
        
        # Update hover template
        fig.update_traces(
            hovertemplate='%{x}<br>%{y:.2f}%<extra></extra>'
        )
        
        return fig

    def calculate_qoq_growth(self, monthly_revenue: Dict) -> float:
        """
        Calculate the quarter-over-quarter (QoQ) growth rate from monthly revenue data.
        
        Args:
            monthly_revenue (Dict): Monthly revenue data
            
        Returns:
            float: QoQ growth rate
        """
        # Extract the last 12 months of revenue data
        sorted_months = sorted(monthly_revenue.keys(), reverse=True)
        if len(sorted_months) < 12:
            return 0.0
        
        def get_quarter_revenue(months):
            revenue = sum(monthly_revenue.get(month, 0) for month in months)
            if revenue == 0:
                # If no data for the quarter, use last 30 days' data multiplied by 4
                last_30_days_revenue = sum(list(monthly_revenue.values())[-1:])
                revenue = last_30_days_revenue * 4
            return revenue

        last_quarter_months = sorted_months[:3]
        previous_quarter_months = sorted_months[3:6]

        last_quarter = get_quarter_revenue(last_quarter_months)
        previous_quarter = get_quarter_revenue(previous_quarter_months)
        
        if previous_quarter == 0:
            return 0.0
        
        return (last_quarter - previous_quarter) / previous_quarter

    def calculate_monthly_growth(self, monthly_revenue: Dict) -> float:
        """
        Calculate the month-over-month (MoM) growth rate from monthly revenue data.
        
        Args:
            monthly_revenue (Dict): Monthly revenue data
            
        Returns:
            float: MoM growth rate
        """
        # Extract the last 2 months of revenue data
        sorted_months = sorted(monthly_revenue.keys(), reverse=True)
        if len(sorted_months) < 2:
            return 0.0
        
        last_month = monthly_revenue[sorted_months[0]]
        previous_month = monthly_revenue[sorted_months[1]]
        
        if previous_month == 0:
            return 0.0
        
        return (last_month - previous_month) / previous_month

    def create_chain_comparison_chart(self, chains: Dict) -> go.Figure:
        """
        Create a bar chart comparing chain revenues.
        
        Args:
            chains (Dict): Chain data
            
        Returns:
            go.Figure: Plotly figure object
        """
        chain_names = list(chains.keys())
        revenues = []
        for chain in chain_names:
            monthly_revenue = chains[chain]["monthly_revenue"]
            if isinstance(monthly_revenue, dict):
                total_revenue = sum(monthly_revenue.values())
            elif isinstance(monthly_revenue, (int, float)):
                total_revenue = monthly_revenue
            else:
                total_revenue = 0
            revenues.append(total_revenue / 1e6)  # Convert to millions
        
        fig = go.Figure(data=[
            go.Bar(
                x=chain_names,
                y=revenues,
                text=[f"${x:.2f}M" for x in revenues],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Chain Revenue Comparison",
            xaxis_title="Chain",
            yaxis_title="Revenue (Millions USD)",
            template="plotly_dark",
            paper_bgcolor='#0a0b0d',
            plot_bgcolor='#1a1b1e',
            font=dict(
                family="Space Mono, monospace",
                color="#e6e7e8"
            )
        )
        
        # Update bar colors
        fig.update_traces(
            marker_color='rgba(0, 246, 255, 0.7)',
            marker_line_color='rgba(0, 246, 255, 1)',
            marker_line_width=1,
            hovertemplate='%{x}<br>$%{y:.2f}M<extra></extra>'
        )
        
        return fig

    def create_tvl_chart(self, protocols: List[Dict]) -> go.Figure:
        """
        Create a bar chart comparing total value locked (TVL).
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            go.Figure: Plotly figure object
        """
        names = [p["displayName"] for p in protocols]
        tvls = [p["metrics"]["tvl"] / 1e6 for p in protocols]  # Convert to millions
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=tvls,
                text=[f"${x:.2f}M" for x in tvls],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Total Value Locked (TVL) Comparison",
            xaxis_title="Protocol",
            yaxis_title="TVL (Millions USD)",
            template="plotly_dark",
            paper_bgcolor='#0a0b0d',
            plot_bgcolor='#1a1b1e',
            font=dict(
                family="Space Mono, monospace",
                color="#e6e7e8"
            )
        )
        
        # Update bar colors
        fig.update_traces(
            marker_color='rgba(0, 246, 255, 0.7)',
            marker_line_color='rgba(0, 246, 255, 1)',
            marker_line_width=1,
            hovertemplate='%{x}<br>$%{y:.2f}M<extra></extra>'
        )
        
        return fig

    def create_fees_chart(self, protocols: List[Dict]) -> go.Figure:
        """
        Create a bar chart comparing protocol fees.
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            go.Figure: Plotly figure object
        """
        names = [p["displayName"] for p in protocols]
        fees = [p["metrics"]["fees"] / 1e6 for p in protocols]  # Convert to millions
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=fees,
                text=[f"${x:.2f}M" for x in fees],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="Protocol Fees Comparison",
            xaxis_title="Protocol",
            yaxis_title="Fees (Millions USD)",
            template="plotly_dark",
            paper_bgcolor='#0a0b0d',
            plot_bgcolor='#1a1b1e',
            font=dict(
                family="Space Mono, monospace",
                color="#e6e7e8"
            )
        )
        
        # Update bar colors
        fig.update_traces(
            marker_color='rgba(0, 246, 255, 0.7)',
            marker_line_color='rgba(0, 246, 255, 1)',
            marker_line_width=1,
            hovertemplate='%{x}<br>$%{y:.2f}M<extra></extra>'
        )
        
        return fig

    def calculate_fdv_ratio(self, protocols: List[Dict]) -> List[Dict]:
        """
        Calculate the FDV/Annualized Revenue Ratio for each protocol and rank them.
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            List[Dict]: List of protocols with FDV ratio and rank
        """
        fdv_data = {
            "AAVE": 2.585e9,
            "Compound Finance": 397.89e6,
            "LIDO": 925.67e6,
            "FLUID": 489.55e6,
            "JUPITER": 3.54e9,
            "MAKER": 1.002e9
        }
        
        protocol_ratios = []
        for protocol in protocols:
            name = protocol["displayName"]
            fdv = fdv_data.get(name.upper(), None)
            if fdv:
                annual_revenue = self.calculate_last_12_months_revenue(protocol["monthly_revenue"])
                if annual_revenue == 0:
                    # If no 12 months data, use last 30 days data and annualize it
                    last_30_days_revenue = sum(list(protocol["monthly_revenue"].values())[-1:])
                    annual_revenue = last_30_days_revenue * 12
                ratio = fdv / annual_revenue if annual_revenue > 0 else float('inf')
                protocol_ratios.append({
                    "name": name,
                    "fdv": fdv,
                    "annual_revenue": annual_revenue,
                    "ratio": ratio
                })
        
        # Sort protocols by FDV/Annualized Revenue Ratio
        protocol_ratios.sort(key=lambda x: x["ratio"])
        
        return protocol_ratios

    def create_fdv_ratio_chart(self, protocols: List[Dict]) -> go.Figure:
        """
        Create a bar chart showing FDV/Annualized Revenue Ratio.
        
        Args:
            protocols (List[Dict]): List of protocol data
            
        Returns:
            go.Figure: Plotly figure object
        """
        fdv_ratios = self.calculate_fdv_ratio(protocols)
        names = [p["name"] for p in fdv_ratios]
        ratios = [p["ratio"] for p in fdv_ratios]
        
        fig = go.Figure(data=[
            go.Bar(
                x=names,
                y=ratios,
                text=[f"{x:.2f}" for x in ratios],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="FDV/Annualized Revenue Ratio",
            xaxis_title="Protocol",
            yaxis_title="FDV/Annualized Revenue Ratio",
            template="plotly_dark",
            paper_bgcolor='#0a0b0d',
            plot_bgcolor='#1a1b1e',
            font=dict(
                family="Space Mono, monospace",
                color="#e6e7e8"
            )
        )
        
        # Update bar colors
        fig.update_traces(
            marker_color='rgba(0, 246, 255, 0.7)',
            marker_line_color='rgba(0, 246, 255, 1)',
            marker_line_width=1,
            hovertemplate='%{x}<br>%{y:.2f}<extra></extra>'
        )
        
        return fig

    def create_dashboard(self):
        """
        Create the DeFi dashboard with multiple charts.
        """
        data = self.load_data()
        protocols = data["protocols"]
        chains = data["chains"]
        
        market_cap_chart = self.create_market_cap_chart(protocols)
        revenue_chart = self.create_revenue_chart(protocols)
        qoq_growth_chart = self.create_qoq_growth_chart(protocols)
        chain_comparison_chart = self.create_chain_comparison_chart(chains)
        tvl_chart = self.create_tvl_chart(protocols)
        fees_chart = self.create_fees_chart(protocols)
        fdv_ratio_chart = self.create_fdv_ratio_chart(protocols)
        
        # Create a subplot with 7 rows and 1 column
        fig = sp.make_subplots(
            rows=7, cols=1,
            subplot_titles=(
                "Market Cap Comparison",
                "Annual Revenue Comparison",
                "FDV/Annualized Revenue Ratio",
                "QoQ Revenue Growth Comparison",
                "Chain Revenue Comparison",
                "Total Value Locked (TVL) Comparison",
                "Protocol Fees Comparison"
            ),
            vertical_spacing=0.1
        )
        
        fig.add_trace(market_cap_chart.data[0], row=1, col=1)
        fig.add_trace(revenue_chart.data[0], row=2, col=1)
        fig.add_trace(fdv_ratio_chart.data[0], row=3, col=1)
        fig.add_trace(qoq_growth_chart.data[0], row=4, col=1)
        fig.add_trace(chain_comparison_chart.data[0], row=5, col=1)
        fig.add_trace(tvl_chart.data[0], row=6, col=1)
        fig.add_trace(fees_chart.data[0], row=7, col=1)
        
        # Update the layout with dark theme styling
        fig.update_layout(
            height=2800,
            showlegend=False,
            template="plotly_dark",
            paper_bgcolor='#0a0b0d',
            plot_bgcolor='#1a1b1e',
            font=dict(
                family="Space Mono, monospace",
                color="#e6e7e8"
            ),
            margin=dict(t=30, b=30, l=50, r=50)
        )
        
        # Update all subplot axes for consistent styling
        for i in range(1, 8):
            fig.update_xaxes(
                gridcolor='rgba(255, 255, 255, 0.1)',
                zerolinecolor='rgba(255, 255, 255, 0.2)',
                row=i, col=1
            )
            fig.update_yaxes(
                gridcolor='rgba(255, 255, 255, 0.1)',
                zerolinecolor='rgba(255, 255, 255, 0.2)',
                row=i, col=1
            )
            
        # Update bar colors for all charts
        for trace in fig.data:
            trace.update(
                marker_color='rgba(0, 246, 255, 0.7)',
                marker_line_color='rgba(0, 246, 255, 1)',
                marker_line_width=1,
                hovertemplate='%{x}<br>%{y}<extra></extra>'
            )
        
        output_file = os.path.join(self.output_dir, "defi_dashboard.html")
        fig.write_html(output_file, include_plotlyjs='cdn', full_html=False)

        # Add custom HTML for styling and additional information
        with open(output_file, 'a') as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Crypto Lens - DeFi Analytics Dashboard</title>
                <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
                <style>
                    :root {
                        --primary-color: #00f6ff;
                        --secondary-color: #7000ff;
                        --bg-color: #0a0b0d;
                        --card-bg: #1a1b1e;
                        --text-color: #e6e7e8;
                        --accent-color: #00ffa3;
                    }
                    
                    body {
                        font-family: 'Space Mono', monospace;
                        background-color: var(--bg-color);
                        color: var(--text-color);
                        margin: 0;
                        padding: 0;
                        line-height: 1.6;
                    }
                    
                    .header {
                        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                        padding: 2rem 0;
                        margin-bottom: 2rem;
                        text-align: center;
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                    }
                    
                    .container {
                        width: 90%;
                        max-width: 1400px;
                        margin: auto;
                        padding: 20px;
                    }
                    
                    .dashboard-title {
                        font-size: 3rem;
                        font-weight: 700;
                        margin: 0;
                        text-transform: uppercase;
                    }
                    
                    .subtitle {
                        font-size: 1.2rem;
                        opacity: 0.9;
                        margin-top: 0.5rem;
                        margin-bottom: 0.25rem;
                    }
                    
                    .author {
                        font-size: 1rem;
                        opacity: 0.8;
                        margin-top: 0;
                        color: var(--accent-color);
                    }
                    
                    .info-card {
                        background-color: var(--card-bg);
                        border-radius: 12px;
                        padding: 2rem;
                        margin: 2rem 0;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    }
                    
                    .info-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 1.5rem;
                        margin-bottom: 2rem;
                    }
                    
                    .info-item {
                        background: rgba(255, 255, 255, 0.05);
                        padding: 1rem;
                        border-radius: 8px;
                    }
                    
                    .info-item strong {
                        color: var(--accent-color);
                    }
                    
                    .chart-container {
                        background-color: var(--card-bg);
                        border-radius: 12px;
                        padding: 1.5rem;
                        margin: 1.5rem 0;
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    }
                    
                    .chart-title {
                        color: var(--primary-color);
                        font-size: 1.5rem;
                        margin-bottom: 1rem;
                        padding-bottom: 0.5rem;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                    }
                    
                    a {
                        color: var(--accent-color);
                        text-decoration: none;
                        transition: all 0.3s ease;
                    }
                    
                    a:hover {
                        color: var(--primary-color);
                        text-decoration: none;
                    }
                    
                    .github-link {
                        display: inline-flex;
                        align-items: center;
                        gap: 0.5rem;
                        padding: 0.5rem 1rem;
                        background: rgba(255, 255, 255, 0.05);
                        border-radius: 8px;
                        margin-top: 1rem;
                    }
                    
                    .github-link:hover {
                        background: rgba(255, 255, 255, 0.1);
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="container">
                        <h1 class="dashboard-title">Crypto Lens</h1>
                        <p class="subtitle">Advanced DeFi Analytics Dashboard</p>
                        <p class="author">by Rahul Lath</p>
                    </div>
                </div>
                
                <div class="container">
                    <div class="info-card">
                        <p>
                            Crypto Lens is a sophisticated DeFi analytics platform that provides real-time insights into key metrics 
                            across major protocols. Our dashboard leverages advanced data analysis to deliver comprehensive views of 
                            market performance, revenue streams, and protocol health indicators.
                        </p>
                        
                        <div class="info-grid">
                            <div class="info-item">
                                <strong>Protocols Analyzed:</strong>
                                <p>AAVE, Compound Finance, LIDO, FLUID, JUPITER, MAKER</p>
                            </div>
                            <div class="info-item">
                                <strong>Data Coverage:</strong>
                                <p>Rolling 12-month analysis with daily updates</p>
                            </div>
                            <div class="info-item">
                                <strong>Metrics Tracked:</strong>
                                <p>Market Cap, Revenue, TVL, Protocol Fees, Growth Rates</p>
                            </div>
                        </div>
                        
                        <a href="https://github.com/rahullath/cryptolens" target="_blank" class="github-link">
                            View on GitHub
                        </a>
                    </div>
                    
                    <div class="charts-section">
                        <div class="chart-container">
                            <h2 class="chart-title">Market Cap Comparison</h2>
                            <div id="chart1"></div>
                        </div>
                        
                        <div class="chart-container">
                            <h2 class="chart-title">Annual Revenue Comparison</h2>
                            <div id="chart2"></div>
                        </div>
                        
                        <div class="chart-container">
                            <h2 class="chart-title">FDV/Annualized Revenue Ratio</h2>
                            <div id="chart3"></div>
                        </div>
                        
                        <div class="chart-container">
                            <h2 class="chart-title">QoQ Revenue Growth Comparison</h2>
                            <div id="chart4"></div>
                        </div>
                        
                        <div class="chart-container">
                            <h2 class="chart-title">Chain Revenue Comparison</h2>
                            <div id="chart5"></div>
                        </div>
                        
                        <div class="chart-container">
                            <h2 class="chart-title">Total Value Locked (TVL) Comparison</h2>
                            <div id="chart6"></div>
                        </div>
                        
                        <div class="chart-container">
                            <h2 class="chart-title">Protocol Fees Comparison</h2>
                            <div id="chart7"></div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """)

        logging.info(f"Dashboard successfully created at {output_file}")

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
