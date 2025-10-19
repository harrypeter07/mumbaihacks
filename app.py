import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Agentic Health Context Guard",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .alert-high {
        background-color: #ff4b4b;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background-color: #ffa500;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🏥 Agentic Health Context Guard</div>', unsafe_allow_html=True)
st.markdown("**Real-time Healthcare Misinformation Tracking & Context Restoration**")

# Real-time simulation toggle
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("")
with col2:
    auto_refresh = st.checkbox("🔄 Live Updates", value=False)
with col3:
    if auto_refresh:
        st.markdown("🟢 **LIVE**")
        # Auto-refresh every 30 seconds
        st.rerun()
    else:
        st.markdown("⏸️ **PAUSED**")

st.divider()

# Load data
@st.cache_data
def load_data():
    try:
        posts_df = pd.read_csv('data/sample_posts.csv')
        edges_df = pd.read_csv('data/network_edges.csv')
        return posts_df, edges_df
    except FileNotFoundError:
        st.error("❌ Data files not found! Please ensure 'sample_posts.csv' and 'network_edges.csv' are in the 'data/' folder.")
        st.stop()

posts_df, edges_df = load_data()

# Convert timestamp to datetime
posts_df['timestamp'] = pd.to_datetime(posts_df['timestamp'])

# Sidebar filters
st.sidebar.header("🔍 Filters")
st.sidebar.markdown("---")

selected_platform = st.sidebar.multiselect(
    "Platform",
    options=posts_df['platform'].unique(),
    default=posts_df['platform'].unique()
)

selected_category = st.sidebar.multiselect(
    "Category",
    options=posts_df['category'].unique(),
    default=posts_df['category'].unique()
)

min_score = st.sidebar.slider("Minimum Misinfo Score", 0, 100, 70)

# Apply filters
filtered_posts = posts_df[
    (posts_df['platform'].isin(selected_platform)) &
    (posts_df['category'].isin(selected_category)) &
    (posts_df['misinfo_score'] >= min_score)
]

# Main metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Posts Tracked", len(filtered_posts), delta=f"+{len(filtered_posts) - len(posts_df) + 15}")
    
with col2:
    high_risk = len(filtered_posts[filtered_posts['misinfo_score'] > 85])
    st.metric("High Risk Posts", high_risk, delta="+5", delta_color="inverse")
    
with col3:
    archived_count = filtered_posts['archived'].sum()
    st.metric("Archived Posts", archived_count, delta="+3")
    
with col4:
    unique_users = filtered_posts['user_id'].nunique()
    st.metric("Active Spreaders", unique_users, delta="+2", delta_color="inverse")

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
    "🕸️ Network Graph", 
    "📋 Post Details", 
    "🚨 Alerts",
    "📈 Analytics"
])

with tab1:
    st.subheader("📊 Overview Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Platform distribution
        st.markdown("#### Posts by Platform")
        platform_counts = filtered_posts['platform'].value_counts()
        fig_platform = px.pie(
            values=platform_counts.values, 
            names=platform_counts.index,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_platform.update_layout(height=350)
        st.plotly_chart(fig_platform, width='stretch', config={'displayModeBar': False})
    
    with col2:
        # Category distribution
        st.markdown("#### Posts by Category")
        category_counts = filtered_posts['category'].value_counts()
        fig_category = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            labels={'x': 'Category', 'y': 'Count'},
            color=category_counts.values,
            color_continuous_scale='Reds'
        )
        fig_category.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_category, width='stretch', config={'displayModeBar': False})
    
    # Timeline
    st.markdown("#### Misinformation Timeline")
    timeline_data = filtered_posts.groupby(filtered_posts['timestamp'].dt.date).size().reset_index()
    timeline_data.columns = ['Date', 'Posts']
    
    fig_timeline = px.line(
        timeline_data, 
        x='Date', 
        y='Posts',
        markers=True,
        line_shape='spline'
    )
    fig_timeline.update_traces(line_color='#ff4b4b', marker=dict(size=8))
    fig_timeline.update_layout(height=300, hovermode='x unified')
    st.plotly_chart(fig_timeline, width='stretch', config={'displayModeBar': False})
    
    # Risk score distribution
    st.markdown("#### Risk Score Distribution")
    fig_hist = px.histogram(
        filtered_posts, 
        x='misinfo_score',
        nbins=15,
        color_discrete_sequence=['#ff6b6b']
    )
    fig_hist.update_layout(
        xaxis_title="Misinformation Score",
        yaxis_title="Number of Posts",
        height=300
    )
    st.plotly_chart(fig_hist, width='stretch', config={'displayModeBar': False})

