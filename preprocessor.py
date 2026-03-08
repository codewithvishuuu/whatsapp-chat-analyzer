import re
import pandas as pd

def preprocess(data):
    # Regex for standard WhatsApp date formats
    pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s?(?:am|pm|AM|PM)?\s?-\s'
    
    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    if not messages:
        # Fallback to iOS bracket format
        pattern = r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2}\s?(?:AM|PM|am|pm)?\]\s'
        messages = re.split(pattern, data)[1:]
        dates = re.findall(pattern, data)
        dates = [d.replace('[', '').replace(']', '').strip() for d in dates]
    else:
        dates = [d.replace(' - ', '').strip() for d in dates]

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})
    
    # Parse dates safely
    try:
        df['date'] = pd.to_datetime(df['message_date'], format='mixed', dayfirst=True)
    except:
        df['date'] = pd.to_datetime(df['message_date'], infer_datetime_format=True, errors='coerce')


    users = []
    messages_clean = []
    
    # Extract users and messages
    for message in df['user_message']:
        entry = re.split(r'([\w\W]+?):\s', message)
        if entry[1:]:  # User name found
            users.append(entry[1])
            messages_clean.append(" ".join(entry[2:]))
        else:
            users.append('group_notification')
            messages_clean.append(entry[0])

    df['user'] = users
    df['message'] = messages_clean
    df.drop(columns=['user_message', 'message_date'], inplace=True)

    # Clean system messages
    df = df[df['user'] != 'group_notification']
    df = df[~df['message'].str.contains('Messages and calls are end-to-end encrypted', na=False, case=False)]
    
    # Reset index after filtering
    df.reset_index(drop=True, inplace=True)

    # Extract timeline and date features
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    return df
