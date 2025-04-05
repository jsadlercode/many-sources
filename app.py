import feedparser
from flask import Flask, render_template, request
import logging # Added for basic logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# --- Configuration ---
# Define your list of news sources and their RSS feed URLs
# Using common, generally reliable international sources for this example
RSS_FEEDS = {
    "ABC News": "https://www.abc.net.au/news/feed/2942460/rss.xml",
    "Associated Press (AP)": "https://rsshub.app/apnews/topics/apf-topnews", # Using rsshub proxy for potentially better format
    "Reuters": "https://www.reutersagency.com/feed/?best-topics=world-news&post_type=best", # World News feed
    "BBC News": "http://feeds.bbci.co.uk/news/world/rss.xml", # World News feed
    "NPR": "https://feeds.npr.org/1001/rss.xml", # News feed
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    
    # Add more sources as needed (check their websites for official RSS feeds)
    # "New York Times": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", # Example
    # "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSWorldNews.xml", # Example
}

# Max summary length (approximate)
MAX_SUMMARY_LENGTH = 250

# --- Helper Functions ---
def fetch_and_filter_feed(source_name, feed_url, keywords_list):
    """Fetches an RSS feed and filters entries based on keywords."""
    matching_articles = []
    try:
        logging.info(f"Fetching feed for: {source_name} ({feed_url})")
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            logging.warning(f"Feedparser encountered issues with {source_name}: {feed.bozo_exception}")
            # Decide if you want to proceed despite potential issues, here we will.

        logging.info(f"Processing {len(feed.entries)} entries for {source_name}")

        for entry in feed.entries:
            title = entry.get('title', '').lower()
            summary = entry.get('summary', '').lower() # Sometimes 'description' is used
            content = entry.get('content', '') # Check content too if available
            full_text_lower = summary # Start with summary
            if content and isinstance(content, list) and len(content) > 0:
                 # feedparser often puts content in a list [{...}]
                 full_text_lower += " " + content[0].get('value', '').lower()


            # Check if *all* keywords are present in title OR summary/content
            match = False
            # Check in title first
            if all(keyword in title for keyword in keywords_list):
                match = True
            # If not in title, check in summary/content
            elif all(keyword in full_text_lower for keyword in keywords_list):
                 match = True


            if match:
                # Basic summary cleanup (optional, can be improved)
                raw_summary = entry.get('summary', 'No summary available.')
                # Very basic HTML tag removal - consider using BeautifulSoup for robustness
                import re
                clean_summary = re.sub('<[^<]+?>', '', raw_summary)

                truncated_summary = (clean_summary[:MAX_SUMMARY_LENGTH] + '...') if len(clean_summary) > MAX_SUMMARY_LENGTH else clean_summary

                matching_articles.append({
                    'title': entry.get('title', 'No Title'),
                    'link': entry.get('link', '#'),
                    'summary': truncated_summary,
                    # 'published': entry.get('published') # Could add published date later
                })
        logging.info(f"Found {len(matching_articles)} matching articles for {source_name}")

    except Exception as e:
        logging.error(f"Error fetching or parsing feed for {source_name}: {e}", exc_info=True) # Log full traceback

    return matching_articles

# --- Flask Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    keywords_str = ''
    results = {}
    search_attempted = False # Flag to know if we should show the "Results for..." section

    if request.method == 'POST':
        search_attempted = True
        keywords_str = request.form.get('keywords', '').strip()
        if keywords_str:
            # Simple keyword splitting, lowercased
            keywords_list = [kw.strip().lower() for kw in keywords_str.split() if kw.strip()]
            logging.info(f"Search initiated for keywords: {keywords_list}")

            if not keywords_list:
                 # Handle case where input was just whitespace
                 return render_template('index.html', keywords=keywords_str, results=None, search_attempted=search_attempted)


            for source_name, feed_url in RSS_FEEDS.items():
                # Pass the list of keywords
                results[source_name] = fetch_and_filter_feed(source_name, feed_url, keywords_list)
        else:
            # Handle empty keyword submission if needed, maybe show a message
             logging.info("Empty keyword search submitted.")


    # Pass keywords back to template to refill input box
    # Pass results dictionary (even if empty)
    # Pass search_attempted flag
    return render_template('index.html', keywords=keywords_str, results=results, search_attempted=search_attempted)

# --- Run Application ---
if __name__ == '__main__':
    # Use port 5001 to avoid conflict if 5000 is common
    app.run(debug=True, port=5001) # debug=True is good for development, disable for production