import streamlit as st
import preprocessor
import helper
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="WhatsApp Chat Analyzer", layout="wide", initial_sidebar_state="expanded", page_icon="📈")

# Premium Custom CSS
custom_css = """
<style>
    /* Styling Metrics Cards */
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 5% 5% 5% 10%;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Bigger emojis for sentiment etc */
    .big-emoji {
        font-size: 3rem;
        display: inline-block;
        padding-bottom: 20px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #00a884 !important;
        font-weight: 600 !important;
    }
    
    /* Main Divider */
    hr {
        border: 1px solid #333;
        margin: 2rem 0;
    }
    
    /* Top Summary Box */
    .summary-box {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.sidebar.title("📱 WhatsApp Analyzer")
st.sidebar.markdown("Upload your exported WhatsApp chat text file below.")

uploaded_file = st.sidebar.file_uploader("📥 Upload Export.txt", type=["txt"])

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")
    
    try:
        df = preprocessor.preprocess(data)
    except Exception as e:
        st.error(f"Error processing the file. Make sure it's a valid WhatsApp export. Details: {e}")
        st.stop()
        
    if df.empty:
           st.error("No valid chat data could be extracted. Please ensure the format matches WhatsApp conventions.")
           st.stop()

    # fetch unique users
    user_list = df['user'].unique().tolist()
    user_list.sort()
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("👤 Show analysis wrt", user_list)

    if st.sidebar.button("🚀 Analyze Now"):
        
        st.title(f"📊 Dashboard Insights for: *{selected_user}*")
        
        # ----------- CHAT SUMMARY SECTION -----------
        st.markdown("---")
        st.header("✨ Quick Summary")
        top_user, peak_time, top_word, top_emoji = helper.get_summary_stats(df)
        
        sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
        with sum_col1:
            st.info(f"🏆 Most Active User: **{top_user}**")
        with sum_col2:
             st.success(f"🔥 Peak Time: **{peak_time}**")
        with sum_col3:
             st.warning(f"💬 Top Word: **'{top_word}'**")
        with sum_col4:
             st.error(f"🤩 Top Emoji: **{top_emoji}**")
             
        # ----------- METRICS SECTION -----------
        st.markdown("---")
        st.header("📈 Key Performance Metrics")
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Total Messages 📝", value=num_messages)
        with col2:
            st.metric(label="Total Words 🗣️", value=words)
        with col3:
            st.metric(label="Media Shared 📷", value=num_media_messages)
        with col4:
            st.metric(label="Links Shared 🔗", value=num_links)
            
        st.markdown("---")

        # ----------- TIMELINES -----------
        st.header("⏳ Interactive Timelines")
        
        # Monthly Timeline
        st.subheader("Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        if not timeline.empty:
            fig = px.line(timeline, x='time', y='message', 
                          markers=True, 
                          color_discrete_sequence=['#00a884'],
                          labels={'time': 'Month-Year', 'message': 'Message Count'},
                          template='plotly_dark')
            fig.update_layout(hovermode='x unified', margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
             st.info("Not enough data.")

        # Daily Timeline
        st.subheader("Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        if not daily_timeline.empty:
            fig = px.line(daily_timeline, x='only_date', y='message', 
                          color_discrete_sequence=['#25D366'],
                          labels={'only_date': 'Date', 'message': 'Message Count'},
                          template='plotly_dark')
            fig.update_layout(hovermode='x unified', margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
             st.info("Not enough data.")

        st.markdown("---")
        
        # ----------- ACTIVITY MAPS -----------
        st.header("📅 Activity Distribution")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Busiest Days")
            busy_day = helper.week_activity_map(selected_user, df)
            fig = px.bar(x=busy_day.index, y=busy_day.values,
                         labels={'x': 'Day of Week', 'y': 'Messages'},
                         color=busy_day.values, color_continuous_scale='Purples',
                         template='plotly_dark')
            fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Busiest Months")
            busy_month = helper.month_activity_map(selected_user, df)
            fig = px.bar(x=busy_month.index, y=busy_month.values,
                         labels={'x': 'Month', 'y': 'Messages'},
                         color=busy_month.values, color_continuous_scale='Oranges',
                         template='plotly_dark')
            fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Activity Heatmap Matrix")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        if not user_heatmap.empty:
            fig = px.imshow(user_heatmap, 
                            labels=dict(x="Time Period", y="Day of Week", color="Msg Count"),
                            color_continuous_scale="YlGnBu",
                            aspect="auto",
                            template='plotly_dark')
            fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ----------- GROUP ANALYSIS -----------
        if selected_user == 'Overall':
            st.header("👥 Most Active Users")
            x, new_df = helper.most_busy_users(df)

            col1, col2 = st.columns([2, 1])
            with col1:
                fig = px.bar(x=x.index, y=x.values,
                             labels={'x': 'User', 'y': 'Messages Sent'},
                             color=x.values, color_continuous_scale='Reds',
                             template='plotly_dark')
                fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.dataframe(new_df, use_container_width=True, height=400)
                
            st.markdown("---")
            
        # ----------- WORDCLOUD AND EMOTIONS -----------
        st.header("🧠 Linguistic & Emotion Analysis")
        st.subheader("Word Cloud & Top Keywords")
        
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown("<p style='text-align:center;'>Hover to see distribution</p>", unsafe_allow_html=True)
            df_wc = helper.create_wordcloud(selected_user, df)
            if df_wc is not None:
                # We still use matplotlib for wordcloud image generation since plotly doesn't naively support raw wordclouds
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(10, 5), facecolor='#1E1E1E')
                ax.imshow(df_wc, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)
            else:
                 st.info("Not enough words to generate WordCloud.")
            
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            most_common_df = helper.most_common_words(selected_user, df)
            if not most_common_df.empty:
                 # Display as clean table
                 st.dataframe(most_common_df, use_container_width=True, height=350)
                 
                 
        st.markdown("---")
        
        # Sentiment & Emoji Row
        col_emo, col_sent = st.columns(2)

        with col_emo:
             st.subheader("😁 Top Emojis Used")
             emoji_df = helper.emoji_helper(selected_user, df)
             if not emoji_df.empty:
                 fig = px.bar(emoji_df.head(10), x='Emoji', y='Frequency',
                              color='Frequency', color_continuous_scale='Viridis',
                              template='plotly_dark')
                 fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), xaxis=dict(tickfont=dict(size=18)))
                 st.plotly_chart(fig, use_container_width=True)
             else:
                  st.info("No emojis found in chat.")

        with col_sent:
             st.subheader("🎭 Sentiment Analysis")
             sentiment_df = helper.sentiment_analysis(selected_user, df)
             if not sentiment_df.empty:
                 # Color map for sentiments
                 color_map = {'Positive': '#00C851', 'Neutral': '#FFBB33', 'Negative': '#ff4444'}
                 fig = px.pie(sentiment_df, values='Message Count', names='Sentiment',
                              color='Sentiment', color_discrete_map=color_map,
                              hole=0.4, template='plotly_dark')
                 fig.update_traces(textposition='inside', textinfo='percent+label')
                 fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
                 st.plotly_chart(fig, use_container_width=True)
             else:
                  st.info("Not enough data to analyze sentiment.")

        st.markdown("---")
        
        # ----------- ADVANCED INSIGHTS -----------
        st.header("🔬 Deep Dive Insights")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Conversation Starters")
            starter_df = helper.conversation_starter(selected_user, df)
            if not starter_df.empty:
                st.dataframe(starter_df, use_container_width=True)
            else:
                st.info("Data insufficient to track conversation starters.")
                
            st.subheader("Average Response Time")
            res_df = helper.response_time_analysis(selected_user, df)
            if not res_df.empty:
                st.dataframe(res_df, use_container_width=True)
            else:
                st.info("Data insufficient to calculate response times.")

        with col2:
            st.subheader("Average Message Length")
            avg_len_df, full_len_df = helper.message_length_analysis(selected_user, df)
            
            if not avg_len_df.empty:
                # Plot distribution instead of just table for premium feel
                fig = px.box(full_len_df, x='user' if selected_user == 'Overall' else None, y='msg_length',
                             points="outliers", color='user' if selected_user == 'Overall' else None,
                             labels={'user': 'User', 'msg_length': 'Characters (Log scale)'},
                             template='plotly_dark', log_y=True)
                fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(avg_len_df, use_container_width=True)
            else:
                 st.info("Data insufficient to calculate message lengths.")
                 
else:
    # Beautiful landing screen
    st.markdown('''
    # Welcome to WhatsApp Chat Analyzer 📊
    We bring your WhatsApp conversations to life through interactive charts, metrics, and deep linguistic insights.

    ### 🛠 How to Export your WhatsApp Chat:
    1. Open any chat or group on **WhatsApp**.
    2. Tap the **three dots** (Android) or **contact name** (iOS).
    3. Select **More > Export Chat** (Android) or **Export Chat** (iOS).
    4. Important: Choose **Without Media**.
    5. Save the generated `.txt` file and upload it into the sidebar!
    ''')
    st.info("👈 Please use the sidebar on the left to upload your file and begin your analysis.")
