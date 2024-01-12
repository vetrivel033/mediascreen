import os
import streamlit as st
from newspaper import Article, Config
from nltk.sentiment import SentimentIntensityAnalyzer
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import requests
import nltk
import re
import gdown

nltk.download('vader_lexicon')

# Use the provided SERP API key
SERP_API_KEY = '450ab1c24b6bbe9302e96179ac6f299818b9d5f7e99beef44bc88fd02efc07ca'

# Google Drive folder ID where the PDF will be uploaded
GOOGLE_DRIVE_FOLDER_ID = '1mVcWrGnZgL8Lq2WNR-l7wJN-4y8LmdCB'

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

        config = Config()
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        config.browser_user_agent = user_agent

        article = Article(link, config=config)

        try:
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

        except Exception as e:
            st.warning(f"Error processing article: {e}. Skipping to the next article.")

    doc.build(Story)
    st.success(f"Results written to {pdf_filename}")

def upload_to_google_drive(pdf_filename):
    st.info("Uploading PDF to Google Drive... Please wait.")
    gdown.upload(pdf_filename, drive_data=GOOGLE_DRIVE_FOLDER_ID, file_id=None)
    st.success("PDF uploaded to Google Drive.")
    st.info(f"View the uploaded PDF on Google Drive: [Link](https://drive.google.com/drive/folders/{GOOGLE_DRIVE_FOLDER_ID})")

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
            pdf_filename = "google_news_analysis.pdf"
            create_pdf(pdf_filename, search_results, keywords)
            upload_to_google_drive(pdf_filename)
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
