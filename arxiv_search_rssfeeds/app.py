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

if 'page' not in st.session_state:
    st.session_state.page = 1

if 'cached_feed' not in st.session_state:
    st.session_state.cached_feed = None
    st.session_state.last_successful_fetch = None

def is_weekend():
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    return now.weekday() >= 5 

def get_next_update_time():
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    next_update = now.replace(hour=0, minute=0, second=0, microsecond=0)
    while next_update.weekday() >= 5:  # Skip to Monday if it's weekend
        next_update += timedelta(days=1)
    return next_update

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

# Initialize session state for cached data if it doesn't exist
if 'cached_feed' not in st.session_state:
    st.session_state.cached_feed = None
    st.session_state.last_successful_fetch = None

from datetime import datetime, timedelta
import pytz


@st.cache_data(ttl=3600)
def fetch_rss_feed(url):
    if is_weekend():
        if 'last_feed' in st.session_state:
            return st.session_state.last_feed, "Displaying cached data. Feed updates are paused during weekends."
        else:
            return None, "Feed updates are paused during weekends. Please check back on weekdays."

    current_time = datetime.now(pytz.utc)
    
    try:
        # First, check if the URL is reachable
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # If reachable, parse the feed
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            return None, "The feed is currently empty. This might be due to no recent updates."
        
        st.session_state.last_feed = feed  # Cache the feed
        return feed, None
    except requests.RequestException as e:
        return None, f"Error fetching feed: {str(e)}"
    
    
def display_rss_feed(feed, fetch_time, is_cached, error_message, page=1, per_page=10, date_filter=None, keyword_filter=None):
    if error_message:
        st.warning(error_message)
    
    if feed is None:
        st.error("No data available to display.")
        return

    st.write(f"## RSS Feed: {feed.feed.title}")
    
    if is_cached:
        st.warning(f"Displaying cached data from {fetch_time.strftime('%Y-%m-%d %H:%M:%S UTC')}.")
    else:
        st.success(f"Data refreshed at {fetch_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
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

def parse_date(date_str):
    try:
        return parser.parse(date_str)
    except (ValueError, TypeError):
        return None

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

   
    # Add a unique key to the Refresh Data button
    if st.button('Refresh Data', key='refresh_data_button'):
        st.session_state.pop('last_feed', None)  # Clear cached feed on refresh

    feed, error_message = fetch_rss_feed(feed_url)

    if error_message:
        st.warning(error_message)
        if is_weekend():
            next_update = get_next_update_time()
            st.info(f"Next feed update expected on: {next_update.strftime('%A, %B %d at %I:%M %p')} EST")
    elif feed:
        display_rss_feed(feed, datetime.now(pytz.utc), False, None, page=st.session_state.page)
        st.success(f"Feed last updated on: {feed.feed.get('pubDate', 'Unknown')}")
    else:
        st.error("Failed to fetch the feed.")

    # Add unique keys to the pagination buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.page > 1:
            if st.button("Previous Page", key='prev_page_button'):
                st.session_state.page -= 1
                st.rerun()
    with col2:
        if feed and len(feed.entries) > st.session_state.page * 10:  # Assuming 10 items per page
            if st.button("Next Page", key='next_page_button'):
                st.session_state.page += 1
                st.rerun()

if __name__ == "__main__":
    main()