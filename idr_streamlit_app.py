import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sqlite3
import io
from datetime import datetime
import numpy as np

# Page config
st.set_page_config(
    page_title="IDR Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a5490;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4a5568;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f7fafc;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #1a5490;
    }
    .alert-box {
        background-color: #fff5f5;
        border-left: 4px solid #fc8181;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .success-box {
        background-color: #f0fff4;
        border-left: 4px solid #48bb78;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .warning-box {
        background-color: #fffaf0;
        border-left: 4px solid #ed8936;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    .fraud-flag {
        background-color: #fff5f5;
        border: 2px solid #fc8181;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        display: inline-block;
        margin: 0.25rem;
        font-weight: 600;
        color: #c53030;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
DB_PATH = Path("idr_database.db")
DATA_FOLDER = Path("idr_data")

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS idr_disputes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quarter TEXT,
            data_loaded_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_database_info():
    """Get database status"""
    if not DB_PATH.exists():
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM idr_disputes")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT DISTINCT quarter FROM idr_disputes ORDER BY quarter")
        quarters = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT MAX(data_loaded_at) FROM idr_disputes")
        last_loaded = cursor.fetchone()[0]
        
        conn.close()
        return {
            'count': count,
            'quarters': quarters,
            'last_loaded': last_loaded
        }
    except:
        conn.close()
        return None

def load_csv_to_database():
    """Load CSV files to database"""
    
    if not DATA_FOLDER.exists():
        st.error(f"❌ Data folder not found: {DATA_FOLDER}")
        return False
    
    csv_files = list(DATA_FOLDER.glob('*.csv'))
    
    if not csv_files:
        st.error(f"❌ No CSV files found in {DATA_FOLDER}")
        return False
    
    st.info(f"📂 Found {len(csv_files)} CSV files. Loading...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_dfs = []
    
    for idx, csv_file in enumerate(csv_files):
        status_text.text(f"Loading {csv_file.name}...")
        
        try:
            df = pd.read_csv(csv_file)
            
            # Determine quarter from filename
            filename_lower = csv_file.name.lower()
            if '2022' in filename_lower:
                year = '2022'
            elif '2023' in filename_lower:
                year = '2023'
            elif '2024' in filename_lower:
                year = '2024'
            elif '2025' in filename_lower:
                year = '2025'
            else:
                year = 'Unknown'
            
            if 'q1' in filename_lower:
                quarter = f'Q1 {year}'
            elif 'q2' in filename_lower:
                quarter = f'Q2 {year}'
            elif 'q3' in filename_lower:
                quarter = f'Q3 {year}'
            elif 'q4' in filename_lower:
                quarter = f'Q4 {year}'
            else:
                quarter = f'Unknown {year}'
            
            df['quarter'] = quarter
            df['data_loaded_at'] = datetime.now().isoformat()
            
            all_dfs.append(df)
            
        except Exception as e:
            st.warning(f"⚠️ Error loading {csv_file.name}: {e}")
        
        progress_bar.progress((idx + 1) / len(csv_files))
    
    if not all_dfs:
        st.error("❌ Failed to load any CSV files")
        return False
    
    status_text.text("Combining data...")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    status_text.text("Saving to database...")
    conn = sqlite3.connect(DB_PATH)
    combined_df.to_sql('idr_disputes', conn, if_exists='replace', index=False)
    conn.close()
    
    progress_bar.progress(1.0)
    status_text.text("✅ Data loaded successfully!")
    
    return True

@st.cache_data(ttl=3600)
def load_data_from_db():
    """Load data from database with caching"""
    if not DB_PATH.exists():
        return None
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        df = pd.read_sql_query("SELECT * FROM idr_disputes", conn)
        
        # Clean percentage columns
        pct_columns = [col for col in df.columns if 'Percent' in col or '% of QPA' in col]
        for col in pct_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace('%', '').str.replace('N/A', ''), 
                    errors='coerce'
                )
        
        # Clean currency columns
        if 'IDRE Compensation' in df.columns:
            df['IDRE Compensation'] = pd.to_numeric(
                df['IDRE Compensation'].astype(str).str.replace('$', '').str.replace(',', ''), 
                errors='coerce'
            )
        
        conn.close()
        return df
        
    except Exception as e:
        conn.close()
        st.error(f"Error loading data: {e}")
        return None

