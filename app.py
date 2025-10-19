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
        st.plotly_chart(fig_platform, width='stretch')
    
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
        st.plotly_chart(fig_category, width='stretch')
    
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
    st.plotly_chart(fig_timeline, width='stretch')
    
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
    st.plotly_chart(fig_hist, width='stretch')

with tab2:
    st.subheader("🕸️ Misinformation Spread Network")
    st.info("📍 Larger nodes = Super spreaders | Thicker lines = More shared content")
    
    # Create network graph
    G = nx.from_pandas_edgelist(edges_df, 'source', 'target', edge_attr='weight')
    
    # Calculate node metrics
    degree_centrality = nx.degree_centrality(G)
    
    # Layout
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
    
    # Edge trace
    edge_x = []
    edge_y = []
    edge_weights = []
    
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_weights.append(edge[2]['weight'])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Node trace
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        degree = G.degree(node)
        centrality = degree_centrality[node]
        node_text.append(f"<b>{node}</b><br>Connections: {degree}<br>Centrality: {centrality:.3f}")
        node_size.append(degree * 8 + 15)
        node_color.append(degree)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=node_text,
        text=[node.replace('user_', 'U') for node in G.nodes()],
        textposition="top center",
        textfont=dict(size=10, color='#333'),
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
        data=[edge_trace, node_trace],
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
    
    st.plotly_chart(fig_network, width='stretch')
    
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
                if row['archived']:
                    st.success("✅ Archived")
                else:
                    st.warning("⏳ Pending")
            
            st.divider()

with tab4:
    st.subheader("🚨 Active Threat Alerts")
    
    # Critical alerts
    st.markdown('<div class="alert-high"><b>🔴 CRITICAL</b>: Viral post claiming "vaccines contain microchips" reached 50K+ shares across platforms</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="alert-high"><b>🔴 CRITICAL</b>: Super spreader "user_1" sharing false treatment claims - 8 direct connections</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="alert-medium"><b>🟠 HIGH</b>: Misinformation about COVID cure trending on Reddit - 3,500 shares in 6 hours</div>', unsafe_allow_html=True)
    
    st.info("🔵 MEDIUM: Unverified health claim about natural immunity spreading on Instagram")
    
    st.divider()
    
    # Hospital alert dashboard
    st.subheader("🏥 Hospital Preparedness Dashboard")
    
    alert_data = pd.DataFrame({
        'Hospital': ['City General Hospital', 'Regional Medical Center', 'Metro Community Hospital', 'University Hospital'],
        'Alert Level': ['🔴 Critical', '🟠 High', '🟡 Medium', '🟢 Low'],
        'Affected Posts': [18, 12, 5, 2],
        'Primary Threat': ['Fake cure claims', 'Vaccine misinformation', 'Treatment myths', 'Prevention myths'],
        'Recommended Action': [
            'Issue public statement + prepare FAQ',
            'Monitor ER inquiries closely',
            'Standard patient education',
            'Continue monitoring'
        ]
    })
    
    st.dataframe(alert_data, width='stretch', hide_index=True)
    
    # Archive recovery queue
    st.subheader("📦 Context Recovery Queue")
    st.markdown("Posts flagged for archival preservation:")
    
    recovery_queue = filtered_posts[filtered_posts['archived'] == False].head(5)[
        ['post_id', 'content', 'platform', 'misinfo_score']
    ]
    st.dataframe(recovery_queue, width='stretch', hide_index=True)

with tab5:
    st.subheader("📈 Advanced Analytics")
    
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
        st.plotly_chart(fig_topics, width='stretch')
    
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
        st.plotly_chart(fig_engagement, width='stretch')
    
    # Status breakdown
    st.markdown("#### Verification Status Breakdown")
    status_data = filtered_posts['status'].value_counts()
    
    # Create dynamic columns based on number of status types
    num_statuses = len(status_data)
    cols = st.columns(num_statuses)
    for i, (status, count) in enumerate(status_data.items()):
        with cols[i]:
            st.metric(status, count)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 1rem;'>
    <p><b>Agentic Health Context Guard</b> - MVP Demo</p>
    <p>🔒 Privacy Protected | 📊 Real-time Monitoring | 🏥 Hospital-Ready | 🌐 Multi-Platform Tracking</p>
    <p style='font-size: 0.8rem;'>Built for Hackathon 2025 | Team: Hassan Mansuri & Harshal Pande</p>
</div>
""", unsafe_allow_html=True)
