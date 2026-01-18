# IDR Intelligence Platform

**Advanced Investigative Intelligence & Fraud Detection System**

A comprehensive analytics platform for analyzing CMS Independent Dispute Resolution (IDR) data to identify fraud patterns, investigate suspicious providers, and track exploitation of the No Surprises Act.

![Platform Screenshot](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)

## Features

### 📊 Executive Dashboards
- **Overview**: Quarterly trends, win rates, batch filing statistics
- **Providers**: Identify IDR mills and high-volume filers
- **Specialties**: Analyze exploitation by medical specialty
- **Payers**: Track exposure and loss rates by insurer
- **Geography**: State-level concentration analysis
- **Financial**: QPA offer analysis and IDRE fee tracking

### 🔍 Investigation Tools
- **Provider Deep Dive**: Complete investigation pages with:
  - Risk scoring (0-100)
  - Timeline analysis
  - Geographic footprint
  - Payer targeting patterns
  - Financial behavior analysis
- **Advanced Search**: Find providers by name, NPI, or pattern
- **Comparative Analysis**: Benchmark providers against industry averages

### 🚩 Automated Fraud Detection
- **Pattern Recognition**: Automatically flags:
  - High volume filers (>1,000 disputes)
  - Extreme pricing (>500% of QPA)
  - Batch abuse (>90% batched)
  - Volume spikes (>200% quarterly growth)
  - Geographic expansion
  - Payer targeting
- **Risk Scoring**: Algorithm-based fraud risk assessment
- **Exportable Reports**: Download flagged provider lists

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/YOUR-USERNAME/idr-intelligence-platform.git
cd idr-intelligence-platform
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Add your data**
- Create an `idr_data` folder in the project directory
- Download quarterly IDR files from [CMS](https://www.cms.gov/nosurprises/policies-and-resources/reports)
- Convert to CSV format
- Name files with year and quarter: `idr_2023_q1.csv`, `idr_2023_q2.csv`, etc.
- Place all CSV files in the `idr_data` folder

4. **Run the application**
```bash
streamlit run idr_streamlit_app.py --server.maxUploadSize=1000
```

5. **Load data**
- Open your browser to http://localhost:8501
- Click "Load Data from CSV Files" in the sidebar
- Wait for data to load into the database
- Start investigating!

## Usage

### First-Time Setup
1. Launch the application
2. Click "📥 Load Data from CSV Files" in the sidebar
3. Wait 3-5 minutes for data loading
4. Data persists in `idr_database.db` - you only load once!

### Investigation Workflow
1. **Start with Overview** - Get topline metrics
2. **Check Fraud Alerts** - See automatically flagged providers
3. **Investigate Specific Providers** - Deep dive on suspicious actors
4. **Compare** - Benchmark against peers and industry averages
5. **Export** - Download analysis for reports

### Filtering
Use the sidebar filters to focus your analysis:
- **Quarter**: Filter by time period
- **Specialty**: Focus on specific medical specialties
- **State**: Geographic filtering
- **Payer**: Analyze specific insurers

## Data Sources

This platform analyzes public data from:
- **CMS Federal IDR Process Data** - Quarterly public use files containing dispute-level information
- Available at: https://www.cms.gov/nosurprises/policies-and-resources/reports

## Technical Details

### Architecture
- **Frontend**: Streamlit web framework
- **Data Storage**: SQLite database for persistent storage
- **Analytics**: Pandas, NumPy for data processing
- **Visualization**: Plotly for interactive charts

### Performance
- Handles 2+ million disputes efficiently
- Cached queries for fast filtering
- Automatic data deduplication
- Progress bars for long operations

### Security
- Local deployment by default
- No data transmitted externally
- Database stored locally
- Can be deployed on secure internal networks

## Deployment Options

### Local Development
```bash
streamlit run idr_streamlit_app.py --server.maxUploadSize=1000
```

### Streamlit Cloud (Free)
1. Push code to GitHub
2. Deploy at share.streamlit.io
3. Share URL with team

### Internal Corporate Deployment
- Deploy on internal servers
- Connect to corporate databases
- Integrate with existing auth systems

## Key Insights from 2024 Data

Based on analysis of 2.17 million disputes:
- **Provider Win Rate**: 84% (systematic exploitation)
- **Top 20 Providers**: Account for 31.8% of all disputes
- **Texas Concentration**: 38.1% of national disputes
- **Radiology Dominance**: 26.6% of disputes, 93.1% win rate
- **Batch Filing**: 61.6% filed in batches (industrial scale)

## Use Cases

### For Health Insurers
- Identify providers to prioritize for in-network contracts
- Track IDR exposure by specialty and geography
- Build evidence for regulatory advocacy
- Monitor emerging fraud patterns

### For Policy Researchers
- Analyze No Surprises Act implementation
- Track market behavior changes
- Identify regulatory arbitrage
- Study specialty-specific patterns

### For Legal Teams
- Build investigation dossiers
- Track provider behavior over time
- Export evidence for disputes
- Comparative analysis for cases

## Roadmap

- [ ] Real-time data refresh when CMS publishes new quarters
- [ ] PDF report generation
- [ ] Email alerts for threshold violations
- [ ] Specialty society guidance monitoring
- [ ] Predictive modeling for emerging mills
- [ ] Network analysis for related entities
- [ ] API for integration with other systems

## Contributing

This is currently a private tool. If you're interested in contributing or have access questions, please contact the repository owner.

## License

Proprietary - Internal Use Only

## Support

For questions, issues, or feature requests, please open an issue in the GitHub repository.

## Acknowledgments

Built to combat systematic exploitation of the Independent Dispute Resolution process established under the No Surprises Act. Data sourced from CMS public use files.

---

**Note**: This tool is for analytical and investigative purposes. All data is sourced from publicly available CMS reports.
