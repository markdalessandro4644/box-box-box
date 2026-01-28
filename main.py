from flask import Flask, jsonify, render_template_string
import feedparser
from datetime import datetime
import requests
import os
from xml.etree import ElementTree as ET

app = Flask(__name__)

# RSS Feed URLs
FEEDS = {
    'The Race': 'https://www.the-race.com/feed/',
    'F1.com': 'https://www.formula1.com/en/latest/all.xml',
    'Sky Sports F1': 'https://www.skysports.com/rss/11095',
    'The Race F1 Podcast': 'https://feeds.acast.com/public/shows/6819ae2bf30c20bff775e8a1',
    'F1 Beyond the Grid': 'https://audioboom.com/channels/4964339.rss',
    'F1 Nation': 'https://audioboom.com/channels/5024396.rss'
}

PODCAST_SOURCES = ['The Race F1 Podcast', 'F1 Beyond the Grid', 'F1 Nation']

def parse_feed(source_name, feed_url):
    """Parse RSS feed and return formatted entries"""
    try:
        feed = feedparser.parse(feed_url)
        entries = []
        
        is_podcast = source_name in PODCAST_SOURCES
        
        for entry in feed.entries[:10]:  # Get latest 10 items
            # Parse publication date
            pub_date = entry.get('published', entry.get('updated', ''))
            parsed_datetime = None
            try:
                if pub_date:
                    dt = feedparser._parse_date(pub_date)
                    if dt:
                        parsed_datetime = datetime(*dt[:6])
                        time_ago = get_time_ago(parsed_datetime)
                    else:
                        time_ago = 'Recently'
                else:
                    time_ago = 'Recently'
            except:
                time_ago = 'Recently'
            
            # Get description/summary
            description = entry.get('summary', entry.get('description', ''))
            # Strip HTML tags
            import re
            description = re.sub('<[^<]+?>', '', description)
            # Truncate to reasonable length
            if len(description) > 250:
                description = description[:250] + '...'
            
            # Get link
            link = entry.get('link', '#')
            
            # For podcasts, try to get artwork
            artwork_url = None
            if is_podcast:
                # Try to get iTunes image
                if hasattr(entry, 'image'):
                    artwork_url = entry.image.get('href', None)
                elif 'itunes_image' in entry:
                    artwork_url = entry.itunes_image.get('href', None)
            
            entries.append({
                'source': source_name,
                'title': entry.get('title', 'Untitled'),
                'description': description,
                'link': link,
                'time_ago': time_ago,
                'is_podcast': is_podcast,
                'artwork_url': artwork_url,
                'timestamp': parsed_datetime.timestamp() if parsed_datetime else 0
            })
        
        return entries
    except Exception as e:
        print(f"Error parsing {source_name}: {e}")
        return []

def get_time_ago(dt):
    """Calculate human-readable time ago"""
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f'{mins} minute{"s" if mins != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    else:
        weeks = int(seconds / 604800)
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'

@app.route('/api/feeds')
def get_feeds():
    """Fetch all feeds and return combined data"""
    all_entries = []
    
    for source_name, feed_url in FEEDS.items():
        entries = parse_feed(source_name, feed_url)
        all_entries.extend(entries)
    
    # Sort by timestamp (most recent first)
    all_entries.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    return jsonify({
        'success': True,
        'count': len(all_entries),
        'entries': all_entries
    })

@app.route('/api/feeds/<source>')
def get_feed_by_source(source):
    """Fetch specific source feed"""
    if source not in FEEDS:
        return jsonify({'success': False, 'error': 'Source not found'}), 404
    
    entries = parse_feed(source, FEEDS[source])
    
    return jsonify({
        'success': True,
        'source': source,
        'count': len(entries),
        'entries': entries
    })

@app.route('/')
def index():
    """Serve the HTML page"""
    try:
        with open('box-box-box-functional.html', 'r') as f:
            html = f.read()
        return render_template_string(html)
    except FileNotFoundError:
        # If file not found, return a simple message
        return "Box Box Box is running! API available at /api/feeds"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
