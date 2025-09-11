"""
SEO utilities for the Video Labeling Tool application.
Provides meta tags, sitemap generation, and Google indexing support.
"""

from flask import Blueprint, render_template, request, url_for, current_app
from datetime import datetime
import xml.etree.ElementTree as ET

seo_bp = Blueprint('seo', __name__)

@seo_bp.route('/sitemap.xml')
def sitemap():
    """Generate XML sitemap for search engines."""
    url_root = request.url_root.rstrip('/')
    
    # Create sitemap
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    
    # Add main pages
    pages = [
        ('/', '1.0', 'daily'),
        ('/login', '0.8', 'monthly'),
        ('/register', '0.8', 'monthly'),
        ('/upload', '0.9', 'weekly'),
        ('/projects', '0.9', 'daily'),
        ('/about', '0.7', 'monthly'),
    ]
    
    for page, priority, changefreq in pages:
        url_elem = ET.SubElement(urlset, 'url')
        ET.SubElement(url_elem, 'loc').text = url_root + page
        ET.SubElement(url_elem, 'lastmod').text = datetime.now().strftime('%Y-%m-%d')
        ET.SubElement(url_elem, 'changefreq').text = changefreq
        ET.SubElement(url_elem, 'priority').text = priority
    
    # Convert to string
    sitemap_xml = ET.tostring(urlset, encoding='unicode')
    
    response = current_app.response_class(
        sitemap_xml,
        mimetype='application/xml'
    )
    return response

@seo_bp.route('/robots.txt')
def robots():
    """Generate robots.txt for search engine crawlers."""
    robots_txt = """User-agent: *
Allow: /
Disallow: /uploads/
Disallow: /frames/
Disallow: /datasets/
Disallow: /admin/

Sitemap: {}/sitemap.xml
""".format(request.url_root.rstrip('/'))
    
    response = current_app.response_class(
        robots_txt,
        mimetype='text/plain'
    )
    return response

def get_meta_tags(title="Video Labeling Tool", description="Create labeled datasets from videos with our easy-to-use web application", keywords="video labeling, dataset creation, machine learning, computer vision, annotation tool"):
    """Generate SEO meta tags for HTML pages."""
    return {
        'title': title,
        'description': description,
        'keywords': keywords,
        'og_title': title,
        'og_description': description,
        'og_type': 'website',
        'og_url': request.url,
        'og_site_name': 'Video Labeling Tool',
        'twitter_card': 'summary_large_image',
        'twitter_title': title,
        'twitter_description': description,
        'canonical_url': request.url
    }