def calculate_fraud_flags(provider_df, full_df):
    """Calculate fraud risk flags for a provider"""
    flags = []
    
    provider_name = provider_df['Provider/Facility Name'].iloc[0] if 'Provider/Facility Name' in provider_df.columns else "Unknown"
    
    # Flag 1: High volume
    total_disputes = len(provider_df)
    if total_disputes > 1000:
        flags.append(("🚩 HIGH VOLUME", f"{total_disputes:,} disputes - Industrial scale filing"))
    
    # Flag 2: Extreme pricing
    if 'Provider/Facility Offer as % of QPA' in provider_df.columns:
        avg_offer = provider_df['Provider/Facility Offer as % of QPA'].mean()
        if avg_offer > 500:
            flags.append(("🚩 EXTREME PRICING", f"Average offer {avg_offer:.0f}% of QPA"))
    
    # Flag 3: High batch rate
    if 'Type of Dispute' in provider_df.columns:
        batch_rate = (provider_df['Type of Dispute'] == 'Batched').sum() / len(provider_df) * 100
        if batch_rate > 90:
            flags.append(("🚩 BATCH ABUSER", f"{batch_rate:.1f}% of disputes are batched"))
    
    # Flag 4: Rapid growth (if multiple quarters available)
    if 'quarter' in provider_df.columns:
        quarterly_counts = provider_df['quarter'].value_counts().sort_index()
        if len(quarterly_counts) >= 2:
            growth_rates = []
            sorted_quarters = sorted(quarterly_counts.index)
            for i in range(1, len(sorted_quarters)):
                prev_count = quarterly_counts[sorted_quarters[i-1]]
                curr_count = quarterly_counts[sorted_quarters[i]]
                if prev_count > 0:
                    growth = ((curr_count - prev_count) / prev_count) * 100
                    growth_rates.append(growth)
            
            if growth_rates and max(growth_rates) > 200:
                flags.append(("🚩 VOLUME SPIKE", f"Disputes increased {max(growth_rates):.0f}% in one quarter"))
    
    # Flag 5: Geographic spread
    if 'Location of Service' in provider_df.columns:
        states = provider_df['Location of Service'].nunique()
        if states > 10:
            flags.append(("🚩 MULTI-STATE OPERATION", f"Filing in {states} different states"))
    
    # Flag 6: Payer concentration
    if 'Health Plan/Issuer Name' in provider_df.columns:
        payer_counts = provider_df['Health Plan/Issuer Name'].value_counts()
        if len(payer_counts) > 0:
            top_payer_pct = (payer_counts.iloc[0] / len(provider_df)) * 100
            if top_payer_pct > 80:
                flags.append(("🚩 PAYER TARGETING", f"{top_payer_pct:.0f}% of disputes against {payer_counts.index[0]}"))
    
    # Calculate overall risk score (0-100)
    risk_score = min(100, len(flags) * 15)
    
    return flags, risk_score

