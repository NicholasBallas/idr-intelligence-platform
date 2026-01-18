import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

st.set_page_config(page_title="IDR Intelligence Platform", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1a5490; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #4a5568; margin-bottom: 2rem; }
    .alert-box { background-color: #fff5f5; border-left: 4px solid #fc8181; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
    .success-box { background-color: #f0fff4; border-left: 4px solid #48bb78; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
    .warning-box { background-color: #fffaf0; border-left: 4px solid #ed8936; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
    .info-box { background-color: #ebf8ff; border-left: 4px solid #4299e1; padding: 1rem; margin: 1rem 0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

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
    st.markdown('<p class="main-header">🔍 IDR Intelligence Platform</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Independent Dispute Resolution Data Analysis • 2023-2024</p>', unsafe_allow_html=True)
    
    overview = load_overview()
    providers_df = load_provider_summaries()
    states_df = load_state_summaries()
    specialties_df = load_specialty_summaries()
    payers_df = load_payer_summaries()
    quarterly_df = load_quarterly_summaries()
    
    if overview is None:
        st.error("Could not load data. Run generate_summaries.py locally first.")
        return
    
    with st.sidebar:
        st.markdown(f'<div class="success-box"><b>✅ Connected</b><br/>Records: {overview["total_disputes"]:,}<br/>Quarters: {overview["quarters_covered"]}</div>', unsafe_allow_html=True)
        st.markdown("---")
        search_query = st.text_input("🔍 Search provider:", placeholder="e.g., Singleton")
        if search_query:
            results = search_providers(search_query)
            if len(results) > 0:
                for _, row in results.head(5).iterrows():
                    st.write(f"• {row['provider_name'][:40]}...")
    
    tabs = st.tabs(["📊 Overview", "🏥 Providers", "📍 States", "🩺 Specialties", "🏢 Payers", "🔍 State Research", "🚩 Fraud Alerts"])
    
    with tabs[0]:
        st.header("Executive Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Disputes", f"{overview['total_disputes']:,}")
        c2.metric("Provider Win Rate", f"{overview['provider_win_rate']}%")
        c3.metric("Batch Rate", f"{overview['batch_rate']}%")
        c4.metric("IDRE Fees", f"${overview['total_idre_fees']:,.0f}")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if len(quarterly_df) > 0:
                fig = px.bar(quarterly_df, x='quarter', y='total_disputes', color='total_disputes', color_continuous_scale='Blues')
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            if len(states_df) > 0:
                fig = px.bar(states_df.head(10), x='total_disputes', y='state', orientation='h', color='total_disputes', color_continuous_scale='Reds')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:
        st.header("Provider Analysis")
        if len(providers_df) > 0:
            st.dataframe(providers_df[['provider_name','total_disputes','win_rate','batch_rate','states_count','top_specialty']], use_container_width=True, height=500)
            fig = px.bar(providers_df.head(15), x='total_disputes', y='provider_name', orientation='h', color='win_rate', color_continuous_scale='RdYlGn')
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
            st.plotly_chart(fig, use_container_width=True)
            st.download_button("📥 Download", providers_df.to_csv(index=False), "providers.csv")
    
    with tabs[2]:
        st.header("State Analysis")
        if len(states_df) > 0:
            fig = px.bar(states_df.head(20), x='state', y='total_disputes', color='win_rate', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(states_df, use_container_width=True)
            st.download_button("📥 Download", states_df.to_csv(index=False), "states.csv")
    
    with tabs[3]:
        st.header("Specialty Analysis")
        if len(specialties_df) > 0:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(specialties_df.head(10), values='total_disputes', names='specialty')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(specialties_df.head(15), x='win_rate', y='specialty', orientation='h', color='win_rate', color_continuous_scale='RdYlGn')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(specialties_df, use_container_width=True)
    
    with tabs[4]:
        st.header("Payer Analysis")
        if len(payers_df) > 0:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(payers_df.head(15), x='total_disputes', y='payer_name', orientation='h')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(payers_df.head(15), x='loss_rate', y='payer_name', orientation='h', color='loss_rate', color_continuous_scale='Reds')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(payers_df, use_container_width=True)
    
    with tabs[5]:
        st.header("🔍 State Research")
        st.markdown('<div class="info-box"><b>Deep Dive:</b> Select any state for detailed provider, specialty, payer, and trend breakdowns.</div>', unsafe_allow_html=True)
        if len(states_df) > 0:
            selected_state = st.selectbox("Select a state:", states_df['state'].tolist())
            state_info = states_df[states_df['state'] == selected_state].iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Disputes", f"{state_info['total_disputes']:,}")
            c2.metric("Win Rate", f"{state_info['win_rate']}%")
            c3.metric("% of National", f"{state_info['pct_of_total']}%")
            st.markdown("---")
            state_tabs = st.tabs(["🏥 Providers", "🩺 Specialties", "🏢 Payers", "📈 Trends"])
            with state_tabs[0]:
                sp = load_state_providers(selected_state)
                if len(sp) > 0:
                    fig = px.bar(sp.head(20), x='total_disputes', y='provider_name', orientation='h', color='win_rate', color_continuous_scale='RdYlGn')
                    fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=600)
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(sp, use_container_width=True)
                    st.download_button(f"📥 Download {selected_state} Providers", sp.to_csv(index=False), f"{selected_state}_providers.csv")
            with state_tabs[1]:
                ss = load_state_specialties(selected_state)
                if len(ss) > 0:
                    fig = px.pie(ss.head(10), values='total_disputes', names='specialty')
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(ss, use_container_width=True)
            with state_tabs[2]:
                spy = load_state_payers(selected_state)
                if len(spy) > 0:
                    fig = px.bar(spy.head(15), x='total_disputes', y='payer_name', orientation='h')
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(spy, use_container_width=True)
            with state_tabs[3]:
                sq = load_state_quarterly(selected_state)
                if len(sq) > 0:
                    fig = px.bar(sq, x='quarter', y='total_disputes', color='win_rate', color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(sq, use_container_width=True)
    
    with tabs[6]:
        st.header("🚩 Fraud Risk Indicators")
        if len(providers_df) > 0:
            flagged = []
            for _, row in providers_df.iterrows():
                flags, risk = [], 0
                if row['total_disputes'] > 10000: flags.append("EXTREME VOLUME"); risk += 30
                elif row['total_disputes'] > 1000: flags.append("HIGH VOLUME"); risk += 15
                if row['batch_rate'] > 90: flags.append("BATCH ABUSER"); risk += 20
                if row['states_count'] > 10: flags.append("MULTI-STATE"); risk += 15
                if row['win_rate'] > 95: flags.append("ABNORMAL WIN RATE"); risk += 10
                if risk >= 30:
                    flagged.append({'Provider': row['provider_name'], 'Disputes': row['total_disputes'], 'Win Rate': f"{row['win_rate']}%", 'Risk Score': risk, 'Flags': ' | '.join(flags)})
            if flagged:
                flagged_df = pd.DataFrame(flagged).sort_values('Risk Score', ascending=False)
                st.markdown(f"### ⚠️ {len(flagged_df)} High-Risk Providers")
                st.dataframe(flagged_df, use_container_width=True)
                st.download_button("📥 Download Flagged", flagged_df.to_csv(index=False), "flagged.csv")

if __name__ == "__main__":
    main()
