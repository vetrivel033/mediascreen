import streamlit as st
from newspaper import Article, Config
from nltk.sentiment import SentimentIntensityAnalyzer
import requests
import nltk
import re

nltk.download('vader_lexicon')

# Use the provided SERP API key
SERP_API_KEY = '450ab1c24b6bbe9302e96179ac6f299818b9d5f7e99beef44bc88fd02efc07ca'

def perform_sentiment_analysis(summary):
    sia = SentimentIntensityAnalyzer()
    sentiment_score = sia.polarity_scores(summary)['compound']

    if sentiment_score >= 0.05:
        return "Positive"
    elif sentiment_score <= -0.05:
        return "Negative"
    else:
        return "Neutral"

def is_advertisement(text):
    advertisement_patterns = ["AdChoices", "Advertisement", "Sponsored", "AD"]
    for pattern in advertisement_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def highlight_keywords(text, keywords):
    for keyword in keywords:
        text = re.sub(rf"\b{re.escape(keyword)}\b", f"<mark>{keyword}</mark>", text, flags=re.IGNORECASE)
    return text

def fetch_search_results(api_key, query, num=10):
    url = 'https://serpapi.com/search'
    params = {
        'q': query,
        'num': num,
        'api_key': api_key,
    }

    try:
        response = requests.get(url, params=params)
        results = response.json().get('organic_results', [])
        return results

    except Exception as e:
        st.error(f"Error accessing SERP API: {e}")
        return []

def main():
    st.title("Google News Analysis with Streamlit")

    # Default keywords
    default_keywords = ["Polygon", "SEC", "Compliance"]
    keywords = st.text_area("Enter keywords (separated by commas)", ", ".join(default_keywords))
    keywords = [keyword.strip() for keyword in keywords.split(',')]

    if st.button("Analyze News"):
        st.info("Analyzing news... Please wait.")
        try:
            search_results = fetch_search_results(SERP_API_KEY, ' '.join(keywords), num=10)

            # Create a table to display the results
            table_data = []

            for item in search_results:
                title = item.get('title', '')
                source = f"[{item.get('source', '')}]({item.get('link', '')})"
                date = item.get('date', '')
                snippet = item.get('snippet', '')
                position = item.get('position', '')

                config = Config()
                article = Article(item.get('link', ''), config=config)

                try:
                    article.download()
                    article.parse()
                    summary = article.text

                    if is_advertisement(summary):
                        continue

                    sentiment = perform_sentiment_analysis(summary)

                    highlighted_summary = highlight_keywords(summary, keywords)

                    table_data.append({
                        'Title': title,
                        'Source': source,
                        'Date': date,
                        'Snippet': snippet,
                        'Position': position,
                        'Summary': highlighted_summary,
                        'Sentiment': sentiment
                    })

                except Exception as e:
                    st.warning(f"Error processing article: {e}. Skipping to the next article.")

            st.table(table_data)

        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