with tab2:
    st.subheader("🕸️ Misinformation Spread Network")
    st.info("📍 Larger nodes = Super spreaders | Thicker lines = More shared content")
    
    # Create network graph
    G = nx.from_pandas_edgelist(edges_df, 'source', 'target', edge_attr='weight')
    
    # Calculate node metrics
    degree_centrality = nx.degree_centrality(G)
    
    # Improved layout with better spacing and multiple algorithms
    st.markdown("#### 🎛️ Network Controls")
    layout_type = st.selectbox("Layout Algorithm", ["Spring (Recommended)", "Circular", "Random", "Kamada-Kawai"], key="layout_select")
    
    if layout_type == "Spring (Recommended)":
        pos = nx.spring_layout(G, k=3.0, iterations=100, seed=42)  # Increased k for better spacing
    elif layout_type == "Circular":
        pos = nx.circular_layout(G)
    elif layout_type == "Random":
        pos = nx.random_layout(G, seed=42)
    else:  # Kamada-Kawai
        pos = nx.kamada_kawai_layout(G)
    
    # Filter for better visualization
    min_connections = st.slider("Minimum Connections to Show", 1, 10, 2, key="min_conn")
    filtered_nodes = [node for node in G.nodes() if G.degree(node) >= min_connections]
    G_filtered = G.subgraph(filtered_nodes)
    pos_filtered = {node: pos[node] for node in filtered_nodes if node in pos}
    
    # Edge trace with variable thickness (using filtered graph)
    edge_traces = []
    if G_filtered.edges():
        max_weight = max([edge[2]['weight'] for edge in G_filtered.edges(data=True)])
        
        for edge in G_filtered.edges(data=True):
            if edge[0] in pos_filtered and edge[1] in pos_filtered:
                x0, y0 = pos_filtered[edge[0]]
                x1, y1 = pos_filtered[edge[1]]
                weight = edge[2]['weight']
                
                # Calculate line width based on weight (1-6px range for cleaner look)
                line_width = max(0.5, min(6, weight / max_weight * 6))
                
                # Use opacity to reduce visual clutter
                opacity = max(0.3, min(0.8, weight / max_weight))
                
                edge_trace = go.Scatter(
                    x=[x0, x1, None], 
                    y=[y0, y1, None],
                    line=dict(width=line_width, color=f'rgba(136, 136, 136, {opacity})'),
                    hoverinfo='none',
                    mode='lines',
                    showlegend=False
                )
                edge_traces.append(edge_trace)
    
    # Node trace (using filtered graph)
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    node_labels = []
    
    for node in G_filtered.nodes():
        if node in pos_filtered:
            x, y = pos_filtered[node]
            node_x.append(x)
            node_y.append(y)
            degree = G_filtered.degree(node)
            centrality = degree_centrality[node]
            node_text.append(f"<b>{node}</b><br>Connections: {degree}<br>Centrality: {centrality:.3f}")
            # Improved node sizing - less aggressive scaling
            node_size.append(max(15, min(50, degree * 3 + 20)))
            node_color.append(degree)
            node_labels.append(node.replace('user_', 'U'))
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=node_text,
        text=node_labels,
        textposition="middle center",
        textfont=dict(size=8, color='white', family="Arial Black"),
        marker=dict(
            showscale=True,
            colorscale='YlOrRd',
            size=node_size,
            color=node_color,
            colorbar=dict(
                thickness=15,
                title=dict(
                    text='Connections',
                    side='right'
                ),
                xanchor='left'
            ),
            line=dict(width=2, color='white')
        )
    )
    
    # Create figure
    fig_network = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=550,
            plot_bgcolor='#f8f9fa'
        )
    )
    
    st.plotly_chart(fig_network, width='stretch', config={'displayModeBar': False})
    
    # Super spreaders table
    st.markdown("#### 🔴 Top Super Spreaders")
    
    spreader_data = pd.DataFrame({
        'User ID': list(G.nodes()),
        'Connections': [G.degree(node) for node in G.nodes()],
        'Centrality': [f"{degree_centrality[node]:.3f}" for node in G.nodes()],
        'Risk Level': ['🔴 High' if G.degree(node) > 3 else '🟡 Medium' if G.degree(node) > 1 else '🟢 Low' for node in G.nodes()]
    }).sort_values('Connections', ascending=False).head(10)
    
    st.dataframe(spreader_data, width='stretch', hide_index=True)

