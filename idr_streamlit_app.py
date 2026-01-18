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
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1a5490; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #4a5568; margin-bottom: 2rem; }
    .alert-box { background-color: #fff5f5; border-left: 4px solid #fc8181; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
    .success-box { background-color: #f0fff4; border-left: 4px solid #48bb78; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
    .warning-box { background-color: #fffaf0; border-left: 4px solid #ed8936; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
    .fraud-flag { background-color: #fff5f5; border: 2px solid #fc8181; padding: 0.5rem 1rem; border-radius: 4px; display: inline-block; margin: 0.25rem; font-weight: 600; color: #c53030; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase_client():
    """Initialize Supabase client"""
    try:
        from supabase import create_client
        import os
        
        # Try Railway environment variables first, then Streamlit secrets
        url = os.environ.get('SUPABASE_URL') or st.secrets.get("supabase", {}).get("url")
        key = os.environ.get('SUPABASE_KEY') or st.secrets.get("supabase", {}).get("key")
        
        if not url or not key:
            st.error("Supabase credentials not found. Set SUPABASE_URL and SUPABASE_KEY environment variables.")
            return None
            
        return create_client(url, key)
    except Exception as e:
        st.error(f"Could not connect to Supabase: {e}")
        return None

@st.cache_data(ttl=3600)
def get_record_count():
    """Get total record count"""
    supabase = get_supabase_client()
    if not supabase:
        return 0
    try:
        response = supabase.table('idr_disputes').select('*', count='exact').limit(1).execute()
        return response.count
    except:
        return 0

@st.cache_data(ttl=3600)
def get_quarters():
    """Get list of quarters"""
    supabase = get_supabase_client()
    if not supabase:
        return []
    try:
        response = supabase.table('idr_disputes').select('quarter').execute()
        quarters = list(set([r['quarter'] for r in response.data if r.get('quarter')]))
        return sorted(quarters)
    except:
        return []

@st.cache_data(ttl=3600)
def load_sample_data(sample_size=100000):
    """Load a sample of data for analysis"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        all_data = []
        batch_size = 1000
        offset = 0
        
        while len(all_data) < sample_size:
            response = supabase.table('idr_disputes').select('*').range(offset, offset + batch_size - 1).execute()
            
            if not response.data:
                break
            
            all_data.extend(response.data)
            offset += batch_size
            
            if len(response.data) < batch_size:
                break
        
        df = pd.DataFrame(all_data)
        
        # Rename columns
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
        
        # Clean numeric columns
        if 'Provider/Facility Offer as % of QPA' in df.columns:
            df['Provider/Facility Offer as % of QPA'] = pd.to_numeric(df['Provider/Facility Offer as % of QPA'], errors='coerce')
        if 'Health Plan/Issuer Offer as % of QPA' in df.columns:
            df['Health Plan/Issuer Offer as % of QPA'] = pd.to_numeric(df['Health Plan/Issuer Offer as % of QPA'], errors='coerce')
        if 'IDRE Compensation' in df.columns:
            df['IDRE Compensation'] = pd.to_numeric(
                df['IDRE Compensation'].astype(str).str.replace('$', '').str.replace(',', ''),
                errors='coerce'
            )
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

@st.cache_data(ttl=3600)
def get_provider_data(provider_name):
    """Get all data for a specific provider"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        all_data = []
        batch_size = 1000
        offset = 0
        
        while True:
            response = supabase.table('idr_disputes').select('*').eq('provider_name', provider_name).range(offset, offset + batch_size - 1).execute()
            
            if not response.data:
                break
            
            all_data.extend(response.data)
            offset += batch_size
            
            if len(response.data) < batch_size:
                break
        
        if not all_data:
            return None
            
        df = pd.DataFrame(all_data)
        
        # Rename columns (same mapping as above)
        column_mapping = {
            'dispute_number': 'Dispute Number',
            'outcome': 'Payment Determination Outcome',
            'dispute_type': 'Type of Dispute',
            'provider_name': 'Provider/Facility Name',
            'payer_name': 'Health Plan/Issuer Name',
            'idre_compensation': 'IDRE Compensation',
            'state': 'Location of Service',
            'specialty': 'Practice/Facility Specialty or Type',
            'provider_offer_pct': 'Provider/Facility Offer as % of QPA',
            'quarter': 'quarter',
        }
        df = df.rename(columns={k:v for k,v in column_mapping.items() if k in df.columns})
        
        return df
    except Exception as e:
        return None

def calculate_fraud_flags(provider_df, total_records):
    """Calculate fraud risk flags for a provider"""
    flags = []
    
    total_disputes = len(provider_df)
    if total_disputes > 1000:
        flags.append(("🚩 HIGH VOLUME", f"{total_disputes:,} disputes - Industrial scale filing"))
    
    if 'Provider/Facility Offer as % of QPA' in provider_df.columns:
        offers = pd.to_numeric(provider_df['Provider/Facility Offer as % of QPA'], errors='coerce')
        avg_offer = offers.mean()
        if pd.notna(avg_offer) and avg_offer > 500:
            flags.append(("🚩 EXTREME PRICING", f"Average offer {avg_offer:.0f}% of QPA"))
    
    if 'Type of Dispute' in provider_df.columns:
        batch_count = (provider_df['Type of Dispute'] == 'Batched').sum()
        batch_rate = batch_count / len(provider_df) * 100 if len(provider_df) > 0 else 0
        if batch_rate > 90:
            flags.append(("🚩 BATCH ABUSER", f"{batch_rate:.1f}% of disputes are batched"))
    
    if 'Location of Service' in provider_df.columns:
        states = provider_df['Location of Service'].nunique()
        if states > 10:
            flags.append(("🚩 MULTI-STATE OPERATION", f"Filing in {states} different states"))
    
    if 'Health Plan/Issuer Name' in provider_df.columns:
        payer_counts = provider_df['Health Plan/Issuer Name'].value_counts()
        if len(payer_counts) > 0:
            top_payer_pct = (payer_counts.iloc[0] / len(provider_df)) * 100
            if top_payer_pct > 80:
                flags.append(("🚩 PAYER TARGETING", f"{top_payer_pct:.0f}% against one payer"))
    
    risk_score = min(100, len(flags) * 20 + (total_disputes // 1000) * 5)
    
    return flags, risk_score

def main():
    st.markdown('<p class="main-header">🔍 IDR Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Investigative Intelligence & Fraud Detection System</p>', unsafe_allow_html=True)
    
    # Get counts
    total_records = get_record_count()
    quarters = get_quarters()
    
    # Load sample data
    df = load_sample_data(100000)
    
    if df is None or len(df) == 0:
        st.error("Could not load data. Check Supabase configuration.")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("💾 Database Status")
        st.markdown(f"""
        <div class="success-box">
        <b>✅ Connected</b><br/>
        Total Records: {total_records:,}<br/>
        Sample Loaded: {len(df):,}<br/>
        Quarters: {len(quarters)}
        </div>
        """, unsafe_allow_html=True)
        
        st.info("📊 Analysis based on sample data. Provider investigations load full data.")
        
        st.markdown("---")
        st.header("🎛️ Filters")
        
        if 'quarter' in df.columns:
            quarter_opts = ['All'] + sorted(df['quarter'].dropna().unique().tolist())
            selected_quarter = st.multiselect("Quarter", quarter_opts, default=['All'])
        
        if 'Practice/Facility Specialty or Type' in df.columns:
            spec_opts = ['All'] + sorted(df['Practice/Facility Specialty or Type'].dropna().unique().tolist()[:30])
            selected_specs = st.multiselect("Specialty", spec_opts, default=['All'])
        
        if 'Location of Service' in df.columns:
            state_opts = ['All'] + sorted(df['Location of Service'].dropna().unique().tolist())
            selected_states = st.multiselect("State", state_opts, default=['All'])
        
        # Apply filters
        filtered_df = df.copy()
        
        if 'quarter' in df.columns and 'All' not in selected_quarter:
            filtered_df = filtered_df[filtered_df['quarter'].isin(selected_quarter)]
        
        if 'Practice/Facility Specialty or Type' in df.columns and 'All' not in selected_specs:
            filtered_df = filtered_df[filtered_df['Practice/Facility Specialty or Type'].isin(selected_specs)]
        
        if 'Location of Service' in df.columns and 'All' not in selected_states:
            filtered_df = filtered_df[filtered_df['Location of Service'].isin(selected_states)]
        
        st.markdown("---")
        st.info(f"📊 Showing {len(filtered_df):,} records")
    
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
        st.caption(f"Based on {total_records:,} total disputes in database")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Disputes", f"{total_records:,}")
        
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
                avg_fee = filtered_df['IDRE Compensation'].mean()
                est_total = avg_fee * total_records if pd.notna(avg_fee) else 0
                st.metric("Est. Total IDRE Fees", f"${est_total:,.0f}")
        
        st.markdown("---")
        
        if 'quarter' in filtered_df.columns:
            st.subheader("Quarterly Trends")
            quarterly = filtered_df['quarter'].value_counts().sort_index()
            fig = px.bar(x=quarterly.index, y=quarterly.values, labels={'x': 'Quarter', 'y': 'Disputes'})
            fig.update_traces(marker_color='#1a5490')
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if 'Payment Determination Outcome' in filtered_df.columns:
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
        st.caption("Top providers by dispute volume")
        
        if 'Provider/Facility Name' in filtered_df.columns:
            provider_counts = filtered_df['Provider/Facility Name'].value_counts().head(20)
            provider_data = []
            
            for provider in provider_counts.index:
                prov_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                total = len(prov_df)
                
                win_rate = "N/A"
                if 'Payment Determination Outcome' in prov_df.columns:
                    wins = (prov_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                    win_rate = f"{wins/total*100:.1f}%"
                
                provider_data.append({
                    'Provider': provider,
                    'Disputes (Sample)': total,
                    'Win Rate': win_rate,
                })
            
            summary = pd.DataFrame(provider_data)
            st.dataframe(summary, use_container_width=True, height=500)
            
            fig = px.bar(summary.head(10), x='Disputes (Sample)', y='Provider', orientation='h')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # TAB 3: SPECIALTIES
    with tabs[2]:
        st.header("Specialty Analysis")
        
        if 'Practice/Facility Specialty or Type' in filtered_df.columns:
            spec_counts = filtered_df['Practice/Facility Specialty or Type'].value_counts().head(15)
            
            fig = px.bar(y=spec_counts.index, x=spec_counts.values, orientation='h',
                       labels={'x': 'Disputes', 'y': 'Specialty'},
                       color=spec_counts.values, color_continuous_scale='Blues')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    # TAB 4: PAYERS
    with tabs[3]:
        st.header("Payer Analysis")
        
        if 'Health Plan/Issuer Name' in filtered_df.columns:
            payer_counts = filtered_df['Health Plan/Issuer Name'].value_counts().head(15)
            
            payer_data = []
            for payer in payer_counts.index:
                pay_df = filtered_df[filtered_df['Health Plan/Issuer Name'] == payer]
                total = len(pay_df)
                
                loss_rate = "N/A"
                if 'Payment Determination Outcome' in pay_df.columns:
                    losses = (pay_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                    loss_rate = f"{losses/total*100:.1f}%"
                
                payer_data.append({'Payer': payer, 'Disputes': total, 'Loss Rate': loss_rate})
            
            st.dataframe(pd.DataFrame(payer_data), use_container_width=True)
            
            fig = px.bar(x=payer_counts.values, y=payer_counts.index, orientation='h',
                        labels={'x': 'Disputes', 'y': 'Payer'})
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    # TAB 5: GEOGRAPHY
    with tabs[4]:
        st.header("Geographic Analysis")
        
        if 'Location of Service' in filtered_df.columns:
            state_counts = filtered_df['Location of Service'].value_counts().head(20)
            
            fig = px.bar(x=state_counts.index, y=state_counts.values,
                       labels={'x': 'State', 'y': 'Disputes'},
                       color=state_counts.values, color_continuous_scale='Reds')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            if 'TX' in state_counts.index:
                tx_pct = state_counts['TX'] / state_counts.sum() * 100
                st.markdown(f"""
                <div class="alert-box">
                <b>🎯 Texas Concentration:</b> {tx_pct:.1f}% of all disputes
                </div>
                """, unsafe_allow_html=True)
    
    # TAB 6: FINANCIAL
    with tabs[5]:
        st.header("Financial Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Provider/Facility Offer as % of QPA' in filtered_df.columns:
                st.subheader("Provider Offers (% of QPA)")
                offers = filtered_df['Provider/Facility Offer as % of QPA'].dropna()
                if len(offers) > 0:
                    col_a, col_b = st.columns(2)
                    col_a.metric("Median", f"{offers.median():.0f}%")
                    col_b.metric("Mean", f"{offers.mean():.0f}%")
        
        with col2:
            if 'Health Plan/Issuer Offer as % of QPA' in filtered_df.columns:
                st.subheader("Payer Offers (% of QPA)")
                offers = filtered_df['Health Plan/Issuer Offer as % of QPA'].dropna()
                if len(offers) > 0:
                    col_a, col_b = st.columns(2)
                    col_a.metric("Median", f"{offers.median():.0f}%")
                    col_b.metric("Mean", f"{offers.mean():.0f}%")
        
        if 'IDRE Compensation' in filtered_df.columns:
            st.subheader("IDRE Fees")
            fees = filtered_df['IDRE Compensation'].dropna()
            if len(fees) > 0:
                col1, col2, col3 = st.columns(3)
                col1.metric("Average Fee", f"${fees.mean():.2f}")
                col2.metric("Median Fee", f"${fees.median():.2f}")
                col3.metric("Est. Total (All Records)", f"${fees.mean() * total_records:,.0f}")
    
    # TAB 7: INVESTIGATE
    with tabs[6]:
        st.header("🔍 Provider Investigation")
        
        st.markdown("""
        <div class="warning-box">
        <b>Deep Dive:</b> Enter a provider name to load their FULL dispute history from the database.
        </div>
        """, unsafe_allow_html=True)
        
        # Get top providers from sample
        if 'Provider/Facility Name' in filtered_df.columns:
            top_providers = filtered_df['Provider/Facility Name'].value_counts().head(20).index.tolist()
            
            col1, col2 = st.columns([2, 1])
            with col1:
                search = st.text_input("Search provider name:", placeholder="Enter name...")
            with col2:
                quick_select = st.selectbox("Or select top provider:", [""] + top_providers)
            
            provider_to_investigate = quick_select if quick_select else search
            
            if provider_to_investigate and st.button("🔍 Investigate", type="primary"):
                with st.spinner(f"Loading all data for {provider_to_investigate}..."):
                    prov_df = get_provider_data(provider_to_investigate)
                
                if prov_df is not None and len(prov_df) > 0:
                    st.markdown("---")
                    st.subheader(f"📋 {provider_to_investigate}")
                    
                    flags, risk_score = calculate_fraud_flags(prov_df, total_records)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        color = "inverse" if risk_score >= 60 else ("off" if risk_score >= 30 else "normal")
                        st.metric("Risk Score", f"{risk_score}/100")
                    with col2:
                        st.metric("Total Disputes", f"{len(prov_df):,}")
                    with col3:
                        if 'Payment Determination Outcome' in prov_df.columns:
                            wins = (prov_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                            st.metric("Win Rate", f"{wins/len(prov_df)*100:.1f}%")
                    
                    if flags:
                        st.markdown("### 🚩 Risk Indicators")
                        for flag_type, desc in flags:
                            st.markdown(f'<div class="fraud-flag">{flag_type}: {desc}</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if 'quarter' in prov_df.columns:
                            st.subheader("📈 Timeline")
                            qtr = prov_df['quarter'].value_counts().sort_index()
                            fig = px.line(x=qtr.index, y=qtr.values, markers=True)
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        if 'Location of Service' in prov_df.columns:
                            st.subheader("🗺️ Geographic Spread")
                            states = prov_df['Location of Service'].value_counts().head(10)
                            fig = px.bar(x=states.values, y=states.index, orientation='h')
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No data found for this provider")
    
    # TAB 8: FRAUD ALERTS
    with tabs[7]:
        st.header("🚩 Fraud Detection")
        
        st.markdown("""
        <div class="warning-box">
        <b>Auto-flagged providers</b> based on suspicious patterns in sample data
        </div>
        """, unsafe_allow_html=True)
        
        if 'Provider/Facility Name' in filtered_df.columns:
            top_providers = filtered_df['Provider/Facility Name'].value_counts().head(30)
            high_risk = []
            
            for provider in top_providers.index:
                prov_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                flags, risk = calculate_fraud_flags(prov_df, total_records)
                
                if risk >= 30:
                    high_risk.append({
                        'Provider': provider,
                        'Risk Score': risk,
                        'Disputes (Sample)': len(prov_df),
                        'Flags': len(flags),
                        'Issues': ' | '.join([f[0] for f in flags]) if flags else 'Volume-based'
                    })
            
            if high_risk:
                risk_df = pd.DataFrame(high_risk).sort_values('Risk Score', ascending=False)
                st.markdown(f"**⚠️ {len(risk_df)} FLAGGED PROVIDERS**")
                st.dataframe(risk_df, use_container_width=True, height=400)
                
                csv = risk_df.to_csv(index=False)
                st.download_button("📥 Download List", csv, "flagged_providers.csv", "text/csv")
            else:
                st.success("✅ No high-risk providers detected in sample")
    
    # TAB 9: COMPARE
    with tabs[8]:
        st.header("📊 Compare Providers")
        
        if 'Provider/Facility Name' in filtered_df.columns:
            top = filtered_df['Provider/Facility Name'].value_counts().head(30).index.tolist()
            selected = st.multiselect("Select providers to compare:", top, max_selections=5)
            
            if len(selected) >= 2:
                comp_data = []
                for provider in selected:
                    prov_df = filtered_df[filtered_df['Provider/Facility Name'] == provider]
                    
                    win_rate = 0
                    if 'Payment Determination Outcome' in prov_df.columns:
                        wins = (prov_df['Payment Determination Outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                        win_rate = wins / len(prov_df) * 100
                    
                    comp_data.append({
                        'Provider': provider[:30] + '...' if len(provider) > 30 else provider,
                        'Disputes': len(prov_df),
                        'Win Rate': win_rate
                    })
                
                comp_df = pd.DataFrame(comp_data)
                
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.bar(comp_df, x='Provider', y='Disputes', title="Dispute Volume",
                               color='Disputes', color_continuous_scale='Reds')
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.bar(comp_df, x='Provider', y='Win Rate', title="Win Rate (%)",
                               color='Win Rate', color_continuous_scale='Blues')
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Select at least 2 providers to compare")

if __name__ == "__main__":
    main()
