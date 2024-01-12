import streamlit as st
from newspaper import Article, Config
from nltk.sentiment import SentimentIntensityAnalyzer
import requests
import nltk
import re
import unicodedata
from bs4 import BeautifulSoup

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

def fetch_search_results(api_key, query, num=10):
    url = 'https://serpapi.com/search'
    results = []

    for start in range(0, num, 10):
        params = {
            'q': query,
            'start': start,
            'api_key': api_key,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx responses
        results += response.json().get('organic_results', [])

    return results

def generate_html_results(search_results, keywords):
    html_results = ""
    
    for index, item in enumerate(search_results):
        title = f"<b>Title:</b> {item.get('title', '')}"
        source = f"<b>Source:</b> <a href='{item.get('link', '')}' style='color: blue; text-decoration: underline;'>{item.get('source', '')}</a>"
        date = f"<b>Date:</b> {item.get('date', '')}"
        snippet = f"<b>Snippet:</b> {item.get('snippet', '')}"
        position = f"<b>Position:</b> {item.get('position', '')}"

        article = Article(item.get('link', ''))

        try:
            article.download()
            article.parse()
    
            summary = article.text
            #st.write(summary)

            # Remove hyperlinks from the summary using BeautifulSoup
            soup = BeautifulSoup(summary, 'html.parser')
            cleaned_summary = ' '.join(soup.stripped_strings)
    
            sentiment = perform_sentiment_analysis(cleaned_summary)

            # Format summary into paragraphs, not exceeding 250 words
            words_limit = 500
            summary_words = cleaned_summary.split()
            summary_paragraphs = [f"<b>Summary:</b>"]
            current_word_count = 0
    
            for word in summary_words:
                # Remove non-printable characters
                word = ''.join(char for char in word if unicodedata.category(char)[0] != 'C')
    
                if current_word_count + len(word) <= words_limit:
                    summary_paragraphs.append(word)
                    current_word_count += len(word) + 1  # Add 1 for the space after the word
                else:
                    break

            formatted_summary = " ".join(summary_paragraphs)
            
            # Format sentiment with color
            sentiment_color = 'green' if sentiment == 'Positive' else ('red' if sentiment == 'Negative' else 'black')
            formatted_sentiment = f"<b>Sentiment:</b> <font color='{sentiment_color}'>{sentiment}</font>"
    
            # Combine all parts into HTML
            html_results += f"{title}<br>{source}<br>{date}<br>{snippet}<br>{position}<br>{formatted_summary}<br>{formatted_sentiment}<br><br>"
            #st.write(f"inside loop: {html_results}")
        except Exception as e:
            st.warning(f"Error processing article {index + 1} titled '{item.get('title', '')}': {e}. Continuing with the next article.")
            continue

    #st.text(f"Total Results: {len(search_results)}")
    #st.write(f"before returning: {html_results}")
    return html_results

def main():
    st.title("Media Screening App")

    # Default keywords
    default_keywords = ["Lido Hack", "Lido Regulatory actions", "Lido SEC", "Lido Hacks", "Lido Token market manipulation", "Lido Scams", "Lido Security Allegations", "$LDO token delisting"]
    keywords = st.text_area("Enter keywords (separated by commas)", ", ".join(default_keywords))
    keywords = [keyword.strip() for keyword in keywords.split(',')]

    if st.button("Analyze News"):
        st.info("Analyzing news... Please wait.")
        try:
            search_results = fetch_search_results(SERP_API_KEY, ' '.join(keywords), num=10)
            html_results = generate_html_results(search_results, keywords)
            st.markdown(html_results, unsafe_allow_html=True)
            st.info("Analysis Complete.")
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