with tab3:
    st.subheader("📋 Misinformation Posts Database")
    
    # Search
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search posts", placeholder="Enter keywords...")
    with col2:
        sort_by = st.selectbox("Sort by", ["Timestamp", "Misinfo Score", "Shares"])
    
    # Apply search
    if search_term:
        display_posts = filtered_posts[
            filtered_posts['content'].str.contains(search_term, case=False, na=False)
        ]
    else:
        display_posts = filtered_posts
    
    # Sort
    if sort_by == "Timestamp":
        display_posts = display_posts.sort_values('timestamp', ascending=False)
    elif sort_by == "Misinfo Score":
        display_posts = display_posts.sort_values('misinfo_score', ascending=False)
    else:
        display_posts = display_posts.sort_values('shares', ascending=False)
    
    st.markdown(f"**Showing {len(display_posts)} posts**")
    st.markdown("---")
    
    # Display posts
    for idx, row in display_posts.head(20).iterrows():
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                st.markdown(f"**{row['post_id']}** | {row['platform']} | {row['username']}")
                st.write(f"📝 {row['content']}")
                st.caption(f"🕒 {row['timestamp'].strftime('%Y-%m-%d %H:%M')} | 🏷️ {row['category']}")
            
            with col2:
                score_color = "🔴" if row['misinfo_score'] > 85 else "🟠" if row['misinfo_score'] > 70 else "🟡"
                st.markdown(f"{score_color} **Risk: {row['misinfo_score']}**")
                st.caption(f"👥 {row['shares']} shares")
                st.caption(f"❤️ {row['likes']} likes")
            
            with col3:
                st.markdown(f"**{row['status']}**")
                if row['archived'] and pd.notna(row['archive_url']) and row['archive_url']:
                    st.success("✅ Archived")
                    st.markdown(f"[🔗 View Archive]({row['archive_url']})")
                else:
                    st.warning("⏳ Pending")
                    if st.button(f"Archive {row['post_id']}", key=f"archive_{row['post_id']}"):
                        st.info("📦 Queued for archival...")
            
            st.divider()

