# DeFi Dashboard

A dashboard that collects and visualizes key metrics (TVL, fees, revenue, market cap) from major DeFi protocols using the DefiLlama API.

## Supported Protocols

### Ethereum
- AAVE (v1, v2, v3)
- Compound Finance (v1, v2, v3)
- Lido
- MakerDAO

### Solana
- Jupiter (+ Jupiter Aggregator)
- Fluid (+ Fluid Lending)
- Sonic

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the following scripts in order:

1. Fetch raw data from DefiLlama API:
```bash
python server/fetch_data.py
```

2. Process and filter the data:
```bash
python server/process_data.py
```

3. Generate visualizations:
```bash
python visualizations/compare_defi.py
```

## Data Sources

This project uses the DefiLlama API endpoints:

- TVL Data: `/protocols` and `/tvl/{protocol}`
- Fees & Revenue: `/overview/fees` and `/summary/fees/{protocol}`

## Project Structure

```
defi-dashboard/
├── README.md                     - Project documentation
├── requirements.txt              - Python dependencies
├── server/
│   ├── fetch_data.py            - API data collection
│   └── process_data.py          - Data processing and filtering
├── visualizations/
│   └── compare_defi.py          - Generate comparison charts
└── data/
    ├── raw/                     - Raw API response data
    └── processed/               - Filtered and processed data
```

## Generated Visualizations

The dashboard generates three main comparisons:
- Market Cap comparison
- Annual Revenue comparison
- Quarter-over-Quarter Revenue Growth comparison

## Error Handling

The scripts include comprehensive error handling for:
- API request failures
- Missing or malformed data
- File I/O issues
- Data processing errors

All errors are logged with detailed messages for debugging.
