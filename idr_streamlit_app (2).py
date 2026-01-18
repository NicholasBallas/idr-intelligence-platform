import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import os

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
    .info-box { background-color: #ebf8ff; border-left: 4px solid #4299e1; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
    .fraud-flag { background-color: #fff5f5; border: 2px solid #fc8181; padding: 0.5rem 1rem; border-radius: 4px; display: inline-block; margin: 0.25rem; font-weight: 600; color: #c53030; }
    .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; }
    .stat-number { font-size: 2rem; font-weight: 700; }
    .stat-label { font-size: 0.9rem; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase_client():
    """Initialize Supabase client"""
    try:
        from supabase import create_client
        
        url = os.environ.get('SUPABASE_URL') or st.secrets.get("supabase", {}).get("url")
        key = os.environ.get('SUPABASE_KEY') or st.secrets.get("supabase", {}).get("key")
        
        if not url or not key:
            st.error("Supabase credentials not found.")
            return None
            
        return create_client(url, key)
    except Exception as e:
        st.error(f"Could not connect to Supabase: {e}")
        return None

# ===== LOAD SUMMARIES (INSTANT) =====

@st.cache_data(ttl=3600)
def load_overview():
    """Load overview summary"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    try:
        response = supabase.table('summary_overview').select('*').execute()
        return response.data[0] if response.data else None
    except:
        return None

@st.cache_data(ttl=3600)
def load_provider_summaries():
    """Load provider summaries"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table('summary_providers').select('*').order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_state_summaries():
    """Load state summaries"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table('summary_states').select('*').order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_specialty_summaries():
    """Load specialty summaries"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table('summary_specialties').select('*').order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_payer_summaries():
    """Load payer summaries"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table('summary_payers').select('*').order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_quarterly_summaries():
    """Load quarterly summaries"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    try:
        response = supabase.table('summary_quarterly').select('*').order('quarter').execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

# ===== ON-DEMAND QUERIES (FOR RESEARCH) =====

def query_by_provider(provider_name):
    """Query all records for a specific provider"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
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
    
    return pd.DataFrame(all_data)

def query_by_state(state):
    """Query all records for a specific state"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    all_data = []
    batch_size = 1000
    offset = 0
    
    while True:
        response = supabase.table('idr_disputes').select('*').eq('state', state).range(offset, offset + batch_size - 1).execute()
        
        if not response.data:
            break
        
        all_data.extend(response.data)
        offset += batch_size
        
        if len(response.data) < batch_size:
            break
    
    return pd.DataFrame(all_data)

def query_by_specialty(specialty):
    """Query all records for a specific specialty"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    all_data = []
    batch_size = 1000
    offset = 0
    
    while True:
        response = supabase.table('idr_disputes').select('*').eq('specialty', specialty).range(offset, offset + batch_size - 1).execute()
        
        if not response.data:
            break
        
        all_data.extend(response.data)
        offset += batch_size
        
        if len(response.data) < batch_size:
            break
    
    return pd.DataFrame(all_data)

def search_providers(search_term):
    """Search for providers by name"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table('summary_providers').select('*').ilike('provider_name', f'%{search_term}%').execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

# ===== MAIN APP =====

def main():
    st.markdown('<p class="main-header">🔍 IDR Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Independent Dispute Resolution Data Analysis • 2023-2024</p>', unsafe_allow_html=True)
    
    # Load summaries
    overview = load_overview()
    providers_df = load_provider_summaries()
    states_df = load_state_summaries()
    specialties_df = load_specialty_summaries()
    payers_df = load_payer_summaries()
    quarterly_df = load_quarterly_summaries()
    
    if overview is None:
        st.error("Could not load data. Make sure summary tables exist in Supabase.")
        st.info("Run `python generate_summaries.py` locally to create summary tables.")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="success-box">
        <b>✅ Database Connected</b><br/>
        Total Records: {overview['total_disputes']:,}<br/>
        Quarters: {overview['quarters_covered']}<br/>
        Last Updated: {overview['last_updated'][:10]}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔍 Quick Search")
        search_query = st.text_input("Search provider:", placeholder="e.g., Singleton")
        
        if search_query:
            results = search_providers(search_query)
            if len(results) > 0:
                st.write(f"Found {len(results)} matches")
                for _, row in results.head(5).iterrows():
                    if st.button(f"📋 {row['provider_name'][:30]}...", key=row['provider_name']):
                        st.session_state['investigate_provider'] = row['provider_name']
    
    # Main tabs
    tabs = st.tabs([
        "📊 Overview", 
        "🏥 Providers", 
        "📍 States",
        "🩺 Specialties", 
        "🏢 Payers",
        "🔍 Research",
        "🚩 Fraud Alerts"
    ])
    
    # ===== TAB 1: OVERVIEW =====
    with tabs[0]:
        st.header("Executive Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Disputes", f"{overview['total_disputes']:,}")
        with col2:
            st.metric("Provider Win Rate", f"{overview['provider_win_rate']}%")
        with col3:
            st.metric("Batch Filing Rate", f"{overview['batch_rate']}%")
        with col4:
            st.metric("Total IDRE Fees", f"${overview['total_idre_fees']:,.0f}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Quarterly Trends")
            if len(quarterly_df) > 0:
                fig = px.bar(quarterly_df, x='quarter', y='total_disputes',
                           labels={'quarter': 'Quarter', 'total_disputes': 'Disputes'},
                           color='total_disputes', color_continuous_scale='Blues')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🗺️ Top States")
            if len(states_df) > 0:
                top_states = states_df.head(10)
                fig = px.bar(top_states, x='total_disputes', y='state', orientation='h',
                           labels={'state': 'State', 'total_disputes': 'Disputes'},
                           color='total_disputes', color_continuous_scale='Reds')
                fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Key insight
        if len(states_df) > 0:
            tx_data = states_df[states_df['state'] == 'TX']
            if len(tx_data) > 0:
                tx_pct = tx_data.iloc[0]['pct_of_total']
                st.markdown(f"""
                <div class="alert-box">
                <b>🎯 Key Finding:</b> Texas accounts for <b>{tx_pct}%</b> of all IDR disputes nationally.
                </div>
                """, unsafe_allow_html=True)
    
    # ===== TAB 2: PROVIDERS =====
    with tabs[1]:
        st.header("Provider Analysis")
        st.caption("Top 100 providers by dispute volume")
        
        if len(providers_df) > 0:
            # Summary stats
            top_20_pct = providers_df.head(20)['pct_of_total'].sum()
            st.markdown(f"""
            <div class="warning-box">
            <b>⚠️ Market Concentration:</b> The top 20 providers account for <b>{top_20_pct:.1f}%</b> of all disputes.
            </div>
            """, unsafe_allow_html=True)
            
            # Table
            display_df = providers_df[['provider_name', 'total_disputes', 'win_rate', 'batch_rate', 'states_count', 'top_specialty']].copy()
            display_df.columns = ['Provider', 'Disputes', 'Win Rate %', 'Batch Rate %', 'States', 'Primary Specialty']
            st.dataframe(display_df, use_container_width=True, height=500)
            
            # Chart
            fig = px.bar(providers_df.head(15), x='total_disputes', y='provider_name', orientation='h',
                        labels={'provider_name': '', 'total_disputes': 'Total Disputes'},
                        color='win_rate', color_continuous_scale='RdYlGn',
                        hover_data=['win_rate', 'states_count'])
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Download
            csv = providers_df.to_csv(index=False)
            st.download_button("📥 Download Provider Data", csv, "idr_providers.csv", "text/csv")
    
    # ===== TAB 3: STATES =====
    with tabs[2]:
        st.header("State Analysis")
        
        if len(states_df) > 0:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Disputes by State")
                fig = px.bar(states_df.head(20), x='state', y='total_disputes',
                           color='win_rate', color_continuous_scale='RdYlGn',
                           labels={'state': 'State', 'total_disputes': 'Disputes', 'win_rate': 'Win Rate %'})
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Select State to Explore")
                selected_state = st.selectbox("Choose a state:", states_df['state'].tolist())
                
                if selected_state:
                    state_info = states_df[states_df['state'] == selected_state].iloc[0]
                    st.metric("Total Disputes", f"{state_info['total_disputes']:,}")
                    st.metric("Win Rate", f"{state_info['win_rate']}%")
                    st.metric("% of National", f"{state_info['pct_of_total']}%")
                    st.write(f"**Top Provider:** {state_info['top_provider'][:40]}...")
                    
                    if st.button(f"🔍 Deep Dive: {selected_state}", type="primary"):
                        st.session_state['research_state'] = selected_state
                        st.info("Go to Research tab to see full state data")
            
            # Full table
            st.subheader("All States")
            st.dataframe(states_df, use_container_width=True)
    
    # ===== TAB 4: SPECIALTIES =====
    with tabs[3]:
        st.header("Specialty Analysis")
        
        if len(specialties_df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Disputes by Specialty")
                fig = px.pie(specialties_df.head(10), values='total_disputes', names='specialty',
                           title='Top 10 Specialties')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Win Rates by Specialty")
                fig = px.bar(specialties_df.head(15), x='win_rate', y='specialty', orientation='h',
                           color='win_rate', color_continuous_scale='RdYlGn',
                           labels={'specialty': '', 'win_rate': 'Win Rate %'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(specialties_df, use_container_width=True)
    
    # ===== TAB 5: PAYERS =====
    with tabs[4]:
        st.header("Payer Analysis")
        st.caption("Health plans ranked by IDR dispute volume")
        
        if len(payers_df) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Disputes by Payer")
                fig = px.bar(payers_df.head(15), x='total_disputes', y='payer_name', orientation='h',
                           labels={'payer_name': '', 'total_disputes': 'Disputes'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Loss Rates")
                fig = px.bar(payers_df.head(15), x='loss_rate', y='payer_name', orientation='h',
                           color='loss_rate', color_continuous_scale='Reds',
                           labels={'payer_name': '', 'loss_rate': 'Loss Rate %'})
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(payers_df, use_container_width=True)
    
    # ===== TAB 6: RESEARCH =====
    with tabs[5]:
        st.header("🔍 Research Tools")
        st.markdown("""
        <div class="info-box">
        <b>Deep Dive Research:</b> Query the full database of 2.5M+ records by provider, state, or specialty.
        </div>
        """, unsafe_allow_html=True)
        
        research_type = st.radio("Research by:", ["Provider", "State", "Specialty"], horizontal=True)
        
        if research_type == "Provider":
            st.subheader("Provider Research")
            
            # Show top providers for selection
            if len(providers_df) > 0:
                provider_options = providers_df['provider_name'].tolist()
                selected_provider = st.selectbox("Select a provider:", [""] + provider_options)
                
                # Or search
                search = st.text_input("Or search by name:")
                if search:
                    matches = search_providers(search)
                    if len(matches) > 0:
                        selected_provider = st.selectbox("Search results:", matches['provider_name'].tolist())
                
                if selected_provider and st.button("🔍 Load Full Data", type="primary"):
                    with st.spinner(f"Loading all records for {selected_provider}..."):
                        data = query_by_provider(selected_provider)
                    
                    if len(data) > 0:
                        st.success(f"Loaded {len(data):,} records")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Disputes", f"{len(data):,}")
                        with col2:
                            if 'outcome' in data.columns:
                                wins = (data['outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                                st.metric("Win Rate", f"{wins/len(data)*100:.1f}%")
                        with col3:
                            if 'state' in data.columns:
                                st.metric("States", data['state'].nunique())
                        
                        # Show quarterly trend
                        if 'quarter' in data.columns:
                            quarterly = data['quarter'].value_counts().sort_index()
                            fig = px.line(x=quarterly.index, y=quarterly.values, markers=True,
                                        labels={'x': 'Quarter', 'y': 'Disputes'})
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.dataframe(data.head(1000), use_container_width=True)
                        
                        csv = data.to_csv(index=False)
                        st.download_button("📥 Download Full Data", csv, f"{selected_provider[:20]}_data.csv", "text/csv")
        
        elif research_type == "State":
            st.subheader("State Research")
            
            if len(states_df) > 0:
                selected_state = st.selectbox("Select a state:", states_df['state'].tolist())
                
                if selected_state and st.button("🔍 Load Full State Data", type="primary"):
                    with st.spinner(f"Loading all records for {selected_state}..."):
                        data = query_by_state(selected_state)
                    
                    if len(data) > 0:
                        st.success(f"Loaded {len(data):,} records for {selected_state}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Disputes", f"{len(data):,}")
                        with col2:
                            if 'outcome' in data.columns:
                                wins = (data['outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                                st.metric("Win Rate", f"{wins/len(data)*100:.1f}%")
                        with col3:
                            if 'provider_name' in data.columns:
                                st.metric("Unique Providers", data['provider_name'].nunique())
                        
                        # Top providers in state
                        if 'provider_name' in data.columns:
                            st.subheader(f"Top Providers in {selected_state}")
                            top_in_state = data['provider_name'].value_counts().head(20)
                            fig = px.bar(x=top_in_state.values, y=top_in_state.index, orientation='h')
                            fig.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig, use_container_width=True)
                        
                        csv = data.to_csv(index=False)
                        st.download_button("📥 Download State Data", csv, f"{selected_state}_data.csv", "text/csv")
        
        elif research_type == "Specialty":
            st.subheader("Specialty Research")
            
            if len(specialties_df) > 0:
                selected_specialty = st.selectbox("Select a specialty:", specialties_df['specialty'].tolist())
                
                if selected_specialty and st.button("🔍 Load Full Specialty Data", type="primary"):
                    with st.spinner(f"Loading all records for {selected_specialty}..."):
                        data = query_by_specialty(selected_specialty)
                    
                    if len(data) > 0:
                        st.success(f"Loaded {len(data):,} records")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Disputes", f"{len(data):,}")
                        with col2:
                            if 'outcome' in data.columns:
                                wins = (data['outcome'] == 'In Favor of Provider/Facility/AA Provider').sum()
                                st.metric("Win Rate", f"{wins/len(data)*100:.1f}%")
                        
                        csv = data.to_csv(index=False)
                        st.download_button("📥 Download Specialty Data", csv, f"specialty_data.csv", "text/csv")
    
    # ===== TAB 7: FRAUD ALERTS =====
    with tabs[6]:
        st.header("🚩 Fraud Risk Indicators")
        
        st.markdown("""
        <div class="warning-box">
        <b>Automated Risk Detection:</b> Providers flagged based on suspicious patterns.
        </div>
        """, unsafe_allow_html=True)
        
        if len(providers_df) > 0:
            # Flag high-risk providers
            flagged = []
            
            for _, row in providers_df.iterrows():
                flags = []
                risk_score = 0
                
                # High volume
                if row['total_disputes'] > 10000:
                    flags.append("🚩 EXTREME VOLUME")
                    risk_score += 30
                elif row['total_disputes'] > 1000:
                    flags.append("🚩 HIGH VOLUME")
                    risk_score += 15
                
                # High batch rate
                if row['batch_rate'] > 90:
                    flags.append("🚩 BATCH ABUSER")
                    risk_score += 20
                
                # Multi-state
                if row['states_count'] > 10:
                    flags.append("🚩 MULTI-STATE")
                    risk_score += 15
                
                # Very high win rate
                if row['win_rate'] > 95:
                    flags.append("🚩 ABNORMAL WIN RATE")
                    risk_score += 10
                
                if risk_score >= 30:
                    flagged.append({
                        'Provider': row['provider_name'],
                        'Disputes': row['total_disputes'],
                        'Win Rate': f"{row['win_rate']}%",
                        'Batch Rate': f"{row['batch_rate']}%",
                        'States': row['states_count'],
                        'Risk Score': risk_score,
                        'Flags': ' | '.join(flags)
                    })
            
            if flagged:
                flagged_df = pd.DataFrame(flagged).sort_values('Risk Score', ascending=False)
                
                st.markdown(f"### ⚠️ {len(flagged_df)} High-Risk Providers Identified")
                st.dataframe(flagged_df, use_container_width=True, height=500)
                
                csv = flagged_df.to_csv(index=False)
                st.download_button("📥 Download Flagged Providers", csv, "flagged_providers.csv", "text/csv")
            else:
                st.success("No high-risk providers detected")

if __name__ == "__main__":
    main()