with tab4:
    st.subheader("🚨 Active Threat Alerts")
    
    # Live activity feed
    if auto_refresh:
        st.info("🔄 **Live Activity Feed** - Updates every 30 seconds")
        
        # Simulate live activity
        import random
        activities = [
            "New post flagged: 'COVID vaccine causes autism' - 1,200 shares",
            "Super spreader user_15 detected sharing false treatment claims",
            "Archive completed: POST_0045 preserved successfully",
            "Hospital alert sent: Regional Medical Center - High risk detected",
            "Fact-check completed: 'Vitamin D cures COVID' - DEBUNKED",
            "Network analysis: 3 new connections identified in spread chain"
        ]
        
        recent_activity = random.sample(activities, 3)
        for activity in recent_activity:
            st.markdown(f"🟢 {activity}")
    
    # Critical alerts
    st.markdown('<div class="alert-high"><b>🔴 CRITICAL</b>: Viral post claiming "vaccines contain microchips" reached 50K+ shares across platforms</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="alert-high"><b>🔴 CRITICAL</b>: Super spreader "user_1" sharing false treatment claims - 8 direct connections</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="alert-medium"><b>🟠 HIGH</b>: Misinformation about COVID cure trending on Reddit - 3,500 shares in 6 hours</div>', unsafe_allow_html=True)
    
    st.info("🔵 MEDIUM: Unverified health claim about natural immunity spreading on Instagram")
    
    st.divider()
    
    # Hospital alert dashboard
    st.subheader("🏥 Hospital Preparedness Dashboard")
    
    alert_data = pd.DataFrame({
        'Hospital': ['City General Hospital', 'Regional Medical Center', 'Metro Community Hospital', 'University Hospital', 'Children\'s Hospital', 'Emergency Care Center'],
        'Alert Level': ['🔴 Critical', '🟠 High', '🟡 Medium', '🟢 Low', '🟡 Medium', '🟠 High'],
        'Affected Posts': [18, 12, 5, 2, 7, 9],
        'Primary Threat': ['Fake cure claims', 'Vaccine misinformation', 'Treatment myths', 'Prevention myths', 'Child health myths', 'Emergency care myths'],
        'Estimated Impact': ['High ER surge expected', 'Moderate patient concerns', 'Low impact', 'Minimal impact', 'Pediatric concerns', 'Emergency protocol confusion'],
        'Recommended Action': [
            'Issue public statement + prepare FAQ + staff briefing',
            'Monitor ER inquiries closely + update website',
            'Standard patient education materials',
            'Continue monitoring',
            'Pediatric team alert + parent education',
            'Emergency staff training + protocol review'
        ]
    })
    
    st.dataframe(alert_data, width='stretch', hide_index=True)
    
    # Hospital action buttons
    st.markdown("#### 🎯 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📢 Send Hospital Alert", type="primary"):
            st.success("✅ Alert sent to all hospitals in affected regions")
    
    with col2:
        if st.button("📋 Generate FAQ Template"):
            st.info("📄 FAQ template generated for common misinformation topics")
    
    with col3:
        if st.button("📊 Export Hospital Report"):
            st.success("📁 Report exported for hospital administrators")
    
    # Archive recovery queue
    st.subheader("📦 Context Recovery Queue")
    st.markdown("Posts flagged for archival preservation:")
    
    recovery_queue = filtered_posts[filtered_posts['archived'] == False].head(5)[
        ['post_id', 'content', 'platform', 'misinfo_score']
    ]
    st.dataframe(recovery_queue, width='stretch', hide_index=True)

