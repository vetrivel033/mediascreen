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
    results = []

    for start in range(0, num, 10):
        params = {
            'q': query,
            'start': start,
            'api_key': api_key,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx responses
            results += response.json().get('organic_results', [])
        except requests.exceptions.HTTPError as errh:
            st.error(f"HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            st.error(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            st.error(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            st.error(f"Error: {err}")

    return results

def generate_html_results(search_results, keywords):
    html_results = ""
    for item in search_results:
        try:
            title = f"<b>Title:</b> {item.get('title', '')}"
            source = f"<b>Source:</b> <a href='{item.get('link', '')}' style='color: blue; text-decoration: underline;'>{item.get('source', '')}</a>"
            date = f"<b>Date:</b> {item.get('date', '')}"
            snippet = f"<b>Snippet:</b> {item.get('snippet', '')}"
            position = f"<b>Position:</b> {item.get('position', '')}"

            config = Config()
            article = Article(item.get('link', ''), config=config)

            article.download()
            article.parse()
            summary = article.text

            if is_advertisement(summary):
                continue

            sentiment = perform_sentiment_analysis(summary)

            # Highlight keywords in summary
            highlighted_summary = highlight_keywords(summary, keywords)

            # Format summary into paragraphs, not exceeding 25 lines
            summary_paragraphs = [f"<b>Summary:</b>"]
            summary_lines = highlighted_summary.split('\n')

            for i, line in enumerate(summary_lines):
                if i < 25:
                    summary_paragraphs.append(line)
                else:
                    break

            formatted_summary = "<br>".join(summary_paragraphs)

            # Format sentiment with color
            sentiment_color = 'green' if sentiment == 'Positive' else ('red' if sentiment == 'Negative' else 'black')
            formatted_sentiment = f"<b>Sentiment:</b> <font color='{sentiment_color}'>{sentiment}</font>"

            # Combine all parts into HTML
            html_results += f"{title}<br>{source}<br>{date}<br>{snippet}<br>{position}<br>{formatted_summary}<br>{formatted_sentiment}<br><br>"
        except Exception as e:
            st.warning(f"Error processing article: {e}. Skipping to the next article.")

    st.text(f"Total Results: {len(search_results)}")
    return html_results

def main():
    st.title("Media Screening App")

    # Default keywords
    default_keywords = ["Polygon", "SEC", "Compliance"]
    keywords = st.text_area("Enter keywords (separated by commas)", ", ".join(default_keywords))
    keywords = [keyword.strip() for keyword in keywords.split(',')]

    if st.button("Analyze News"):
        st.info("Analyzing news... Please wait.")
        try:
            search_results = fetch_search_results(SERP_API_KEY, ' '.join(keywords), num=10)
            html_results = generate_html_results(search_results, keywords)
            st.markdown(html_results, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
