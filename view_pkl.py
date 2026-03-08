import pandas as pd
df = pd.read_pickle(r"C:\Users\VISHAL KUMAR\OneDrive\Desktop\WhatsApp Chat Analyzer\whatsapp_chat.pkl")
print(df.head())
print(df.columns)
print(df.info())
