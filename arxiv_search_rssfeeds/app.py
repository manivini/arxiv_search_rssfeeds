import streamlit as st
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import pandas as pd
import feedparser
from datetime import datetime, timedelta
import pytz
from dateutil import parser

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    body {
        background-color: #111111;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def fetch_arxiv_data(query='cat:cs.AI', max_results=10):
    base_url = 'http://export.arxiv.org/api/query?'
    encoded_query = urllib.parse.quote(f'"{query}"')
    params = f'search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=lastUpdatedDate&sortOrder=descending'
    full_url = base_url + params
    response = requests.get(full_url)
    return response.text

def parse_arxiv_data(xml_data):
    root = ET.fromstring(xml_data)
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}

    papers = []
    for entry in root.findall('atom:entry', namespace):
        title = entry.find('atom:title', namespace).text.strip()
        link = entry.find('atom:id', namespace).text
        summary = entry.find('atom:summary', namespace).text.strip()
        published = entry.find('atom:published', namespace).text
        authors = ", ".join([author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)])
        
        papers.append({
            'Title': title,
            'Authors': authors,
            'Published': published,
            'Link': link,
            'Summary': summary
        })
    
    return papers

@st.cache_data(ttl=3600)
def fetch_rss_feed(url):
    feed = feedparser.parse(url)
    return feed

def parse_date(date_str):
    try:
        return parser.parse(date_str)
    except (ValueError, TypeError):
        return None

def display_rss_feed(feed, page=1, per_page=10, date_filter=None, keyword_filter=None):
    st.write(f"## RSS Feed: {feed.feed.title}")
    
    # Parse the feed's pubDate
    feed_pub_date = parse_date(feed.feed.get('published')) or parse_date(feed.feed.get('updated'))
    
    feed_data = []
    for entry in feed.entries:
        authors = ', '.join(author.get('name', '') for author in entry.get('authors', []))
        
        # Use the feed's publication date for all entries
        entry_date = feed_pub_date
        
        # Apply date filter
        if date_filter and entry_date:
            if entry_date < date_filter:
                continue
        
        # Apply keyword filter
        if keyword_filter and keyword_filter.lower() not in entry.get('title', '').lower() and keyword_filter.lower() not in entry.get('summary', '').lower():
            continue
        
        feed_data.append({
            'Title': entry.get('title', 'N/A'),
            'Authors': authors,
            'Date': entry_date.strftime("%Y-%m-%d") if entry_date else 'N/A',
            'Link': entry.get('link', '#')
        })
    
    # Sort by date (all entries will have the same date)
    feed_data.sort(key=lambda x: parse_date(x['Date']) or datetime.min.replace(tzinfo=pytz.UTC), reverse=True)
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = feed_data[start:end]
    
    # Create a custom HTML table
    table_html = "<table style='width:100%; border-collapse: collapse;'>"
    table_html += "<tr style='background-color: #f2f2f2;'><th style='padding: 12px; text-align: left; border: 1px solid #ddd;'>Title</th><th style='padding: 12px; text-align: left; border: 1px solid #ddd;'>Authors</th><th style='padding: 12px; text-align: left; border: 1px solid #ddd;'>Date</th></tr>"
    for item in paginated_data:
        table_html += f"<tr>"
        table_html += f"<td style='padding: 12px; border: 1px solid #ddd;'><a href='{item['Link']}' target='_blank'>{item['Title']}</a></td>"
        table_html += f"<td style='padding: 12px; border: 1px solid #ddd;'>{item['Authors']}</td>"
        table_html += f"<td style='padding: 12px; border: 1px solid #ddd;'>{item['Date']}</td>"
        table_html += "</tr>"
    table_html += "</table>"
    
    # Display the custom HTML table
    st.markdown(table_html, unsafe_allow_html=True)
    
    total_pages = -(-len(feed_data) // per_page)  # Ceiling division
    st.write(f"Page {page} of {total_pages}")
    
    col1, col2 = st.columns(2)
    with col1:
        if page > 1:
            if st.button("Previous Page"):
                st.session_state.page -= 1
    with col2:
        if page < total_pages:
            if st.button("Next Page"):
                st.session_state.page += 1

def main():
    st.title('arXiv Paper Search and RSS Feeds')

    # Add a refresh button at the top of the app
    if st.button('Refresh Data'):
        st.rerun()

    query = st.text_input('Enter your search query:', 'retrieval augmented generation')
    max_results = st.slider('Number of results:', 1, 50, 10)

    if st.button('Search'):
        with st.spinner('Fetching data...'):
            arxiv_data = fetch_arxiv_data(query=query, max_results=max_results)
            papers = parse_arxiv_data(arxiv_data)

        df = pd.DataFrame(papers)

        for _, row in df.iterrows():
            st.write(f"## {row['Title']}")
            st.write(f"**Authors:** {row['Authors']}")
            st.write(f"**Published:** {row['Published']}")
            st.write(f"**Link:** [{row['Link']}]({row['Link']})")
            st.write("**Summary:**")
            st.write(row['Summary'])
            st.write("---")

    st.title('arXiv RSS Feeds')
    
    feed_options = {
        'AI (default)': "https://rss.arxiv.org/rss/cs.AI",
        'CS': "http://export.arxiv.org/rss/cs",
        'Physics': "http://export.arxiv.org/rss/physics",
        'Math': "http://export.arxiv.org/rss/math",
        'Quantitative Biology': "http://export.arxiv.org/rss/q-bio",
        'Quantitative Finance': "http://export.arxiv.org/rss/q-fin",
        'Statistics': "http://export.arxiv.org/rss/stat"
    }

    selected_feed = st.selectbox('Select RSS feed:', list(feed_options.keys()), index=0)
    feed_url = feed_options[selected_feed]

    # Date filter
    date_filter = st.date_input("Show entries from (leave empty for all):", value=None)
    if date_filter:
        date_filter = datetime.combine(date_filter, datetime.min.time()).replace(tzinfo=pytz.UTC)

    # Keyword filter
    keyword_filter = st.text_input("Filter by keyword (leave empty for all):")

    if 'page' not in st.session_state:
        st.session_state.page = 1

    with st.spinner(f'Fetching RSS feed for {selected_feed}...'):
        feed = fetch_rss_feed(feed_url)
        display_rss_feed(feed, page=st.session_state.page, date_filter=date_filter, keyword_filter=keyword_filter)

if __name__ == "__main__":
    main()