#!/usr/bin/env python3
"""
Web Content Fetcher for Eddie the Expansion Store Evaluator
Retrieves HTML content from websites for image analysis
"""

import requests
import logging
from typing import Optional, Dict
from urllib.parse import urlparse
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebContentFetcher:
    """Fetch web content for analysis"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 10
        self.max_retries = 3
    
    def fetch_html_content(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL"""
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Add small delay to be respectful
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Check if response is HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"URL {url} returned non-HTML content: {content_type}")
                return None
            
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching content from {url}: {e}")
            return None
    
    def fetch_with_retry(self, url: str) -> Optional[str]:
        """Fetch content with retry logic"""
        for attempt in range(self.max_retries):
            try:
                content = self.fetch_html_content(url)
                if content:
                    return content
                
                # Wait before retry
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def get_site_info(self, url: str) -> Dict:
        """Get basic site information"""
        try:
            parsed_url = urlparse(url)
            return {
                'domain': parsed_url.netloc,
                'path': parsed_url.path,
                'scheme': parsed_url.scheme,
                'full_url': url
            }
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return {'domain': 'unknown', 'path': '', 'scheme': 'https', 'full_url': url}
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is accessible"""
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Try to fetch just headers
            response = self.session.head(url, timeout=5)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"URL validation failed for {url}: {e}")
            return False 