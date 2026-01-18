import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

st.set_page_config(page_title="IDR Intelligence Platform", page_icon="◉", layout="wide", initial_sidebar_state="expanded")

# Palantir-inspired dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background-color: #0a0a0f;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 0.25rem;
        border-left: 3px solid #3b82f6;
        padding-left: 1rem;
    }
    
    .sub-header {
        font-size: 0.9rem;
        color: #6b7280;
        margin-bottom: 2rem;
        padding-left: 1.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stSidebar {
        background-color: #0f0f14 !important;
        border-right: 1px solid #1f2937;
    }
    
    .stSidebar [data-testid="stSidebarContent"] {
        background-color: #0f0f14;
    }
    
    .status-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #1e3a5f;
        padding: 1.25rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    
    .status-card .label {
        color: #64748b;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .status-card .value {
        color: #22d3ee;
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    .status-online {
        color: #22c55e;
        font-weight: 600;
    }
    
    .alert-critical {
        background-color: rgba(220, 38, 38, 0.1);
        border: 1px solid #991b1b;
        border-left: 3px solid #dc2626;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 2px;
        color: #fca5a5;
    }
    
    .alert-warning {
        background-color: rgba(245, 158, 11, 0.1);
        border: 1px solid #92400e;
        border-left: 3px solid #f59e0b;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 2px;
        color: #fcd34d;
    }
    
    .alert-info {
        background-color: rgba(59, 130, 246, 0.1);
        border: 1px solid #1e40af;
        border-left: 3px solid #3b82f6;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 2px;
        color: #93c5fd;
    }
    
    .metric-container {
        background: #0f172a;
        border: 1px solid #1e3a5f;
        padding: 1.5rem;
        border-radius: 4px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 600;
        color: #ffffff;
        font-family: 'Inter', monospace;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }
    
    h1, h2, h3 {
        color: #f1f5f9 !important;
        font-weight: 500 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0f0f14;
        border-bottom: 1px solid #1f2937;
        gap: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #6b7280;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 1rem 1.5rem;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #e0e0e0;
        background-color: rgba(59, 130, 246, 0.1);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: #3b82f6 !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
    
    .stDataFrame {
        background-color: #0f172a;
        border: 1px solid #1e3a5f;
    }
    
    .stDataFrame [data-testid="stDataFrameResizable"] {
        background-color: #0a0a0f;
    }
    
    .stSelectbox > div > div {
        background-color: #1e293b;
        border: 1px solid #374151;
        color: #e0e0e0;
    }
    
    .stTextInput > div > div > input {
        background-color: #1e293b;
        border: 1px solid #374151;
        color: #e0e0e0;
    }
    
    .stButton > button {
        background-color: #1e40af;
        color: #ffffff;
        border: none;
        border-radius: 2px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #2563eb;
        border: none;
    }
    
    .stDownloadButton > button {
        background-color: transparent;
        color: #3b82f6;
        border: 1px solid #1e40af;
        border-radius: 2px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.75rem;
    }
    
    .stMetric {
        background-color: #0f172a;
        border: 1px solid #1e3a5f;
        padding: 1rem;
        border-radius: 4px;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: #22d3ee;
        font-family: 'Inter', monospace;
    }
    
    .stMetric [data-testid="stMetricLabel"] {
        color: #64748b;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 1px;
    }
    
    [data-testid="stHeader"] {
        background-color: #0a0a0f;
    }
    
    .section-header {
        color: #94a3b8;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1f2937;
    }
</style>
""", unsafe_allow_html=True)

# Dark theme for Plotly charts
CHART_TEMPLATE = {
    'layout': {
        'paper_bgcolor': '#0a0a0f',
        'plot_bgcolor': '#0f172a',
        'font': {'color': '#94a3b8', 'family': 'Inter'},
        'title': {'font': {'color': '#f1f5f9'}},
        'xaxis': {
            'gridcolor': '#1e3a5f',
            'linecolor': '#1e3a5f',
            'tickfont': {'color': '#64748b'}
        },
        'yaxis': {
            'gridcolor': '#1e3a5f',
            'linecolor': '#1e3a5f',
            'tickfont': {'color': '#64748b'}
        },
        'colorway': ['#3b82f6', '#22d3ee', '#14b8a6', '#f59e0b', '#ef4444'],
        'margin': {'t': 40, 'b': 40, 'l': 40, 'r': 40}
    }
}

def style_chart(fig):
    fig.update_layout(
        paper_bgcolor='#0a0a0f',
        plot_bgcolor='#0f172a',
        font=dict(color='#94a3b8', family='Inter'),
        xaxis=dict(gridcolor='#1e3a5f', linecolor='#1e3a5f', tickfont=dict(color='#64748b')),
        yaxis=dict(gridcolor='#1e3a5f', linecolor='#1e3a5f', tickfont=dict(color='#64748b')),
        margin=dict(t=40, b=40, l=40, r=40),
        showlegend=False
    )
    return fig

@st.cache_resource
def get_supabase_client():
    try:
        from supabase import create_client
        url = os.environ.get('SUPABASE_URL') or st.secrets.get("supabase", {}).get("url")
        key = os.environ.get('SUPABASE_KEY') or st.secrets.get("supabase", {}).get("key")
        if not url or not key:
            return None
        return create_client(url, key)
    except:
        return None

@st.cache_data(ttl=3600)
def load_overview():
    supabase = get_supabase_client()
    if not supabase: return None
    try:
        response = supabase.table('summary_overview').select('*').execute()
        return response.data[0] if response.data else None
    except: return None

@st.cache_data(ttl=3600)
def load_provider_summaries():
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('summary_providers').select('*').order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_state_summaries():
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('summary_states').select('*').order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_specialty_summaries():
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('summary_specialties').select('*').order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_payer_summaries():
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('summary_payers').select('*').order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_quarterly_summaries():
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('summary_quarterly').select('*').order('quarter').execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_state_providers(state):
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('state_providers').select('*').eq('state', state).order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_state_specialties(state):
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('state_specialties').select('*').eq('state', state).order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_state_payers(state):
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('state_payers').select('*').eq('state', state).order('total_disputes', desc=True).execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_state_quarterly(state):
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('state_quarterly').select('*').eq('state', state).order('quarter').execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

def search_providers(search_term):
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table('summary_providers').select('*').ilike('provider_name', f'%{search_term}%').execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

def main():
    st.markdown('<p class="main-header">IDR INTELLIGENCE PLATFORM</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Independent Dispute Resolution Analysis System | 2023-2024 Data</p>', unsafe_allow_html=True)
    
    overview = load_overview()
    providers_df = load_provider_summaries()
    states_df = load_state_summaries()
    specialties_df = load_specialty_summaries()
    payers_df = load_payer_summaries()
    quarterly_df = load_quarterly_summaries()
    
    if overview is None:
        st.error("DATABASE CONNECTION FAILED. Run generate_summaries.py locally.")
        return
    
    with st.sidebar:
        st.markdown('<p class="section-header">System Status</p>', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="status-card">
            <div class="label">Connection</div>
            <div class="value status-online">● ONLINE</div>
        </div>
        <div class="status-card">
            <div class="label">Total Records</div>
            <div class="value">{overview["total_disputes"]:,}</div>
        </div>
        <div class="status-card">
            <div class="label">Data Coverage</div>
            <div class="value">{overview["quarters_covered"]} Quarters</div>
        </div>
        <div class="status-card">
            <div class="label">Last Sync</div>
            <div class="value">{overview["last_updated"][:10]}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('<p class="section-header">Search</p>', unsafe_allow_html=True)
        search_query = st.text_input("Provider lookup:", placeholder="Enter provider name...", label_visibility="collapsed")
        if search_query:
            results = search_providers(search_query)
            if len(results) > 0:
                st.markdown(f'<span style="color:#64748b;font-size:0.8rem;">{len(results)} results found</span>', unsafe_allow_html=True)
                for _, row in results.head(5).iterrows():
                    st.markdown(f'<span style="color:#94a3b8;font-size:0.85rem;">› {row["provider_name"][:35]}...</span>', unsafe_allow_html=True)
    
    tabs = st.tabs(["OVERVIEW", "PROVIDERS", "STATES", "SPECIALTIES", "PAYERS", "STATE INTEL", "RISK FLAGS"])
    
    with tabs[0]:
        st.markdown('<p class="section-header">Executive Summary</p>', unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Disputes", f"{overview['total_disputes']:,}")
        c2.metric("Provider Win Rate", f"{overview['provider_win_rate']}%")
        c3.metric("Batch Filing Rate", f"{overview['batch_rate']}%")
        c4.metric("Total IDRE Fees", f"${overview['total_idre_fees']:,.0f}")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<p class="section-header">Quarterly Volume</p>', unsafe_allow_html=True)
            if len(quarterly_df) > 0:
                fig = px.bar(quarterly_df, x='quarter', y='total_disputes')
                fig.update_traces(marker_color='#3b82f6')
                fig = style_chart(fig)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<p class="section-header">Geographic Distribution</p>', unsafe_allow_html=True)
            if len(states_df) > 0:
                fig = px.bar(states_df.head(10), x='total_disputes', y='state', orientation='h')
                fig.update_traces(marker_color='#22d3ee')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                fig = style_chart(fig)
                st.plotly_chart(fig, use_container_width=True)
        
        if len(states_df) > 0:
            tx_data = states_df[states_df['state'] == 'TX']
            if len(tx_data) > 0:
                tx_pct = tx_data.iloc[0]['pct_of_total']
                st.markdown(f'<div class="alert-critical"><strong>CRITICAL FINDING:</strong> Texas accounts for {tx_pct}% of all national IDR disputes. Concentration indicates potential systemic exploitation.</div>', unsafe_allow_html=True)
    
    with tabs[1]:
        st.markdown('<p class="section-header">Provider Analysis</p>', unsafe_allow_html=True)
        if len(providers_df) > 0:
            top_20_pct = providers_df.head(20)['pct_of_total'].sum()
            st.markdown(f'<div class="alert-warning"><strong>MARKET CONCENTRATION:</strong> Top 20 providers control {top_20_pct:.1f}% of all dispute volume.</div>', unsafe_allow_html=True)
            
            st.dataframe(
                providers_df[['provider_name','total_disputes','win_rate','batch_rate','states_count','top_specialty']].rename(
                    columns={'provider_name':'PROVIDER','total_disputes':'DISPUTES','win_rate':'WIN %','batch_rate':'BATCH %','states_count':'STATES','top_specialty':'SPECIALTY'}
                ), 
                use_container_width=True, 
                height=400
            )
            
            fig = px.bar(providers_df.head(15), x='total_disputes', y='provider_name', orientation='h')
            fig.update_traces(marker_color='#3b82f6')
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
            fig = style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)
            
            st.download_button("EXPORT DATA", providers_df.to_csv(index=False), "providers_export.csv")
    
    with tabs[2]:
        st.markdown('<p class="section-header">State Analysis</p>', unsafe_allow_html=True)
        if len(states_df) > 0:
            fig = px.bar(states_df.head(20), x='state', y='total_disputes')
            fig.update_traces(marker_color='#14b8a6')
            fig = style_chart(fig)
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(
                states_df.rename(columns={'state':'STATE','total_disputes':'DISPUTES','win_rate':'WIN %','pct_of_total':'% NATIONAL','top_provider':'TOP PROVIDER'}),
                use_container_width=True
            )
            st.download_button("EXPORT DATA", states_df.to_csv(index=False), "states_export.csv")
    
    with tabs[3]:
        st.markdown('<p class="section-header">Specialty Analysis</p>', unsafe_allow_html=True)
        if len(specialties_df) > 0:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(specialties_df.head(10), values='total_disputes', names='specialty', hole=0.4)
                fig.update_traces(marker=dict(colors=['#3b82f6','#22d3ee','#14b8a6','#f59e0b','#ef4444','#8b5cf6','#ec4899','#06b6d4','#84cc16','#f97316']))
                fig = style_chart(fig)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(specialties_df.head(15), x='win_rate', y='specialty', orientation='h')
                fig.update_traces(marker_color='#22d3ee')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                fig = style_chart(fig)
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(specialties_df, use_container_width=True)
    
    with tabs[4]:
        st.markdown('<p class="section-header">Payer Analysis</p>', unsafe_allow_html=True)
        if len(payers_df) > 0:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(payers_df.head(15), x='total_disputes', y='payer_name', orientation='h')
                fig.update_traces(marker_color='#3b82f6')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                fig = style_chart(fig)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(payers_df.head(15), x='loss_rate', y='payer_name', orientation='h')
                fig.update_traces(marker_color='#ef4444')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                fig = style_chart(fig)
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(payers_df, use_container_width=True)
    
    with tabs[5]:
        st.markdown('<p class="section-header">State Intelligence</p>', unsafe_allow_html=True)
        st.markdown('<div class="alert-info">Select a state jurisdiction to analyze provider activity, specialty distribution, payer exposure, and temporal patterns.</div>', unsafe_allow_html=True)
        
        if len(states_df) > 0:
            selected_state = st.selectbox("TARGET STATE:", states_df['state'].tolist(), label_visibility="visible")
            state_info = states_df[states_df['state'] == selected_state].iloc[0]
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Disputes", f"{state_info['total_disputes']:,}")
            c2.metric("Win Rate", f"{state_info['win_rate']}%")
            c3.metric("National Share", f"{state_info['pct_of_total']}%")
            
            st.markdown("---")
            state_tabs = st.tabs(["PROVIDERS", "SPECIALTIES", "PAYERS", "TRENDS"])
            
            with state_tabs[0]:
                sp = load_state_providers(selected_state)
                if len(sp) > 0:
                    fig = px.bar(sp.head(20), x='total_disputes', y='provider_name', orientation='h')
                    fig.update_traces(marker_color='#3b82f6')
                    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
                    fig = style_chart(fig)
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(sp, use_container_width=True)
                    st.download_button(f"EXPORT {selected_state} PROVIDERS", sp.to_csv(index=False), f"{selected_state}_providers.csv")
            
            with state_tabs[1]:
                ss = load_state_specialties(selected_state)
                if len(ss) > 0:
                    fig = px.pie(ss.head(10), values='total_disputes', names='specialty', hole=0.4)
                    fig = style_chart(fig)
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(ss, use_container_width=True)
            
            with state_tabs[2]:
                spy = load_state_payers(selected_state)
                if len(spy) > 0:
                    fig = px.bar(spy.head(15), x='total_disputes', y='payer_name', orientation='h')
                    fig.update_traces(marker_color='#22d3ee')
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    fig = style_chart(fig)
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(spy, use_container_width=True)
            
            with state_tabs[3]:
                sq = load_state_quarterly(selected_state)
                if len(sq) > 0:
                    fig = px.bar(sq, x='quarter', y='total_disputes')
                    fig.update_traces(marker_color='#14b8a6')
                    fig = style_chart(fig)
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(sq, use_container_width=True)
    
    with tabs[6]:
        st.markdown('<p class="section-header">Risk Identification</p>', unsafe_allow_html=True)
        st.markdown('<div class="alert-critical"><strong>AUTOMATED THREAT DETECTION:</strong> Entities flagged based on anomalous filing patterns, volume concentration, and behavioral indicators.</div>', unsafe_allow_html=True)
        
        if len(providers_df) > 0:
            flagged = []
            for _, row in providers_df.iterrows():
                flags, risk = [], 0
                if row['total_disputes'] > 10000: 
                    flags.append("EXTREME VOLUME")
                    risk += 30
                elif row['total_disputes'] > 1000: 
                    flags.append("HIGH VOLUME")
                    risk += 15
                if row['batch_rate'] > 90: 
                    flags.append("BATCH EXPLOITATION")
                    risk += 20
                if row['states_count'] > 10: 
                    flags.append("MULTI-JURISDICTION")
                    risk += 15
                if row['win_rate'] > 95: 
                    flags.append("ANOMALOUS WIN RATE")
                    risk += 10
                if risk >= 30:
                    flagged.append({
                        'ENTITY': row['provider_name'],
                        'DISPUTES': row['total_disputes'],
                        'WIN RATE': f"{row['win_rate']}%",
                        'THREAT LEVEL': risk,
                        'INDICATORS': ' | '.join(flags)
                    })
            
            if flagged:
                flagged_df = pd.DataFrame(flagged).sort_values('THREAT LEVEL', ascending=False)
                st.markdown(f"### {len(flagged_df)} HIGH-RISK ENTITIES IDENTIFIED")
                st.dataframe(flagged_df, use_container_width=True, height=500)
                st.download_button("EXPORT FLAGGED ENTITIES", flagged_df.to_csv(index=False), "risk_flags.csv")

if __name__ == "__main__":
    main()