with tab5:
    st.subheader("📈 Advanced Analytics")
    
    # Export functionality
    st.markdown("#### 📊 Data Export")
    col_export1, col_export2, col_export3 = st.columns(3)
    
    with col_export1:
        if st.button("📄 Export Posts CSV"):
            csv = filtered_posts.to_csv(index=False)
            st.download_button(
                label="Download Posts Data",
                data=csv,
                file_name=f"misinformation_posts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with col_export2:
        if st.button("📊 Export Network Data"):
            network_data = edges_df.to_csv(index=False)
            st.download_button(
                label="Download Network Data",
                data=network_data,
                file_name=f"network_edges_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with col_export3:
        if st.button("📋 Export Summary Report"):
            # Generate summary report
            summary = f"""
MISINFORMATION TRACKING SUMMARY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW:
- Total Posts Tracked: {len(filtered_posts)}
- High Risk Posts (>85): {len(filtered_posts[filtered_posts['misinfo_score'] > 85])}
- Archived Posts: {filtered_posts['archived'].sum()}
- Active Spreaders: {filtered_posts['user_id'].nunique()}

PLATFORM BREAKDOWN:
{filtered_posts['platform'].value_counts().to_string()}

CATEGORY BREAKDOWN:
{filtered_posts['category'].value_counts().to_string()}

STATUS BREAKDOWN:
{filtered_posts['status'].value_counts().to_string()}

TOP SUPER SPREADERS:
{spreader_data.head(5).to_string()}
            """
            st.download_button(
                label="Download Summary Report",
                data=summary,
                file_name=f"misinformation_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top misinformation topics
        st.markdown("#### Top Misinformation Topics")
        top_content = filtered_posts['content'].value_counts().head(7)
        fig_topics = px.bar(
            x=top_content.values,
            y=[content[:40] + '...' if len(content) > 40 else content for content in top_content.index],
            orientation='h',
            color=top_content.values,
            color_continuous_scale='Reds'
        )
        fig_topics.update_layout(
            xaxis_title="Occurrences",
            yaxis_title="",
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig_topics, width='stretch', config={'displayModeBar': False})
    
    with col2:
        # Engagement metrics
        st.markdown("#### Engagement Analysis")
        engagement_data = filtered_posts.nlargest(10, 'shares')[['content', 'shares', 'likes', 'comments']]
        engagement_data['content_short'] = engagement_data['content'].apply(
            lambda x: x[:30] + '...' if len(x) > 30 else x
        )
        
        fig_engagement = go.Figure()
        fig_engagement.add_trace(go.Bar(
            x=engagement_data['content_short'],
            y=engagement_data['shares'],
            name='Shares',
            marker_color='#ff6b6b'
        ))
        fig_engagement.add_trace(go.Bar(
            x=engagement_data['content_short'],
            y=engagement_data['likes'],
            name='Likes',
            marker_color='#4ecdc4'
        ))
        
        fig_engagement.update_layout(
            barmode='group',
            xaxis_title="",
            yaxis_title="Count",
            height=400,
            xaxis={'tickangle': -45}
        )
        st.plotly_chart(fig_engagement, width='stretch', config={'displayModeBar': False})
    
    # Status breakdown
    st.markdown("#### Verification Status Breakdown")
    status_data = filtered_posts['status'].value_counts()
    
    # Create dynamic columns based on number of status types
    num_statuses = len(status_data)
    cols = st.columns(num_statuses)
    for i, (status, count) in enumerate(status_data.items()):
        with cols[i]:
            st.metric(status, count)

# Technical Architecture Section
st.divider()
st.markdown("### 🏗️ Technical Architecture")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Data Ingestion Layer:**
    - Python crawlers monitoring health forums
    - Social media APIs (Twitter/X, Reddit, Instagram)
    - Real-time data streaming and processing
    
    **Archive Module:**
    - Integration with Archive.org API
    - Automated preservation of deleted/edited posts
    - Context restoration capabilities
    """)

with col2:
    st.markdown("""
    **Context Graph Engine:**
    - NetworkX for influence chain mapping
    - Super spreader identification algorithms
    - Misinformation mutation tracking
    
    **Risk Analysis Agent:**
    - LLM-powered classification system
    - Severity scoring and alert generation
    - Hospital preparedness recommendations
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 1rem;'>
    <p><b>Agentic Health Context Guard</b> - MVP Demo</p>
    <p>🔒 Privacy Protected | 📊 Real-time Monitoring | 🏥 Hospital-Ready | 🌐 Multi-Platform Tracking</p>
    <p style='font-size: 0.8rem;'>Built for Hackathon 2025 | Team: Hassan Mansuri & Harshal Pande</p>
    <p style='font-size: 0.7rem; margin-top: 1rem;'>
        <strong>Impact Potential:</strong> Reduce misinformation spread time by 60% | 
        Enable hospitals to prepare for false-alarm surges | 
        Preserve clinical context for post-crisis analysis
    </p>
</div>
""", unsafe_allow_html=True)
