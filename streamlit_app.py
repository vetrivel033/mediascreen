pip install streamlit newspaper3k requests

import streamlit as st
from newspaper import Article
from nltk.sentiment import SentimentIntensityAnalyzer
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import requests
import nltk
import re

nltk.download('vader_lexicon')

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
    advertisement_patterns = ["AdChoices", "Advertisement", "Sponsored"]
    for pattern in advertisement_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

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

def create_pdf(pdf_filename, data, keywords):
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    Story = []

    styles = getSampleStyleSheet()

    for item in data:
        title = item.get('title', '')
        source = item.get('source', '')
        link = item.get('link', '')
        date = item.get('date', '')
        snippet = item.get('snippet', '')
        position = item.get('position', '')

        article = Article(link)
        article.download()
        article.parse()
        summary = article.text

        if is_advertisement(summary):
            continue

        sentiment = perform_sentiment_analysis(summary)

        Story.append(Paragraph(f"<b>Title:</b> {title}", styles['Title']))
        Story.append(Paragraph(f"<b>Source:</b> <a href='{link}' color='blue' underline='true'>{source}</a>", styles['BodyText']))
        Story.append(Paragraph(f"<b>Date:</b> {date}", styles['BodyText']))
        Story.append(Paragraph(f"<b>Snippet:</b> {snippet}", styles['BodyText']))
        Story.append(Paragraph(f"<b>Position:</b> {position}", styles['BodyText']))

        summary_paragraphs = [f"<b>Summary:</b>"]
        summary_lines = summary.split('\n')

        for line in summary_lines[:25]:
            for keyword in keywords:
                line = line.replace(keyword, f"<font color='red'>{keyword}</font>")
            summary_paragraphs.append(line)

        Story.extend([Paragraph(paragraph, styles['BodyText']) for paragraph in summary_paragraphs])

        sentiment_color = colors.green if sentiment == "Positive" else colors.red
        Story.append(Paragraph(f"<b>Sentiment:</b> {sentiment}", ParagraphStyle('Sentiment', textColor=sentiment_color)))
        Story.append(PageBreak())

    doc.build(Story)
    st.success(f"Results written to {pdf_filename}")

def main():
    st.title("Google News Analysis with Streamlit")

    keywords = st.text_area("Enter keywords (separated by commas)", "Python, Programming, OpenAI")
    keywords = [keyword.strip() for keyword in keywords.split(',')]

    if st.button("Analyze News"):
        st.info("Analyzing news... Please wait.")
        try:
            search_results = fetch_search_results(SERP_API_KEY, ' '.join(keywords), num=10)
            pdf_filename = "google_news_analysis.pdf"
            create_pdf(pdf_filename, search_results, keywords)
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
