import pandas as pd
from urlextract import URLExtract
from wordcloud import WordCloud
from collections import Counter
import emoji
import os
from textblob import TextBlob
import plotly.express as px
import plotly.graph_objects as go

extract = URLExtract()

def fetch_stats(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    num_messages = df.shape[0]

    words = []
    for message in df['message']:
        words.extend(str(message).split())

    # robust media count
    num_media_messages = df[df['message'].astype(str).str.contains('<Media omitted>', na=False, regex=False)].shape[0]

    links = []
    for message in df['message']:
        links.extend(extract.find_urls(str(message)))

    return num_messages, len(words), num_media_messages, len(links)

def get_summary_stats(df):
    if df.empty:
      return None, None, None, None

    # Get most active user
    user_counts = df['user'].value_counts()
    most_active_user = user_counts.index[0] if not user_counts.empty else "N/A"

    # Get peak activity hour
    hour_counts = df['hour'].value_counts()
    peak_hour = hour_counts.index[0] if not hour_counts.empty else "N/A"
    if peak_hour != "N/A":
        peak_time = f"{peak_hour}:00 - {peak_hour+1}:00"
    else:
        peak_time = "N/A"

    # Get most common word
    most_common_df = most_common_words('Overall', df)
    most_common_word = most_common_df.iloc[0][0] if not most_common_df.empty else "N/A"

    # Get most common emoji
    emoji_df = emoji_helper('Overall', df)
    most_common_emoji = emoji_df.iloc[0][0] if not emoji_df.empty else "N/A"

    return most_active_user, peak_time, most_common_word, most_common_emoji

def most_busy_users(df):
    x = df['user'].value_counts().head(10)
    new_df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
        columns={'user': 'User', 'count': 'Percentage (%)'})
    return x, new_df

def create_wordcloud(selected_user, df):
    stop_words = ""
    if os.path.exists('stop_hinglish.txt'):
        with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
            stop_words = f.read()

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[~temp['message'].astype(str).str.contains('<Media omitted>', na=False, regex=False)]

    def remove_stop_words(message):
        y = []
        for word in str(message).lower().split():
             # Basic URL filtering
            if 'http' in word or 'www' in word:
                continue
            if word not in stop_words and len(word) > 2:
                y.append(word)
        return " ".join(y)

    temp['message'] = temp['message'].apply(remove_stop_words)
    
    text = temp['message'].str.cat(sep=" ")
    if not text.strip():
        return None

    wc = WordCloud(width=800, height=400, min_font_size=10, background_color='#1E1E1E', colormap='Set3')
    df_wc = wc.generate(text)
    return df_wc

def most_common_words(selected_user, df):
    stop_words = ""
    if os.path.exists('stop_hinglish.txt'):
        with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
            stop_words = f.read()

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[~temp['message'].astype(str).str.contains('<Media omitted>', na=False, regex=False)]

    words = []
    for message in temp['message']:
        for word in str(message).lower().split():
            # filter out links and short words
            if 'http' in word or 'www' in word:
                  continue
            if word not in stop_words and len(word) > 2:
                words.append(word)

    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    if not most_common_df.empty:
      most_common_df.columns = ['Word', 'Frequency']
    return most_common_df

def emoji_helper(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    emojis = []
    for message in df['message']:
        emojis.extend([c for c in str(message) if emoji.is_emoji(c)])

    emoji_df = pd.DataFrame(Counter(emojis).most_common(20))
    if not emoji_df.empty:
      emoji_df.columns = ['Emoji', 'Frequency']
    return emoji_df

def sentiment_analysis(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[~temp['message'].astype(str).str.contains('<Media omitted>', na=False, regex=False)]

    sentiments = []
    for message in temp['message']:
        analysis = TextBlob(str(message))
        # Determine sentiment
        if analysis.sentiment.polarity > 0:
            sentiments.append('Positive')
        elif analysis.sentiment.polarity < 0:
            sentiments.append('Negative')
        else:
            sentiments.append('Neutral')

    sentiment_counts = pd.Series(sentiments).value_counts().reset_index()
    if not sentiment_counts.empty:
      sentiment_counts.columns = ['Sentiment', 'Message Count']
    return sentiment_counts

def monthly_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()

    time = []
    for i in range(timeline.shape[0]):
        time.append(timeline['month'][i][:3] + "-" + str(timeline['year'][i]))

    timeline['time'] = time
    return timeline

def daily_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    df['only_date'] = df['date'].dt.date
    daily_timeline = df.groupby('only_date').count()['message'].reset_index()
    return daily_timeline

def week_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    return df['day_name'].value_counts()

def month_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    return df['month'].value_counts()

def activity_heatmap(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    period = []
    for hour in df['hour']:
        if hour == 23:
            period.append(str(hour) + "-00")
        elif hour == 0:
            period.append("00-01")
        elif hour < 9:
           period.append(f"0{hour}-0{hour+1}")
        elif hour == 9:
           period.append(f"0{hour}-{hour+1}")
        else:
            period.append(str(hour) + "-" + str(hour + 1))
    
    # We must operate on a copy if we add columns dynamically
    df_copy = df.copy()
    df_copy['period'] = period
    
    user_heatmap = df_copy.pivot_table(index='day_name', columns='period', values='message', aggfunc='count').fillna(0)
    
    # Order days
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    user_heatmap = user_heatmap.reindex(days_order)
    
    return user_heatmap

def conversation_starter(selected_user, df):
    df_copy = df.copy()
    if selected_user != 'Overall':
        df_copy = df_copy[df_copy['user'] == selected_user]
        
    df_copy['only_date'] = df_copy['date'].dt.date
    first_messages = df_copy.groupby('only_date').first().reset_index()
    
    if first_messages.empty:
        return pd.DataFrame()
        
    starter_counts = first_messages['user'].value_counts().reset_index()
    starter_counts.columns = ['User', 'Started Conversations']
    return starter_counts

def response_time_analysis(selected_user, df):
    df_copy = df.copy()
    df_copy = df_copy.sort_values(by='date')
    df_copy['time_diff'] = df_copy['date'].diff().dt.total_seconds() / 60
    
    df_copy['prev_user'] = df_copy['user'].shift(1)
    response_df = df_copy[df_copy['user'] != df_copy['prev_user']]
    
    # Filter out large gaps indicating new sessions (e.g. > 12 hours)
    response_df = response_df[response_df['time_diff'] < 60 * 12]
    
    if selected_user != 'Overall':
        response_df = response_df[response_df['user'] == selected_user]
        
    if response_df.empty:
        return pd.DataFrame()

    avg_response_time = response_df.groupby('user')['time_diff'].mean().reset_index()
    avg_response_time.rename(columns={'time_diff': 'Avg Response Time (Mins)', 'user': 'User'}, inplace=True)
    avg_response_time['Avg Response Time (Mins)'] = avg_response_time['Avg Response Time (Mins)'].round(2)
    return avg_response_time

def message_length_analysis(selected_user, df):
    # Overall dataframe containing msg length for distribution plotting
    df_copy = df.copy()
    if selected_user != 'Overall':
        df_copy = df_copy[df_copy['user'] == selected_user]
        
    if df_copy.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    df_copy['msg_length'] = df_copy['message'].astype(str).apply(len)
    
    avg_length = df_copy.groupby('user')['msg_length'].mean().reset_index()
    avg_length.rename(columns={'msg_length': 'Avg Message Length (Chars)', 'user': 'User'}, inplace=True)
    avg_length['Avg Message Length (Chars)'] = avg_length['Avg Message Length (Chars)'].round(2)
    
    return avg_length, df_copy