def render_provider_deep_dive(provider_name, df):
    """Render detailed provider investigation page"""
    provider_df = df[df['Provider/Facility Name'] == provider_name]
    
    if len(provider_df) == 0:
        st.warning("No data found for this provider")
        return
    
    st.markdown(f"## 🔍 Investigation: {provider_name}")
    
    # Calculate fraud flags
    flags, risk_score = calculate_fraud_flags(provider_df, df)
    
    # Risk score
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        if risk_score >= 60:
            st.metric("🚨 Risk Score", f"{risk_score}/100", delta="HIGH RISK", delta_color="inverse")
        elif risk_score >= 30:
            st.metric("⚠️ Risk Score", f"{risk_score}/100", delta="MEDIUM", delta_color="off")
        else:
            st.metric("✓ Risk Score", f"{risk_score}/100", delta="LOW", delta_color="normal")
    
    with col2:
        st.metric("Total Disputes", f"{len(provider_df):,}")
    
    with col3:
        if 'Payment Determination Outcome' in provider_df.columns:
            wins = (provider_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
            win_rate = (wins / len(provider_df)) * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
    
    with col4:
        if 'quarter' in provider_df.columns:
            quarters = provider_df['quarter'].nunique()
            date_range = f"{provider_df['quarter'].min()} - {provider_df['quarter'].max()}"
            st.metric("Active Period", f"{quarters} quarters", delta=date_range)
    
    # Fraud flags
    if flags:
        st.markdown("### 🚩 Fraud Risk Indicators")
        for flag_type, description in flags:
            st.markdown(f'<div class="fraud-flag">{flag_type}: {description}</div>', unsafe_allow_html=True)
        st.markdown("")  # spacing
    
    st.markdown("---")
    
    # Tabs for detailed analysis
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Timeline", "💰 Financial", "🗺️ Geography", "📊 Patterns"])
    
    with tab1:
        st.subheader("Dispute Volume Over Time")
        if 'quarter' in provider_df.columns:
            quarterly = provider_df['quarter'].value_counts().sort_index()
            fig = px.line(
                x=quarterly.index,
                y=quarterly.values,
                markers=True,
                labels={'x': 'Quarter', 'y': 'Number of Disputes'},
                title="Quarterly Dispute Filings"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show percentage change
            st.subheader("Quarter-over-Quarter Growth")
            growth_data = []
            sorted_quarters = sorted(quarterly.index)
            for i in range(1, len(sorted_quarters)):
                prev = quarterly[sorted_quarters[i-1]]
                curr = quarterly[sorted_quarters[i]]
                growth = ((curr - prev) / prev) * 100 if prev > 0 else 0
                growth_data.append({
                    'Quarter': sorted_quarters[i],
                    'Previous': prev,
                    'Current': curr,
                    'Growth %': f"{growth:+.1f}%"
                })
            
            if growth_data:
                st.dataframe(pd.DataFrame(growth_data), use_container_width=True)
    
    with tab2:
        st.subheader("Financial Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Provider/Facility Offer as % of QPA' in provider_df.columns:
                offers = provider_df['Provider/Facility Offer as % of QPA'].dropna()
                
                # Compare to industry average
                industry_avg = df['Provider/Facility Offer as % of QPA'].dropna().median()
                provider_avg = offers.median()
                
                st.metric(
                    "Median Offer (% of QPA)", 
                    f"{provider_avg:.0f}%",
                    delta=f"{provider_avg - industry_avg:+.0f}% vs industry",
                    delta_color="inverse" if provider_avg > industry_avg * 1.5 else "normal"
                )
                
                st.write("**Offer Distribution:**")
                st.write(f"- Mean: {offers.mean():.0f}%")
                st.write(f"- Median: {offers.median():.0f}%")
                st.write(f"- 75th percentile: {offers.quantile(0.75):.0f}%")
                st.write(f"- 90th percentile: {offers.quantile(0.90):.0f}%")
        
        with col2:
            if 'IDRE Compensation' in provider_df.columns:
                fees = provider_df['IDRE Compensation'].dropna()
                st.metric("Total IDRE Fees Paid", f"${fees.sum():,.0f}")
                st.write(f"**Average per dispute:** ${fees.mean():.2f}")
    
    with tab3:
        st.subheader("Geographic Footprint")
        
        if 'Location of Service' in provider_df.columns:
            state_counts = provider_df['Location of Service'].value_counts().head(15)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = px.bar(
                    x=state_counts.values,
                    y=state_counts.index,
                    orientation='h',
                    labels={'x': 'Number of Disputes', 'y': 'State'},
                    title="Disputes by State"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("**State Summary:**")
                for state, count in state_counts.head(10).items():
                    pct = (count / len(provider_df)) * 100
                    st.write(f"- {state}: {count:,} ({pct:.1f}%)")
    
    with tab4:
        st.subheader("Filing Patterns")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Type of Dispute' in provider_df.columns:
                dispute_types = provider_df['Type of Dispute'].value_counts()
                fig = px.pie(
                    values=dispute_types.values,
                    names=dispute_types.index,
                    title="Batch vs Single Filing"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'Health Plan/Issuer Name' in provider_df.columns:
                st.write("**Top 10 Targeted Payers:**")
                payer_counts = provider_df['Health Plan/Issuer Name'].value_counts().head(10)
                for payer, count in payer_counts.items():
                    pct = (count / len(provider_df)) * 100
                    st.write(f"- {payer}: {count:,} ({pct:.1f}%)")

def main():
    # Header
    st.markdown('<p class="main-header">🔍 IDR Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Investigative Intelligence & Fraud Detection System</p>', unsafe_allow_html=True)
    
    # Check database
    db_info = get_database_info()
    
    # Sidebar
    with st.sidebar:
        st.header("💾 Database Status")
        
        if db_info:
            st.markdown(f"""
            <div class="success-box">
            <b>✅ Database Active</b><br/>
            Records: {db_info['count']:,}<br/>
            Quarters: {len(db_info['quarters'])}<br/>
            Last Updated: {db_info['last_loaded'][:10] if db_info['last_loaded'] else 'Unknown'}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Refresh Data from CSV Files"):
                with st.spinner("Refreshing data..."):
                    if load_csv_to_database():
                        st.success("✅ Data refreshed!")
                        st.cache_data.clear()
                        st.rerun()
        else:
            st.warning("⚠️ No database found")
            if st.button("📥 Load Data from CSV Files", type="primary"):
                init_database()
                with st.spinner("Loading data..."):
                    if load_csv_to_database():
                        st.success("✅ Data loaded!")
                        st.cache_data.clear()
                        st.rerun()
        
        # Load data
        if db_info:
            df = load_data_from_db()
            
            if df is not None:
                st.markdown("---")
                st.header("🎛️ Filters")
                
                # Quarter filter
                quarters = ['All'] + sorted(df['quarter'].unique().tolist())
                selected_quarter = st.multiselect(
                    "Quarter",
                    quarters,
                    default=['All']
                )
                
                # Specialty filter
                if 'Practice/Facility Specialty or Type' in df.columns:
                    specialties = ['All'] + sorted(df['Practice/Facility Specialty or Type'].dropna().unique().tolist()[:50])
                    selected_specialties = st.multiselect(
                        "Specialty (Top 50)",
                        specialties,
                        default=['All']
                    )
                
                # State filter
                if 'Location of Service' in df.columns:
                    states = ['All'] + sorted(df['Location of Service'].dropna().unique().tolist())
                    selected_states = st.multiselect(
                        "State",
                        states,
                        default=['All']
                    )
                
                # Payer filter
                if 'Health Plan/Issuer Name' in df.columns:
                    payers = ['All'] + sorted(df['Health Plan/Issuer Name'].dropna().unique().tolist()[:30])
                    selected_payers = st.multiselect(
                        "Payer (Top 30)",
                        payers,
                        default=['All']
                    )
                
                # Apply filters
                filtered_df = df.copy()
                
                if 'All' not in selected_quarter:
                    filtered_df = filtered_df[filtered_df['quarter'].isin(selected_quarter)]
                
                if 'Practice/Facility Specialty or Type' in df.columns and 'All' not in selected_specialties:
                    filtered_df = filtered_df[filtered_df['Practice/Facility Specialty or Type'].isin(selected_specialties)]
                
                if 'Location of Service' in df.columns and 'All' not in selected_states:
                    filtered_df = filtered_df[filtered_df['Location of Service'].isin(selected_states)]
                
                if 'Health Plan/Issuer Name' in df.columns and 'All' not in selected_payers:
                    filtered_df = filtered_df[filtered_df['Health Plan/Issuer Name'].isin(selected_payers)]
                
                st.markdown("---")
                st.info(f"📊 Showing {len(filtered_df):,} of {len(df):,} disputes")
            else:
                filtered_df = None
        else:
            filtered_df = None
            df = None
    
    # Main content
    if filtered_df is not None and len(filtered_df) > 0:
        
        # Tabs - Original 6 + New 3
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
            "📊 Overview", 
            "🏥 Providers", 
            "🩺 Specialties", 
            "🏢 Payers", 
            "📍 Geography",
            "💰 Financial",
            "🔍 Investigate",
            "🚩 Fraud Alerts",
            "📊 Compare"
        ])
        
        # TAB 1: OVERVIEW (unchanged)
        with tab1:
            st.header("Executive Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_disputes = len(filtered_df)
                st.metric("Total Disputes", f"{total_disputes:,}")
            
            with col2:
                if 'Payment Determination Outcome' in filtered_df.columns:
                    provider_wins = (filtered_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                    win_rate = provider_wins / len(filtered_df) * 100
                    st.metric("Provider Win Rate", f"{win_rate:.1f}%")
            
            with col3:
                if 'Type of Dispute' in filtered_df.columns:
                    batch_rate = (filtered_df['Type of Dispute'] == 'Batched').sum() / len(filtered_df) * 100
                    st.metric("Batch Filing Rate", f"{batch_rate:.1f}%")
            
            with col4:
                if 'IDRE Compensation' in filtered_df.columns:
                    total_fees = filtered_df['IDRE Compensation'].sum()
                    st.metric("Total IDRE Fees", f"${total_fees:,.0f}")
            
            st.markdown("---")
            
            if 'quarter' in filtered_df.columns:
                st.subheader("Dispute Volume by Quarter")
                quarterly_counts = filtered_df['quarter'].value_counts().sort_index()
                fig = px.bar(
                    x=quarterly_counts.index,
                    y=quarterly_counts.values,
                    labels={'x': 'Quarter', 'y': 'Number of Disputes'},
                    title="Quarterly Dispute Volume"
                )
                fig.update_traces(marker_color='#1a5490')
                st.plotly_chart(fig, use_container_width=True)
            
            if 'Payment Determination Outcome' in filtered_df.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Payment Outcomes")
                    outcome_counts = filtered_df['Payment Determination Outcome'].value_counts()
                    fig = px.pie(
                        values=outcome_counts.values,
                        names=outcome_counts.index,
                        title="Determination Outcomes"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Batch vs Single Disputes")
                    if 'Type of Dispute' in filtered_df.columns:
                        type_counts = filtered_df['Type of Dispute'].value_counts()
                        fig = px.pie(
                            values=type_counts.values,
                            names=type_counts.index,
                            title="Dispute Type Distribution"
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        # TAB 2: PROVIDERS (unchanged)
        with tab2:
            st.header("Provider Analysis - IDR Mills")
            
            if 'Provider/Facility Name' in filtered_df.columns:
                st.markdown("""
                <div class="alert-box">
                <b>⚠️ IDR Mills Identified:</b> Providers filing disputes at industrial scale with high win rates.
                </div>
                """, unsafe_allow_html=True)
                
                provider_counts = filtered_df['Provider/Facility Name'].value_counts().head(20)
                
                provider_data = []
                for provider in provider_counts.index:
                    provider_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                    total = len(provider_df)
                    if 'Payment Determination Outcome' in filtered_df.columns:
                        wins = (provider_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                        win_rate = wins / total * 100 if total > 0 else 0
                    else:
                        win_rate = None
                    
                    provider_data.append({
                        'Provider': provider,
                        'Disputes': total,
                        'Win Rate': f"{win_rate:.1f}%" if win_rate else "N/A",
                        '% of Total': f"{total/len(filtered_df)*100:.2f}%"
                    })
                
                provider_summary = pd.DataFrame(provider_data)
                
                st.subheader("Top 20 Highest-Volume Providers")
                st.dataframe(provider_summary, use_container_width=True, height=600)
                
                fig = px.bar(
                    provider_summary.head(10),
                    x='Disputes',
                    y='Provider',
                    orientation='h',
                    title="Top 10 Providers by Dispute Volume"
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                csv = provider_summary.to_csv(index=False)
                st.download_button(
                    label="📥 Download Provider Analysis (CSV)",
                    data=csv,
                    file_name="idr_provider_analysis.csv",
                    mime="text/csv"
                )
        
        # TAB 3: SPECIALTIES (unchanged)
        with tab3:
            st.header("Specialty Analysis")
            
            if 'Practice/Facility Specialty or Type' in filtered_df.columns:
                specialty_counts = filtered_df['Practice/Facility Specialty or Type'].value_counts().head(20)
                
                specialty_data = []
                for specialty in specialty_counts.index:
                    specialty_df = filtered_df[filtered_df['Practice/Facility Specialty or Type'] == specialty]
                    total = len(specialty_df)
                    if 'Payment Determination Outcome' in filtered_df.columns:
                        wins = (specialty_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                        win_rate = wins / total * 100 if total > 0 else 0
                    else:
                        win_rate = None
                    
                    specialty_data.append({
                        'Specialty': specialty,
                        'Disputes': total,
                        'Win Rate': f"{win_rate:.1f}%" if win_rate else "N/A",
                        '% of Total': f"{total/len(filtered_df)*100:.1f}%"
                    })
                
                specialty_summary = pd.DataFrame(specialty_data)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("Top 20 Specialties by Volume")
                    fig = px.bar(
                        specialty_summary.head(15),
                        y='Specialty',
                        x='Disputes',
                        orientation='h',
                        title="Dispute Volume by Specialty",
                        color='Disputes',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(height=600)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Summary Table")
                    st.dataframe(specialty_summary, height=600)
                
                if 'quarter' in filtered_df.columns:
                    st.subheader("Quarterly Trends - Top 5 Specialties")
                    top_5_specialties = specialty_counts.head(5).index
                    
                    trend_data = []
                    for specialty in top_5_specialties:
                        for quarter in filtered_df['quarter'].unique():
                            count = len(filtered_df[
                                (filtered_df['Practice/Facility Specialty or Type'] == specialty) &
                                (filtered_df['quarter'] == quarter)
                            ])
                            trend_data.append({
                                'Specialty': specialty,
                                'Quarter': quarter,
                                'Disputes': count
                            })
                    
                    trend_df = pd.DataFrame(trend_data)
                    fig = px.line(
                        trend_df,
                        x='Quarter',
                        y='Disputes',
                        color='Specialty',
                        title="Quarterly Dispute Trends by Specialty",
                        markers=True
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # TAB 4: PAYERS (unchanged)
        with tab4:
            st.header("Payer Exposure Analysis")
            
            if 'Health Plan/Issuer Name' in filtered_df.columns:
                payer_counts = filtered_df['Health Plan/Issuer Name'].value_counts().head(20)
                
                payer_data = []
                for payer in payer_counts.index:
                    payer_df = filtered_df[filtered_df['Health Plan/Issuer Name'] == payer]
                    total = len(payer_df)
                    if 'Payment Determination Outcome' in filtered_df.columns:
                        losses = (payer_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                        loss_rate = losses / total * 100 if total > 0 else 0
                    else:
                        loss_rate = None
                    
                    payer_data.append({
                        'Payer': payer,
                        'Disputes': total,
                        'Loss Rate': f"{loss_rate:.1f}%" if loss_rate else "N/A",
                        '% of Total': f"{total/len(filtered_df)*100:.1f}%"
                    })
                
                payer_summary = pd.DataFrame(payer_data)
                
                st.subheader("Top 20 Payers by Dispute Volume")
                st.dataframe(payer_summary, use_container_width=True, height=500)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(
                        payer_summary.head(10),
                        x='Disputes',
                        y='Payer',
                        orientation='h',
                        title="Top 10 Payers by Volume"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    payer_summary['Loss Rate Numeric'] = payer_summary['Loss Rate'].str.replace('%', '').str.replace('N/A', '0').astype(float)
                    fig = px.bar(
                        payer_summary.head(10),
                        x='Loss Rate Numeric',
                        y='Payer',
                        orientation='h',
                        title="Loss Rates by Payer",
                        labels={'Loss Rate Numeric': 'Loss Rate (%)'}
                    )
                    fig.update_traces(marker_color='#fc8181')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
        
        # TAB 5: GEOGRAPHY (unchanged)
        with tab5:
            st.header("Geographic Distribution")
            
            if 'Location of Service' in filtered_df.columns:
                state_counts = filtered_df['Location of Service'].value_counts().head(20)
                
                state_data = []
                for state in state_counts.index:
                    count = state_counts[state]
                    state_data.append({
                        'State': state,
                        'Disputes': count,
                        '% of Total': f"{count/len(filtered_df)*100:.1f}%"
                    })
                
                state_summary = pd.DataFrame(state_data)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("Top 20 States by Dispute Volume")
                    fig = px.bar(
                        state_summary.head(15),
                        x='State',
                        y='Disputes',
                        title="Geographic Concentration of Disputes",
                        color='Disputes',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("State Rankings")
                    st.dataframe(state_summary, height=500)
                
                if 'TX' in state_summary['State'].values:
                    tx_pct = state_summary[state_summary['State'] == 'TX']['% of Total'].values[0]
                    st.markdown(f"""
                    <div class="alert-box">
                    <b>🎯 Texas Concentration:</b> Texas accounts for {tx_pct} of all disputes in this dataset.
                    </div>
                    """, unsafe_allow_html=True)
        
        # TAB 6: FINANCIAL (unchanged)
        with tab6:
            st.header("Financial Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'Provider/Facility Offer as % of QPA' in filtered_df.columns:
                    st.subheader("Provider Offer Distribution")
                    provider_offers = filtered_df['Provider/Facility Offer as % of QPA'].dropna()
                    
                    stats_data = {
                        'Statistic': ['Mean', 'Median', '75th Percentile', '90th Percentile'],
                        'Value': [
                            f"{provider_offers.mean():.1f}%",
                            f"{provider_offers.median():.1f}%",
                            f"{provider_offers.quantile(0.75):.1f}%",
                            f"{provider_offers.quantile(0.90):.1f}%"
                        ]
                    }
                    st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
            
            with col2:
                if 'Health Plan/Issuer Offer as % of QPA' in filtered_df.columns:
                    st.subheader("Payer Offer Distribution")
                    payer_offers = filtered_df['Health Plan/Issuer Offer as % of QPA'].dropna()
                    
                    stats_data = {
                        'Statistic': ['Mean', 'Median', '25th Percentile', '10th Percentile'],
                        'Value': [
                            f"{payer_offers.mean():.1f}%",
                            f"{payer_offers.median():.1f}%",
                            f"{payer_offers.quantile(0.25):.1f}%",
                            f"{payer_offers.quantile(0.10):.1f}%"
                        ]
                    }
                    st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
            
            if 'Provider/Facility Offer as % of QPA' in filtered_df.columns:
                st.subheader("Provider Offer Distribution (Histogram)")
                offers_clean = provider_offers[provider_offers < 1000]
                fig = px.histogram(
                    offers_clean,
                    nbins=50,
                    title="Distribution of Provider Offers (as % of QPA, capped at 1000%)",
                    labels={'value': 'Offer as % of QPA', 'count': 'Number of Disputes'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            if 'IDRE Compensation' in filtered_df.columns:
                st.subheader("IDRE Compensation Analysis")
                idre_fees = filtered_df['IDRE Compensation'].dropna()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Fees", f"${idre_fees.sum():,.0f}")
                with col2:
                    st.metric("Average Fee", f"${idre_fees.mean():.2f}")
                with col3:
                    st.metric("Median Fee", f"${idre_fees.median():.2f}")
        
        # TAB 7: INVESTIGATE (NEW)
        with tab7:
            st.header("🔍 Advanced Investigation Tools")
            
            st.markdown("""
            <div class="warning-box">
            <b>Investigation Mode:</b> Search for specific providers, analyze patterns, and generate investigation reports.
            </div>
            """, unsafe_allow_html=True)
            
            # Search functionality
            if 'Provider/Facility Name' in filtered_df.columns:
                st.subheader("Provider Search")
                
                search_query = st.text_input(
                    "Search for a provider by name:",
                    placeholder="Enter provider name..."
                )
                
                if search_query:
                    # Search providers
                    matching_providers = filtered_df[
                        filtered_df['Provider/Facility Name'].str.contains(search_query, case=False, na=False)
                    ]['Provider/Facility Name'].value_counts()
                    
                    if len(matching_providers) > 0:
                        st.write(f"Found {len(matching_providers)} matching providers:")
                        
                        selected_provider = st.selectbox(
                            "Select a provider to investigate:",
                            matching_providers.index.tolist()
                        )
                        
                        if st.button("🔍 Launch Investigation", type="primary"):
                            st.markdown("---")
                            render_provider_deep_dive(selected_provider, filtered_df)
                    else:
                        st.warning("No providers found matching your search")
                
                else:
                    # Show top providers to investigate
                    st.subheader("High-Risk Providers (Quick Select)")
                    
                    top_providers = filtered_df['Provider/Facility Name'].value_counts().head(20)
                    
                    # Calculate risk scores for quick view
                    provider_risk_data = []
                    for provider in top_providers.index[:10]:
                        provider_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                        flags, risk_score = calculate_fraud_flags(provider_df, filtered_df)
                        
                        provider_risk_data.append({
                            'Provider': provider,
                            'Disputes': len(provider_df),
                            'Risk Score': risk_score,
                            'Flags': len(flags)
                        })
                    
                    risk_df = pd.DataFrame(provider_risk_data).sort_values('Risk Score', ascending=False)
                    
                    st.dataframe(risk_df, use_container_width=True)
                    
                    st.write("Click on a provider name above, then use the search box to investigate.")
        
        # TAB 8: FRAUD ALERTS (NEW)
        with tab8:
            st.header("🚩 Automated Fraud Detection")
            
            st.markdown("""
            <div class="alert-box">
            <b>Active Monitoring:</b> Automatically flagged providers based on suspicious patterns and behavior.
            </div>
            """, unsafe_allow_html=True)
            
            if 'Provider/Facility Name' in filtered_df.columns:
                # Analyze all providers and flag high-risk ones
                st.subheader("High-Risk Providers Identified")
                
                with st.spinner("Analyzing providers for fraud patterns..."):
                    high_risk_providers = []
                    
                    # Get top 50 providers by volume
                    top_providers = filtered_df['Provider/Facility Name'].value_counts().head(50)
                    
                    for provider in top_providers.index:
                        provider_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                        flags, risk_score = calculate_fraud_flags(provider_df, filtered_df)
                        
                        if risk_score >= 45:  # Medium to high risk threshold
                            high_risk_providers.append({
                                'Provider': provider,
                                'Risk Score': risk_score,
                                'Total Disputes': len(provider_df),
                                'Flags': len(flags),
                                'Flag Details': ' | '.join([f[0] for f in flags])
                            })
                    
                    risk_df = pd.DataFrame(high_risk_providers).sort_values('Risk Score', ascending=False)
                
                if len(risk_df) > 0:
                    st.markdown(f"""
                    <div class="warning-box">
                    <b>⚠️ {len(risk_df)} HIGH-RISK PROVIDERS DETECTED</b><br/>
                    These providers exhibit multiple fraud risk indicators and warrant immediate investigation.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Color code by risk level
                    def highlight_risk(row):
                        if row['Risk Score'] >= 75:
                            return ['background-color: #fff5f5'] * len(row)
                        elif row['Risk Score'] >= 60:
                            return ['background-color: #fffaf0'] * len(row)
                        else:
                            return ['background-color: #f0fff4'] * len(row)
                    
                    styled_df = risk_df.style.apply(highlight_risk, axis=1)
                    st.dataframe(styled_df, use_container_width=True, height=500)
                    
                    # Download flagged providers
                    csv = risk_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Flagged Providers List",
                        data=csv,
                        file_name=f"flagged_providers_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                    
                    # Summary statistics
                    st.subheader("Risk Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        critical = len(risk_df[risk_df['Risk Score'] >= 75])
                        st.metric("🔴 Critical Risk", critical)
                    
                    with col2:
                        high = len(risk_df[(risk_df['Risk Score'] >= 60) & (risk_df['Risk Score'] < 75)])
                        st.metric("🟠 High Risk", high)
                    
                    with col3:
                        medium = len(risk_df[(risk_df['Risk Score'] >= 45) & (risk_df['Risk Score'] < 60)])
                        st.metric("🟡 Medium Risk", medium)
                    
                else:
                    st.success("✅ No high-risk providers detected in current filtered dataset")
        
        # TAB 9: COMPARE (NEW)
        with tab9:
            st.header("📊 Comparative Analysis")
            
            st.markdown("""
            <div class="warning-box">
            <b>Benchmarking:</b> Compare specific providers against industry averages and peer groups.
            </div>
            """, unsafe_allow_html=True)
            
            if 'Provider/Facility Name' in filtered_df.columns:
                st.subheader("Select Providers to Compare")
                
                # Multi-select for comparison
                top_providers = filtered_df['Provider/Facility Name'].value_counts().head(50).index.tolist()
                
                selected_providers = st.multiselect(
                    "Select up to 5 providers to compare:",
                    top_providers,
                    max_selections=5
                )
                
                if len(selected_providers) >= 2:
                    st.subheader("Comparison Analysis")
                    
                    comparison_data = []
                    
                    for provider in selected_providers:
                        provider_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                        
                        # Calculate metrics
                        total_disputes = len(provider_df)
                        
                        if 'Payment Determination Outcome' in provider_df.columns:
                            wins = (provider_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                            win_rate = (wins / total_disputes * 100) if total_disputes > 0 else 0
                        else:
                            win_rate = None
                        
                        if 'Provider/Facility Offer as % of QPA' in provider_df.columns:
                            avg_offer = provider_df['Provider/Facility Offer as % of QPA'].median()
                        else:
                            avg_offer = None
                        
                        if 'Type of Dispute' in provider_df.columns:
                            batch_rate = (provider_df['Type of Dispute'] == 'Batched').sum() / total_disputes * 100
                        else:
                            batch_rate = None
                        
                        if 'Location of Service' in provider_df.columns:
                            states = provider_df['Location of Service'].nunique()
                        else:
                            states = None
                        
                        comparison_data.append({
                            'Provider': provider[:40],  # Truncate long names
                            'Disputes': total_disputes,
                            'Win Rate %': f"{win_rate:.1f}" if win_rate else "N/A",
                            'Median Offer % QPA': f"{avg_offer:.0f}" if avg_offer else "N/A",
                            'Batch Rate %': f"{batch_rate:.1f}" if batch_rate else "N/A",
                            'States': states if states else "N/A"
                        })
                    
                    comparison_df = pd.DataFrame(comparison_data)
                    
                    # Display comparison table
                    st.dataframe(comparison_df, use_container_width=True)
                    
                    # Visualize comparisons
                    st.subheader("Visual Comparison")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Dispute volume comparison
                        fig = px.bar(
                            comparison_df,
                            x='Provider',
                            y='Disputes',
                            title="Dispute Volume Comparison",
                            color='Disputes',
                            color_continuous_scale='Reds'
                        )
                        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Win rate comparison
                        comparison_df['Win Rate Numeric'] = pd.to_numeric(comparison_df['Win Rate %'], errors='coerce')
                        fig = px.bar(
                            comparison_df,
                            x='Provider',
                            y='Win Rate Numeric',
                            title="Win Rate Comparison (%)",
                            color='Win Rate Numeric',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(showlegend=False, xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Add industry benchmarks
                    st.subheader("Industry Benchmarks")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if 'Payment Determination Outcome' in filtered_df.columns:
                            industry_win_rate = (filtered_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum() / len(filtered_df) * 100
                            st.metric("Industry Avg Win Rate", f"{industry_win_rate:.1f}%")
                    
                    with col2:
                        if 'Provider/Facility Offer as % of QPA' in filtered_df.columns:
                            industry_offer = filtered_df['Provider/Facility Offer as % of QPA'].median()
                            st.metric("Industry Median Offer", f"{industry_offer:.0f}% of QPA")
                    
                    with col3:
                        if 'Type of Dispute' in filtered_df.columns:
                            industry_batch = (filtered_df['Type of Dispute'] == 'Batched').sum() / len(filtered_df) * 100
                            st.metric("Industry Batch Rate", f"{industry_batch:.1f}%")
                
                elif len(selected_providers) == 1:
                    st.info("Select at least 2 providers to enable comparison")
                else:
                    st.info("Select providers from the dropdown above to begin comparison analysis")
    
    else:
        # Welcome screen
        if db_info:
            st.info("Use the filters in the sidebar to explore the data.")
        else:
            st.info("""
            ## 👋 Welcome to the IDR Intelligence Platform
            
            **Investigative Intelligence & Fraud Detection System**
            
            This platform provides:
            - **Executive dashboards** for topline analytics
            - **Deep-dive investigations** on specific providers
            - **Automated fraud detection** with risk scoring
            - **Comparative analysis** tools for benchmarking
            
            **To get started:**
            1. Click "Load Data from CSV Files" in the sidebar
            2. The system will scan your `idr_data` folder and import all quarterly data
            3. Data persists - you only load once!
            4. Explore the 9 analysis tabs
            
            **New Investigation Features:**
            - 🔍 **Investigate Tab**: Search providers and generate detailed investigation reports
            - 🚩 **Fraud Alerts Tab**: Automated detection of high-risk providers
            - 📊 **Compare Tab**: Benchmark providers against industry averages
            """)

if __name__ == "__main__":
    main()
