import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# Supabase connection
@st.cache_resource
def get_supabase_client():
    """Initialize Supabase client"""
    try:
        from supabase import create_client
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Could not connect to Supabase: {e}")
        return None

@st.cache_data(ttl=3600)
def load_data_from_supabase():
    """Load data from Supabase with caching"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        # Fetch data in batches (Supabase has row limits)
        all_data = []
        batch_size = 10000
        offset = 0
        
        with st.spinner("Loading data from database..."):
            progress = st.progress(0)
            
            while True:
                response = supabase.table('idr_disputes').select('*').range(offset, offset + batch_size - 1).execute()
                
                if not response.data:
                    break
                
                all_data.extend(response.data)
                offset += batch_size
                
                # Update progress (estimate based on expected ~2.5M records)
                progress.progress(min(offset / 2500000, 0.99))
                
                if len(response.data) < batch_size:
                    break
            
            progress.progress(1.0)
        
        df = pd.DataFrame(all_data)
        
        # Rename columns back to friendly names for display
        column_mapping = {
            'dispute_number': 'Dispute Number',
            'dli_number': 'DLI Number',
            'outcome': 'Payment Determination Outcome',
            'default_decision': 'Default Decision',
            'dispute_type': 'Type of Dispute',
            'provider_group': 'Provider/Facility Group Name',
            'provider_name': 'Provider/Facility Name',
            'provider_email': 'Provider Email Domain',
            'provider_npi': 'Provider/Facility NPI Number',
            'facility_size': 'Practice/Facility Size',
            'payer_name': 'Health Plan/Issuer Name',
            'payer_email': 'Health Plan/Issuer Email Domain',
            'plan_type': 'Health Plan Type',
            'determination_time': 'Length of Time to Make Determination',
            'idre_compensation': 'IDRE Compensation',
            'line_item_type': 'Dispute Line Item Type',
            'service_code_type': 'Type of Service Code',
            'service_code': 'Service Code',
            'place_of_service': 'Place of Service Code',
            'service_description': 'Item or Service Description',
            'state': 'Location of Service',
            'specialty': 'Practice/Facility Specialty or Type',
            'provider_offer_pct': 'Provider/Facility Offer as % of QPA',
            'payer_offer_pct': 'Health Plan/Issuer Offer as % of QPA',
            'offer_selected': 'Offer Selected from Provider or Issuer',
            'prevailing_offer_pct': 'Prevailing Party Offer as % of QPA',
            'qpa_vs_median': 'QPA as Percent of Median QPA',
            'provider_offer_vs_median': 'Provider Offer vs Median',
            'payer_offer_vs_median': 'Payer Offer vs Median',
            'prevailing_vs_median': 'Prevailing vs Median',
            'quarter': 'quarter',
            'data_loaded_at': 'data_loaded_at',
            'provider_offer_pct2': 'Provider Offer Pct 2',
            'payer_offer_pct2': 'Payer Offer Pct 2',
            'prevailing_offer_pct2': 'Prevailing Offer Pct 2',
            'initiating_party': 'Initiating Party'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Clean percentage columns
        pct_columns = [col for col in df.columns if 'Percent' in col or '% of QPA' in col or 'Offer' in col]
        for col in pct_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean IDRE Compensation
        if 'IDRE Compensation' in df.columns:
            df['IDRE Compensation'] = pd.to_numeric(
                df['IDRE Compensation'].astype(str).str.replace('$', '').str.replace(',', ''),
                errors='coerce'
            )
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def calculate_fraud_flags(provider_df, full_df):
    """Calculate fraud risk flags for a provider"""
    flags = []
    
    # Flag 1: High volume
    total_disputes = len(provider_df)
    if total_disputes > 1000:
        flags.append(("🚩 HIGH VOLUME", f"{total_disputes:,} disputes - Industrial scale filing"))
    
    # Flag 2: Extreme pricing
    if 'Provider/Facility Offer as % of QPA' in provider_df.columns:
        avg_offer = provider_df['Provider/Facility Offer as % of QPA'].mean()
        if pd.notna(avg_offer) and avg_offer > 500:
            flags.append(("🚩 EXTREME PRICING", f"Average offer {avg_offer:.0f}% of QPA"))
    
    # Flag 3: High batch rate
    if 'Type of Dispute' in provider_df.columns:
        batch_rate = (provider_df['Type of Dispute'] == 'Batched').sum() / len(provider_df) * 100
        if batch_rate > 90:
            flags.append(("🚩 BATCH ABUSER", f"{batch_rate:.1f}% of disputes are batched"))
    
    # Flag 4: Rapid growth
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
    
    risk_score = min(100, len(flags) * 15)
    
    return flags, risk_score

def render_provider_deep_dive(provider_name, df):
    """Render detailed provider investigation page"""
    provider_df = df[df['Provider/Facility Name'] == provider_name]
    
    if len(provider_df) == 0:
        st.warning("No data found for this provider")
        return
    
    st.markdown(f"## 🔍 Investigation: {provider_name}")
    
    flags, risk_score = calculate_fraud_flags(provider_df, df)
    
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
    
    if flags:
        st.markdown("### 🚩 Fraud Risk Indicators")
        for flag_type, description in flags:
            st.markdown(f'<div class="fraud-flag">{flag_type}: {description}</div>', unsafe_allow_html=True)
        st.markdown("")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Timeline", "💰 Financial", "🗺️ Geography", "📊 Patterns"])
    
    with tab1:
        st.subheader("Dispute Volume Over Time")
        if 'quarter' in provider_df.columns:
            quarterly = provider_df['quarter'].value_counts().sort_index()
            fig = px.line(x=quarterly.index, y=quarterly.values, markers=True,
                         labels={'x': 'Quarter', 'y': 'Number of Disputes'})
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Financial Analysis")
        col1, col2 = st.columns(2)
        with col1:
            if 'Provider/Facility Offer as % of QPA' in provider_df.columns:
                offers = provider_df['Provider/Facility Offer as % of QPA'].dropna()
                if len(offers) > 0:
                    st.metric("Median Offer (% of QPA)", f"{offers.median():.0f}%")
        with col2:
            if 'IDRE Compensation' in provider_df.columns:
                fees = provider_df['IDRE Compensation'].dropna()
                if len(fees) > 0:
                    st.metric("Total IDRE Fees", f"${fees.sum():,.0f}")
    
    with tab3:
        st.subheader("Geographic Footprint")
        if 'Location of Service' in provider_df.columns:
            state_counts = provider_df['Location of Service'].value_counts().head(15)
            fig = px.bar(x=state_counts.values, y=state_counts.index, orientation='h',
                        labels={'x': 'Number of Disputes', 'y': 'State'})
            st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("Filing Patterns")
        col1, col2 = st.columns(2)
        with col1:
            if 'Type of Dispute' in provider_df.columns:
                dispute_types = provider_df['Type of Dispute'].value_counts()
                fig = px.pie(values=dispute_types.values, names=dispute_types.index,
                           title="Batch vs Single Filing")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if 'Health Plan/Issuer Name' in provider_df.columns:
                st.write("**Top 10 Targeted Payers:**")
                payer_counts = provider_df['Health Plan/Issuer Name'].value_counts().head(10)
                for payer, count in payer_counts.items():
                    pct = (count / len(provider_df)) * 100
                    st.write(f"- {payer}: {count:,} ({pct:.1f}%)")

def main():
    st.markdown('<p class="main-header">🔍 IDR Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Investigative Intelligence & Fraud Detection System</p>', unsafe_allow_html=True)
    
    # Load data
    df = load_data_from_supabase()
    
    if df is None or len(df) == 0:
        st.error("Could not load data from database. Please check your Supabase configuration.")
        st.info("Make sure you have set up your Supabase secrets in Streamlit Cloud.")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("💾 Database Status")
        st.markdown(f"""
        <div class="success-box">
        <b>✅ Connected</b><br/>
        Records: {len(df):,}<br/>
        Quarters: {df['quarter'].nunique() if 'quarter' in df.columns else 'N/A'}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.header("🎛️ Filters")
        
        # Quarter filter
        if 'quarter' in df.columns:
            quarters = ['All'] + sorted(df['quarter'].dropna().unique().tolist())
            selected_quarter = st.multiselect("Quarter", quarters, default=['All'])
        
        # Specialty filter
        if 'Practice/Facility Specialty or Type' in df.columns:
            specialties = ['All'] + sorted(df['Practice/Facility Specialty or Type'].dropna().unique().tolist()[:50])
            selected_specialties = st.multiselect("Specialty (Top 50)", specialties, default=['All'])
        
        # State filter
        if 'Location of Service' in df.columns:
            states = ['All'] + sorted(df['Location of Service'].dropna().unique().tolist())
            selected_states = st.multiselect("State", states, default=['All'])
        
        # Payer filter
        if 'Health Plan/Issuer Name' in df.columns:
            payers = ['All'] + sorted(df['Health Plan/Issuer Name'].dropna().unique().tolist()[:30])
            selected_payers = st.multiselect("Payer (Top 30)", payers, default=['All'])
        
        # Apply filters
        filtered_df = df.copy()
        
        if 'quarter' in df.columns and 'All' not in selected_quarter:
            filtered_df = filtered_df[filtered_df['quarter'].isin(selected_quarter)]
        
        if 'Practice/Facility Specialty or Type' in df.columns and 'All' not in selected_specialties:
            filtered_df = filtered_df[filtered_df['Practice/Facility Specialty or Type'].isin(selected_specialties)]
        
        if 'Location of Service' in df.columns and 'All' not in selected_states:
            filtered_df = filtered_df[filtered_df['Location of Service'].isin(selected_states)]
        
        if 'Health Plan/Issuer Name' in df.columns and 'All' not in selected_payers:
            filtered_df = filtered_df[filtered_df['Health Plan/Issuer Name'].isin(selected_payers)]
        
        st.markdown("---")
        st.info(f"📊 Showing {len(filtered_df):,} of {len(df):,} disputes")
    
    # Main tabs
    tabs = st.tabs([
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
    
    # TAB 1: OVERVIEW
    with tabs[0]:
        st.header("Executive Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Disputes", f"{len(filtered_df):,}")
        
        with col2:
            if 'Payment Determination Outcome' in filtered_df.columns:
                wins = (filtered_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                st.metric("Provider Win Rate", f"{wins/len(filtered_df)*100:.1f}%")
        
        with col3:
            if 'Type of Dispute' in filtered_df.columns:
                batch = (filtered_df['Type of Dispute'] == 'Batched').sum()
                st.metric("Batch Rate", f"{batch/len(filtered_df)*100:.1f}%")
        
        with col4:
            if 'IDRE Compensation' in filtered_df.columns:
                total_fees = filtered_df['IDRE Compensation'].sum()
                st.metric("Total IDRE Fees", f"${total_fees:,.0f}")
        
        st.markdown("---")
        
        if 'quarter' in filtered_df.columns:
            st.subheader("Quarterly Trends")
            quarterly = filtered_df['quarter'].value_counts().sort_index()
            fig = px.bar(x=quarterly.index, y=quarterly.values, labels={'x': 'Quarter', 'y': 'Disputes'})
            fig.update_traces(marker_color='#1a5490')
            st.plotly_chart(fig, use_container_width=True)
        
        if 'Payment Determination Outcome' in filtered_df.columns:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Outcomes")
                outcomes = filtered_df['Payment Determination Outcome'].value_counts()
                fig = px.pie(values=outcomes.values, names=outcomes.index)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'Type of Dispute' in filtered_df.columns:
                    st.subheader("Dispute Types")
                    types = filtered_df['Type of Dispute'].value_counts()
                    fig = px.pie(values=types.values, names=types.index)
                    st.plotly_chart(fig, use_container_width=True)
    
    # TAB 2: PROVIDERS
    with tabs[1]:
        st.header("Provider Analysis")
        
        if 'Provider/Facility Name' in filtered_df.columns:
            st.markdown("""
            <div class="alert-box">
            <b>⚠️ IDR Mills:</b> High-volume dispute filers
            </div>
            """, unsafe_allow_html=True)
            
            provider_counts = filtered_df['Provider/Facility Name'].value_counts().head(20)
            provider_data = []
            
            for provider in provider_counts.index:
                prov_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                total = len(prov_df)
                
                if 'Payment Determination Outcome' in filtered_df.columns:
                    wins = (prov_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                    win_rate = f"{wins/total*100:.1f}%"
                else:
                    win_rate = "N/A"
                
                provider_data.append({
                    'Provider': provider,
                    'Disputes': total,
                    'Win Rate': win_rate,
                    '% Total': f"{total/len(filtered_df)*100:.2f}%"
                })
            
            summary = pd.DataFrame(provider_data)
            st.dataframe(summary, use_container_width=True, height=600)
            
            fig = px.bar(summary.head(10), x='Disputes', y='Provider', orientation='h')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            csv = summary.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "providers.csv", "text/csv")
    
    # TAB 3: SPECIALTIES
    with tabs[2]:
        st.header("Specialty Analysis")
        
        if 'Practice/Facility Specialty or Type' in filtered_df.columns:
            spec_counts = filtered_df['Practice/Facility Specialty or Type'].value_counts().head(20)
            spec_data = []
            
            for spec in spec_counts.index:
                spec_df = filtered_df[filtered_df['Practice/Facility Specialty or Type'] == spec]
                total = len(spec_df)
                
                if 'Payment Determination Outcome' in filtered_df.columns:
                    wins = (spec_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                    win_rate = f"{wins/total*100:.1f}%"
                else:
                    win_rate = "N/A"
                
                spec_data.append({
                    'Specialty': spec,
                    'Disputes': total,
                    'Win Rate': win_rate,
                    '% Total': f"{total/len(filtered_df)*100:.1f}%"
                })
            
            summary = pd.DataFrame(spec_data)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.bar(summary.head(15), y='Specialty', x='Disputes', orientation='h',
                           color='Disputes', color_continuous_scale='Blues')
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(summary, height=600)
    
    # TAB 4: PAYERS
    with tabs[3]:
        st.header("Payer Analysis")
        
        if 'Health Plan/Issuer Name' in filtered_df.columns:
            payer_counts = filtered_df['Health Plan/Issuer Name'].value_counts().head(20)
            payer_data = []
            
            for payer in payer_counts.index:
                pay_df = filtered_df[filtered_df['Health Plan/Issuer Name'] == payer]
                total = len(pay_df)
                
                if 'Payment Determination Outcome' in filtered_df.columns:
                    losses = (pay_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                    loss_rate = f"{losses/total*100:.1f}%"
                else:
                    loss_rate = "N/A"
                
                payer_data.append({
                    'Payer': payer,
                    'Disputes': total,
                    'Loss Rate': loss_rate,
                    '% Total': f"{total/len(filtered_df)*100:.1f}%"
                })
            
            summary = pd.DataFrame(payer_data)
            st.dataframe(summary, use_container_width=True, height=500)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(summary.head(10), x='Disputes', y='Payer', orientation='h')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                summary['Loss Rate Num'] = summary['Loss Rate'].str.replace('%', '').str.replace('N/A', '0').astype(float)
                fig = px.bar(summary.head(10), x='Loss Rate Num', y='Payer', orientation='h',
                           labels={'Loss Rate Num': 'Loss Rate (%)'})
                fig.update_traces(marker_color='#fc8181')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    # TAB 5: GEOGRAPHY
    with tabs[4]:
        st.header("Geographic Analysis")
        
        if 'Location of Service' in filtered_df.columns:
            state_counts = filtered_df['Location of Service'].value_counts().head(20)
            state_data = []
            
            for state in state_counts.index:
                count = state_counts[state]
                state_data.append({
                    'State': state,
                    'Disputes': count,
                    '% Total': f"{count/len(filtered_df)*100:.1f}%"
                })
            
            summary = pd.DataFrame(state_data)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.bar(summary.head(15), x='State', y='Disputes',
                           color='Disputes', color_continuous_scale='Reds')
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(summary, height=500)
            
            if 'TX' in summary['State'].values:
                tx_pct = summary[summary['State'] == 'TX']['% Total'].values[0]
                st.markdown(f"""
                <div class="alert-box">
                <b>🎯 Texas:</b> {tx_pct} of disputes
                </div>
                """, unsafe_allow_html=True)
    
    # TAB 6: FINANCIAL
    with tabs[5]:
        st.header("Financial Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Provider/Facility Offer as % of QPA' in filtered_df.columns:
                st.subheader("Provider Offers")
                offers = filtered_df['Provider/Facility Offer as % of QPA'].dropna()
                if len(offers) > 0:
                    stats = {
                        'Stat': ['Mean', 'Median', '75th %', '90th %'],
                        'Value': [
                            f"{offers.mean():.1f}%",
                            f"{offers.median():.1f}%",
                            f"{offers.quantile(0.75):.1f}%",
                            f"{offers.quantile(0.90):.1f}%"
                        ]
                    }
                    st.dataframe(pd.DataFrame(stats), use_container_width=True)
        
        with col2:
            if 'Health Plan/Issuer Offer as % of QPA' in filtered_df.columns:
                st.subheader("Payer Offers")
                offers = filtered_df['Health Plan/Issuer Offer as % of QPA'].dropna()
                if len(offers) > 0:
                    stats = {
                        'Stat': ['Mean', 'Median', '25th %', '10th %'],
                        'Value': [
                            f"{offers.mean():.1f}%",
                            f"{offers.median():.1f}%",
                            f"{offers.quantile(0.25):.1f}%",
                            f"{offers.quantile(0.10):.1f}%"
                        ]
                    }
                    st.dataframe(pd.DataFrame(stats), use_container_width=True)
        
        if 'IDRE Compensation' in filtered_df.columns:
            st.subheader("IDRE Fees")
            fees = filtered_df['IDRE Compensation'].dropna()
            if len(fees) > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", f"${fees.sum():,.0f}")
                with col2:
                    st.metric("Average", f"${fees.mean():.2f}")
                with col3:
                    st.metric("Median", f"${fees.median():.2f}")
    
    # TAB 7: INVESTIGATE
    with tabs[6]:
        st.header("🔍 Investigation Tools")
        
        if 'Provider/Facility Name' in filtered_df.columns:
            st.subheader("Provider Search")
            
            search_query = st.text_input("Search for a provider:", placeholder="Enter provider name...")
            
            if search_query:
                matching = filtered_df[
                    filtered_df['Provider/Facility Name'].str.contains(search_query, case=False, na=False)
                ]['Provider/Facility Name'].value_counts()
                
                if len(matching) > 0:
                    st.write(f"Found {len(matching)} matching providers:")
                    selected = st.selectbox("Select provider:", matching.index.tolist())
                    
                    if st.button("🔍 Investigate", type="primary"):
                        st.markdown("---")
                        render_provider_deep_dive(selected, filtered_df)
                else:
                    st.warning("No providers found")
            else:
                st.subheader("High-Risk Providers")
                top = filtered_df['Provider/Facility Name'].value_counts().head(10)
                risk_data = []
                for provider in top.index:
                    prov_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                    flags, score = calculate_fraud_flags(prov_df, filtered_df)
                    risk_data.append({
                        'Provider': provider,
                        'Disputes': len(prov_df),
                        'Risk Score': score,
                        'Flags': len(flags)
                    })
                
                st.dataframe(pd.DataFrame(risk_data).sort_values('Risk Score', ascending=False), use_container_width=True)
    
    # TAB 8: FRAUD ALERTS
    with tabs[7]:
        st.header("🚩 Fraud Detection")
        
        if 'Provider/Facility Name' in filtered_df.columns:
            st.markdown("""
            <div class="warning-box">
            <b>Auto-flagged providers</b> based on suspicious patterns
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Analyzing providers..."):
                top_providers = filtered_df['Provider/Facility Name'].value_counts().head(50)
                high_risk = []
                
                for provider in top_providers.index:
                    prov_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                    flags, risk = calculate_fraud_flags(prov_df, filtered_df)
                    
                    if risk >= 45:
                        high_risk.append({
                            'Provider': provider,
                            'Risk Score': risk,
                            'Disputes': len(prov_df),
                            'Flags': len(flags),
                            'Details': ' | '.join([f[0] for f in flags])
                        })
                
                risk_df = pd.DataFrame(high_risk).sort_values('Risk Score', ascending=False)
            
            if len(risk_df) > 0:
                st.markdown(f"**⚠️ {len(risk_df)} HIGH-RISK PROVIDERS**")
                st.dataframe(risk_df, use_container_width=True, height=500)
                
                csv = risk_df.to_csv(index=False)
                st.download_button("📥 Download Flagged List", csv, f"flagged_providers_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
            else:
                st.success("✅ No high-risk providers detected")
    
    # TAB 9: COMPARE
    with tabs[8]:
        st.header("📊 Comparative Analysis")
        
        if 'Provider/Facility Name' in filtered_df.columns:
            top = filtered_df['Provider/Facility Name'].value_counts().head(50).index.tolist()
            selected = st.multiselect("Select up to 5 providers:", top, max_selections=5)
            
            if len(selected) >= 2:
                comp_data = []
                
                for provider in selected:
                    prov_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                    total = len(prov_df)
                    
                    win_rate = None
                    if 'Payment Determination Outcome' in prov_df.columns:
                        wins = (prov_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                        win_rate = wins / total * 100
                    
                    comp_data.append({
                        'Provider': provider[:40],
                        'Disputes': total,
                        'Win Rate %': f"{win_rate:.1f}" if win_rate else "N/A"
                    })
                
                comp_df = pd.DataFrame(comp_data)
                st.dataframe(comp_df, use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.bar(comp_df, x='Provider', y='Disputes', title="Dispute Volume",
                               color='Disputes', color_continuous_scale='Reds')
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    comp_df['Win Rate Num'] = pd.to_numeric(comp_df['Win Rate %'], errors='coerce')
                    fig = px.bar(comp_df, x='Provider', y='Win Rate Num', title="Win Rate (%)",
                               color='Win Rate Num', color_continuous_scale='Blues')
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
            elif len(selected) == 1:
                st.info("Select at least 2 providers to compare")
            else:
                st.info("Select providers to compare")

if __name__ == "__main__":
    main()
