
# arXiv Paper Search and RSS Feed Viewer

This Streamlit app allows users to search for arXiv papers and view RSS feeds from various arXiv categories. It provides an easy-to-use interface for exploring recent scientific publications.

## Features

- Search arXiv papers by keyword (leverages arxiv search API)
- View and filter arXiv RSS feeds by category (default being cs.ai category)
- Filter RSS feed entries by date and keyword
- Paginated results for easy navigation
- Refresh button to fetch the latest data

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/manivini/arxiv_search_rssfeeds.git
   cd arxiv_search_rssfeeds
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser and go to the URL provided by the Streanlit in the terminal (usually http://localhost:8501)
   
3. Use the app:
   - Enter a search query in the text input (default is retrieval augmented generation)
   - Adjust the number of results using the slider
   - Click the "Search" button to fetch and display the results
   - For RSS feeds, click Refresh Data on top left of the page first, then choose corresponding options in dropdown (default topic 
     is cs.ai), latest RSS feeds appear for the chosen category
     
## Acknowledgments

arXiv.org for providing the API and RSS feeds.
Streamlit for the amazing app framework.

## Live Demo
This application is deployed on Streamlit Community Cloud. Try it out here:
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://https://arxivsearchrssfeeds.streamlit.app/)

## Screenshot![Screenshot 2024-08-26 at 4 30 07 PM](https://github.com/user-attachments/assets/7040d21d-3df7-4655-9a28-2693e675fac7)




