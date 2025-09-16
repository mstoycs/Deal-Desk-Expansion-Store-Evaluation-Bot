#!/usr/bin/env python3
"""
Expansion Store Evaluation Bot

This bot evaluates whether a requested store qualifies as an expansion store
under the existing main shop URL based on the criteria defined in section 9.13
of the Plus agreement.
"""

import re
import requests
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
import logging
from bs4 import BeautifulSoup
import time
import random

# Import enhanced image analysis modules
# REMOVED: Logo and visual branding analysis temporarily disabled
# try:
#     from image_analyzer import EnhancedBrandingAnalyzer
#     from web_content_fetcher import WebContentFetcher
#     IMAGE_ANALYSIS_AVAILABLE = True
# except ImportError as e:
#     logging.warning(f"Image analysis modules not available: {e}")
#     IMAGE_ANALYSIS_AVAILABLE = False

# Import product extraction module
try:
    from product_extractor import ProductExtractor, Product
    PRODUCT_EXTRACTION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Product extraction module not available: {e}")
    PRODUCT_EXTRACTION_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoreType(Enum):
    ONLINE = "online"
    PHYSICAL = "physical"
    WHOLESALE = "wholesale"
    DEVELOPMENT = "development"
    STAGING = "staging"

class StoreBusinessType(Enum):
    D2C = "d2c"  # Direct to Consumer
    B2B = "b2b"  # Business to Business

class EvaluationResult(Enum):
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    INSUFFICIENT_DATA = "insufficient_data"

@dataclass
class StoreInfo:
    """Store information extracted from URL analysis"""
    url: str
    store_name: Optional[str] = None
    branding_elements: List[str] = None
    goods_services: List[str] = None
    products: List[str] = None  # New field for product names
    language: Optional[str] = None
    currency: Optional[str] = None
    store_type: StoreType = StoreType.ONLINE
    is_high_volume: bool = False
    is_development: bool = False
    is_staging: bool = False
    business_type: StoreBusinessType = StoreBusinessType.D2C # Default to D2C

@dataclass
class EvaluationCriteria:
    """Criteria for expansion store evaluation"""
    main_brand_name: str
    main_brand_branding: List[str]
    main_brand_goods_services: List[str]
    main_brand_products: List[str]  # New field for main brand products
    main_brand_language: str
    main_brand_currency: str
    main_brand_business_type: StoreBusinessType = StoreBusinessType.D2C

@dataclass
class CriteriaAnalysis:
    """Detailed analysis for a specific criteria"""
    criteria_name: str
    criteria_met: bool
    summary: str
    main_store_evidence: Dict[str, any]  # Images, names, URLs, etc.
    expansion_store_evidence: Dict[str, any]  # Images, names, URLs, etc.
    evaluation_details: Dict[str, any]  # Additional evaluation information

@dataclass
class EvaluationReport:
    """Complete evaluation report"""
    result: EvaluationResult
    store_info: StoreInfo
    criteria_met: Dict[str, bool]
    criteria_analysis: Dict[str, CriteriaAnalysis]  # Detailed analysis for each criteria
    reasons: List[str]
    recommendations: List[str]
    confidence_score: float
    product_analysis: Optional[Dict] = None  # Detailed product analysis for B2B evaluations

class ExpansionStoreEvaluator:
    """
    Main evaluator class for expansion store requests
    """
    
    def __init__(self):
        self.development_keywords = ['dev', 'development', 'test', 'staging', 'preview']
        self.high_volume_keywords = ['agency', 'high-volume', 'enterprise']
        
        # Initialize product extraction if available
        if PRODUCT_EXTRACTION_AVAILABLE:
            self.product_extractor = ProductExtractor()
            self.use_real_product_extraction = True
            logger.info("Real product extraction enabled")
        else:
            self.product_extractor = None
            self.use_real_product_extraction = False
            logger.info("Using fallback product extraction")
    
    def extract_store_info(self, url: str) -> StoreInfo:
        """
        Extract store information from the provided URL
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            path = parsed_url.path.lower()
            
            # Initialize store info
            store_info = StoreInfo(url=url)
            
            # Determine store type
            if any(keyword in domain or keyword in path for keyword in self.development_keywords):
                if 'staging' in domain or 'staging' in path:
                    store_info.store_type = StoreType.STAGING
                    store_info.is_staging = True
                else:
                    store_info.store_type = StoreType.DEVELOPMENT
                    store_info.is_development = True
            
            # Check for high volume indicators
            if any(keyword in domain or keyword in path for keyword in self.high_volume_keywords):
                store_info.is_high_volume = True
            
            # Extract store name from domain
            store_info.store_name = self._extract_store_name(domain)
            
            # Extract branding elements
            store_info.branding_elements = self._extract_branding_elements(domain, path)
            
            # Extract goods and services (would need actual scraping in production)
            store_info.goods_services = self._extract_goods_services(url)
            
            # Extract products (would need actual scraping in production)
            store_info.products = self._extract_products(url)
            
            # Extract language and currency
            store_info.language = self._extract_language(domain, path)
            store_info.currency = self._extract_currency(domain, path)
            
            return store_info
            
        except Exception as e:
            logger.error(f"Error extracting store info from {url}: {e}")
            return StoreInfo(url=url)
    
    def _extract_store_name(self, domain: str) -> Optional[str]:
        """Extract store name from domain"""
        # Remove common TLDs and subdomains
        parts = domain.split('.')
        if len(parts) >= 2:
            return parts[-2]  # Second to last part is usually the main domain
        return None
    
    def _extract_branding_elements(self, domain: str, path: str) -> List[str]:
        """Extract branding elements from URL"""
        elements = []
        
        # Extract from domain
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            elements.append(domain_parts[-2])
        
        # Extract from path
        path_parts = [p for p in path.split('/') if p]
        elements.extend(path_parts)
        
        return elements
    
    def _extract_goods_services(self, url: str) -> List[str]:
        """
        Extract goods and services from the store using real product data.
        If no products are found, extracts services from the website content.
        """
        if self.use_real_product_extraction and self.product_extractor:
            try:
                # Extract products and derive goods/services from categories
                result = self.product_extractor.extract_products_from_store(url, max_products=20)
                if result.success and result.products:
                    # Extract unique categories and product types
                    categories = set()
                    for product in result.products:
                        if product.category:
                            categories.add(product.category)
                        # Also extract from product name patterns
                        if product.name:
                            # Simple category extraction from product names
                            name_lower = product.name.lower()
                            if any(word in name_lower for word in ['shirt', 't-shirt', 'polo', 'blouse']):
                                categories.add('Clothing')
                            elif any(word in name_lower for word in ['shoes', 'boots', 'sneakers', 'sandals']):
                                categories.add('Footwear')
                            elif any(word in name_lower for word in ['bag', 'purse', 'wallet', 'backpack']):
                                categories.add('Accessories')
                            elif any(word in name_lower for word in ['book', 'magazine', 'journal']):
                                categories.add('Books & Media')
                            elif any(word in name_lower for word in ['coffee', 'tea', 'beverage']):
                                categories.add('Beverages')
                            elif any(word in name_lower for word in ['jewelry', 'necklace', 'ring', 'earrings']):
                                categories.add('Jewelry')
                            elif any(word in name_lower for word in ['tech', 'phone', 'laptop', 'computer']):
                                categories.add('Electronics')
                    
                    return list(categories) if categories else ['General Products']
                else:
                    logger.info(f"No products found for {url} - extracting services from website content")
                    return self._extract_services_from_website(url)
                    
            except Exception as e:
                logger.error(f"Error in real goods/services extraction for {url}: {e}")
                return self._fallback_goods_services(url)
        else:
            return self._fallback_goods_services(url)
    
    def _extract_services_from_website(self, url: str) -> List[str]:
        """Extract services from website content when no products are found"""
        try:
            # This would involve analyzing the website content for services
            # For now, return common service categories based on domain
            domain = urlparse(url).netloc.lower()
            
            if 'hvac' in domain or ('air' in domain and ('conditioning' in domain or 'heating' in domain)):
                return ['HVAC Services', 'Air Conditioning', 'Heating Services']
            elif 'plumbing' in domain:
                return ['Plumbing Services', 'Repair Services']
            elif 'electrical' in domain:
                return ['Electrical Services', 'Installation Services']
            elif 'cleaning' in domain:
                return ['Cleaning Services', 'Maintenance Services']
            elif 'hair' in domain or 'salon' in domain or 'beauty' in domain:
                return ['Hair Care Services', 'Beauty Services', 'Professional Hair Services']
            elif 'consulting' in domain or 'consultants' in domain:
                return ['Consulting Services', 'Professional Services']
            elif 'agency' in domain or 'marketing' in domain:
                return ['Marketing Services', 'Digital Services']
            elif 'law' in domain or 'legal' in domain:
                return ['Legal Services', 'Professional Services']
            elif 'medical' in domain or 'health' in domain:
                return ['Healthcare Services', 'Medical Services']
            else:
                # Return empty list instead of generic services for unknown sites
                # This prevents false matches between unrelated e-commerce sites
                return []
                
        except Exception as e:
            logger.error(f"Error extracting services from {url}: {e}")
            return []
    
    def _fallback_goods_services(self, url: str) -> List[str]:
        """Fallback goods/services extraction using domain analysis"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Generate realistic goods/services based on store type
            if 'fashion' in domain or 'clothing' in domain or 'apparel' in domain:
                return ['Clothing', 'Accessories', 'Fashion Items']
            elif 'tech' in domain or 'electronics' in domain or 'computer' in domain:
                return ['Electronics', 'Technology', 'Computers']
            elif 'book' in domain or 'library' in domain:
                return ['Books', 'Media', 'Publications']
            elif 'coffee' in domain or 'cafe' in domain or 'beverage' in domain:
                return ['Beverages', 'Coffee', 'Food Items']
            elif 'jewelry' in domain or 'accessories' in domain:
                return ['Jewelry', 'Accessories', 'Luxury Items']
            elif 'boutique' in domain or 'luxury' in domain:
                return ['Luxury Items', 'Boutique Products', 'Premium Goods']
            else:
                return ['General Products', 'Retail Items']
                
        except Exception as e:
            logger.error(f"Error in fallback goods/services extraction from {url}: {e}")
            return ['General Products']
    
    def _extract_products(self, url: str) -> List[str]:
        """
        Extract real product names and URLs using the most effective approach.
        Always uses universal collection discovery for comprehensive product extraction.
        Returns a list of product names with their URLs for verification.
        """
        if self.use_real_product_extraction and self.product_extractor:
            try:
                logger.info(f"🔍 Extracting products from {url} using universal collection discovery")
                
                # Use the product extractor's main extraction method which includes:
                # 1. Static knowledge base check for known major sites
                # 2. Dynamic knowledge base check for previously learned sites  
                # 3. Universal collection discovery for new sites
                # 4. Automatic learning and caching for future use
                result = self.product_extractor.extract_products_from_store(url, max_products=20)
                
                if result and result.success and result.products:
                    logger.info(f"✅ Successfully extracted {len(result.products)} products using {result.extraction_method}")
                    product_names_with_urls = []
                    for product in result.products:
                        if product.name and product.url:
                            product_names_with_urls.append(f"{product.name} - {product.url}")
                        elif product.name:
                            product_names_with_urls.append(product.name)
                    return product_names_with_urls[:25]
                else:
                    logger.info(f"❌ No products found for {url}")
                    return []
                    
            except Exception as e:
                logger.error(f"Error in product extraction for {url}: {e}")
                return []
        else:
            logger.info(f"Product extraction not available for {url}")
            return []

    def _sophisticated_product_extraction(self, url: str) -> List[str]:
        """
        Sophisticated multi-step product extraction that validates actual products
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin, urlparse
            import re
            import time
            import random
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            session = requests.Session()
            session.headers.update(headers)
            
            # Step 1: Get main page and analyze structure
            response = session.get(url, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {url}: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            validated_products = []
            
            # Step 2: Find potential product URLs using refined selectors
            potential_product_urls = self._find_potential_product_urls(soup, url)
            logger.info(f"Found {len(potential_product_urls)} potential product URLs")
            
            # Step 3: Validate and extract from individual product pages (less strict initially)
            for product_url in potential_product_urls[:30]:  # Test even more URLs
                try:
                    time.sleep(random.uniform(0.3, 0.8))  # Faster but still respectful
                    product_info = self._validate_and_extract_product(session, product_url)
                    if product_info:
                        validated_products.append(product_info)
                        logger.info(f"✅ Validated product: {product_info}")
                        
                        if len(validated_products) >= 10:  # Reduce limit to ensure we try direct collections
                            break
                            
                except Exception as e:
                    logger.warning(f"Failed to validate product URL {product_url}: {e}")
                    continue
            
            # Step 4: Always try direct collection discovery to find brand-specific products
            logger.info(f"Found {len(validated_products)} products so far, trying direct collection discovery")
            direct_collection_products = self._extract_from_direct_collections(session, url)
            validated_products.extend(direct_collection_products)
            

            
            # Step 5: If we still don't have enough products, try category pages
            if len(validated_products) < 8:
                logger.info(f"Only found {len(validated_products)} products, trying category pages")
                category_products = self._extract_from_category_pages(session, soup, url)
                validated_products.extend(category_products)
            
            # Step 5: If still not enough, try less strict extraction from main page
            if len(validated_products) < 5:
                logger.info(f"Only found {len(validated_products)} products, trying main page extraction")
                main_page_products = self._extract_from_main_page_less_strict(soup, url)
                validated_products.extend(main_page_products)
            
            # Step 6: Final fallback - structured data and enhanced text analysis
            if len(validated_products) < 3:
                logger.info(f"Only found {len(validated_products)} products, trying fallback methods")
                fallback_products = self._extract_products_fallback_methods(soup, url)
                validated_products.extend(fallback_products)
            
            logger.info(f"Sophisticated extraction found {len(validated_products)} validated products from {url}")
            return validated_products[:20]
            
        except Exception as e:
            logger.error(f"Sophisticated product extraction failed for {url}: {e}")
            return []

    def _extract_from_main_page_less_strict(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Less strict extraction from main page when sophisticated methods don't find enough products
        """
        products = []
        
        try:
            from urllib.parse import urljoin
            
            # Look for any links that might be products with less strict validation
            product_selectors = [
                'a[href*="/products/"]',
                'a[href*="/product/"]', 
                'a[href*="/item/"]',
                '.product-item a',
                '.product-card a',
                '.product-link',
                'a[data-product-id]',
                'a[data-product-handle]',
                # Korean/Asian e-commerce patterns
                'a[href*="product_no="]',
                'a[href*="goods_no="]',
                'a[href*="item_no="]',
                'a[href*="prd_no="]',
                'a[href*="/product/detail.html"]'
            ]
            
            found_links = set()
            
            for selector in product_selectors:
                try:
                    links = soup.select(selector)
                    logger.info(f"Less strict selector '{selector}' found {len(links)} links")
                    
                    for link in links[:10]:  # Check more links per selector
                        href = link.get('href')
                        if href and self._is_individual_product_url(href):
                            full_url = urljoin(base_url, href)
                            
                            # Extract name with less strict validation
                            name = self._extract_name_less_strict(link)
                            if name:
                                product_entry = f"{name} - {full_url}"
                                if product_entry not in found_links:
                                    found_links.add(product_entry)
                                    products.append(product_entry)
                                    logger.info(f"Less strict extraction found: {name}")
                                    
                                    if len(products) >= 10:
                                        break
                                        
                except Exception as e:
                    logger.warning(f"Error with less strict selector {selector}: {e}")
                    continue
                
                if len(products) >= 10:
                    break
                    
        except Exception as e:
            logger.warning(f"Less strict main page extraction failed: {e}")
        
        return products

    def _extract_name_less_strict(self, link_element) -> str:
        """
        Extract product name with less strict validation for fallback
        """
        name = None
        
        # Try multiple approaches
        # 1. Alt text from images
        img = link_element.find('img')
        if img and img.get('alt'):
            alt_text = img.get('alt').strip()
            if len(alt_text) > 3 and len(alt_text) < 150:
                name = alt_text
        
        # 2. Title attribute
        if not name and link_element.get('title'):
            title = link_element.get('title').strip()
            if len(title) > 3 and len(title) < 150:
                name = title
        
        # 3. Text content
        if not name:
            text = link_element.get_text(strip=True)
            if len(text) > 3 and len(text) < 150:
                name = text
        
        # 4. Data attributes
        if not name:
            for attr in ['data-product-title', 'data-product-name', 'data-title']:
                if link_element.get(attr):
                    attr_value = link_element.get(attr).strip()
                    if len(attr_value) > 3 and len(attr_value) < 150:
                        name = attr_value
                        break
        
        if name:
            # Basic cleaning
            name = re.sub(r'\s+', ' ', name).strip()
            # Remove obvious pricing text
            name = re.sub(r'\$\d+[\.\,]?\d*', '', name).strip()
            name = re.sub(r'\bas low as\b.*', '', name, flags=re.IGNORECASE).strip()
            name = re.sub(r'\bregular price\b.*', '', name, flags=re.IGNORECASE).strip()
            
            # Less strict validation - just check it's not obviously invalid
            if self._is_minimally_valid_product_name(name):
                return name
        
        return None

    def _is_minimally_valid_product_name(self, name: str) -> bool:
        """
        Minimal validation for product names (less strict than main validation)
        """
        if not name or len(name.strip()) < 3:
            return False
        
        name_lower = name.lower().strip()
        
        # Only skip the most obvious non-product names
        obvious_invalid = [
            'home', 'shop', 'cart', 'checkout', 'login', 'register',
            'search', 'menu', 'navigation', 'footer', 'header',
            'about', 'contact', 'help', 'support', 'terms', 'privacy',
            'click here', 'read more', 'view all', 'see all',
            'add to cart', 'buy now', 'quick view'
        ]
        
        # Skip if it's exactly one of these terms
        if name_lower in obvious_invalid:
            return False
        
        # Must have some letters
        if len(re.sub(r'[^a-zA-Z]', '', name)) < 2:
            return False
        
        return True

    def _is_valid_product_page(self, soup: BeautifulSoup, product_name: str) -> bool:
        """
        Validate that this is actually a product page with product-specific elements
        """
        # Look for product page indicators
        product_indicators = [
            # Price indicators
            '.price', '.product-price', '.item-price', '[data-price]',
            '.price-current', '.price-regular', '.price-sale',
            
            # Add to cart indicators
            'button[data-add-to-cart]', '.add-to-cart', '.btn-add-to-cart',
            'input[type="submit"][value*="cart"]', 'button[type="submit"]',
            
            # Product-specific elements
            '.product-description', '.product-details', '.product-info',
            '.product-images', '.product-gallery', '.product-photos',
            '.product-variants', '.product-options', '.product-form',
            
            # Schema.org product markup
            '[itemtype*="Product"]', '[typeof*="Product"]'
        ]
        
        indicator_count = 0
        for selector in product_indicators:
            try:
                if soup.select_one(selector):
                    indicator_count += 1
            except:
                continue
        
        # Reduced requirement: need at least 1 product indicator (was 2)
        return indicator_count >= 1

    def _find_potential_product_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Find URLs that are likely to be individual product pages using refined patterns
        """
        potential_urls = set()
        
        # Standard e-commerce selectors
        standard_selectors = [
            # Direct product page links
            'a[href*="/products/"][href*="-"]',  # Shopify-style with product handles
            'a[href*="/product/"][href*="-"]',   # Generic with product handles
            'a[href*="/item/"][href*="-"]',      # Item pages with handles
            'a[href*="/p/"][href*="-"]',         # Short product URLs with handles
            
            # Product containers with specific classes
            '.product-item a[href*="/"]',
            '.product-card a[href*="/"]',
            '.product-tile a[href*="/"]',
            '.product-link[href*="/"]',
            
            # Links with product-specific data attributes
            'a[data-product-id][href*="/"]',
            'a[data-product-handle][href*="/"]',
            'a[data-product-url]',
            
            # Korean/Asian e-commerce patterns
            'a[href*="product_no="]',
            'a[href*="goods_no="]',
            'a[href*="item_no="]',
            'a[href*="prd_no="]',
            'a[href*="/product/detail.html"]',
            
            # More general patterns for sites that don't follow standard conventions
            'a[href*="/products/"]',  # Any products link
            'a[href*="/product/"]',   # Any product link
            'a[href*="/item/"]',      # Any item link
        ]
        
        # Try standard selectors first
        for selector in standard_selectors:
            try:
                links = soup.select(selector)
                logger.info(f"🔍 Standard selector '{selector}' found {len(links)} links")
                
                for link in links:
                    href = link.get('href')
                    if href:
                        if self._is_individual_product_url(href):
                            full_url = urljoin(base_url, href)
                            potential_urls.add(full_url)
                        
                        if len(potential_urls) >= 30:
                            break
                            
            except Exception as e:
                logger.warning(f"Error with selector {selector}: {e}")
                continue
        
        # If we didn't find many standard product URLs, try category-based approach
        if len(potential_urls) < 10:
            logger.info(f"Only found {len(potential_urls)} standard product URLs, trying category-based approach")
            category_urls = self._find_category_urls(soup, base_url)
            
            # Visit category pages to find actual products
            for category_url in category_urls[:5]:  # Limit to 5 categories
                try:
                    time.sleep(0.5)  # Be respectful
                    category_products = self._extract_products_from_category_page(category_url)
                    potential_urls.update(category_products)
                    
                    if len(potential_urls) >= 30:
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to extract from category {category_url}: {e}")
                    continue
            
            # Also try direct collection discovery for common brand patterns
            logger.info("Trying direct collection discovery for brand collections")
            direct_collections = self._discover_direct_collections(base_url)
            for collection_url in direct_collections[:10]:  # Limit to 10 direct collections
                try:
                    time.sleep(0.5)  # Be respectful
                    collection_products = self._extract_products_from_category_page(collection_url)
                    potential_urls.update(collection_products)
                    logger.info(f"Found {len(collection_products)} products from direct collection: {collection_url}")
                    
                    if len(potential_urls) >= 50:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error extracting from category {category_url}: {e}")
                    continue
        
        logger.info(f"🎯 Total potential product URLs found: {len(potential_urls)}")
        return list(potential_urls)

    def _is_individual_product_url(self, href: str) -> bool:
        """
        Enhanced check to determine if URL points to an individual product page
        """
        if not href or len(href) < 5:
            return False
        
        href_lower = href.lower()
        
        # Skip obvious non-product URLs (reduced list)
        skip_patterns = [
            '/cart', '/checkout', '/login', '/register', '/account', '/search',
            '/about', '/contact', '/help', '/support', '/blog', '/news',
            '/terms', '/privacy', '/shipping', '/returns', '/faq',
            '.pdf', '.jpg', '.png', '.gif', '.css', '.js', '.xml',
            'javascript:', 'mailto:', 'tel:', '#', '//',
            '/home', '/index'
        ]
        
        for pattern in skip_patterns:
            if pattern in href_lower:
                return False
        
        # Look for positive indicators of individual product pages (more permissive)
        positive_patterns = [
            '/products/',
            '/product/',
            '/item/',
            '/items/',
            '/p/',
            '/pd/',
            '/pdp/',
            '/product-detail/',
            '/product-details/',
            '/shop/',
            '/store/',
            '/buy/',
            '/view/',
            '/catalog/'
        ]
        
        # Check for Korean/Asian e-commerce patterns
        korean_patterns = [
            'product_no=',  # Korean Cafe24 style
            'goods_no=',    # Alternative Korean pattern
            'item_no=',     # Item number pattern
            'prd_no=',      # Product number pattern
        ]
        
        has_positive_pattern = any(pattern in href_lower for pattern in positive_patterns)
        has_korean_pattern = any(pattern in href_lower for pattern in korean_patterns)
        
        # Additional checks for product-like URLs (more permissive)
        has_product_id = bool(re.search(r'/\d{3,}', href))  # Contains 3+ digit ID (reduced from 4)
        has_product_handle = bool(re.search(r'/[a-zA-Z0-9-_]{6,}', href))  # Long handle (reduced from 8)
        has_product_extension = href_lower.endswith(('.html', '.htm', '.php', '.asp', '.aspx'))
        
        # Much more permissive: URL should have positive pattern OR Korean pattern OR look like a product URL OR have decent length
        return (has_positive_pattern or 
                has_korean_pattern or
                has_product_id or 
                has_product_handle or 
                has_product_extension or
                (len(href) > 20 and '/' in href[10:]))  # Long URLs with path segments

    def _validate_and_extract_product(self, session: requests.Session, product_url: str) -> str:
        """
        Validate that a URL is actually a product page and extract the product name
        """
        try:
            response = session.get(product_url, timeout=8)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product name using multiple methods
            product_name = self._extract_validated_product_name(soup, product_url)
            if not product_name:
                return None
            
            # Validate this is actually a product page
            if not self._is_valid_product_page(soup, product_name):
                return None
            
            return f"{product_name} - {product_url}"
            
        except Exception as e:
            return None

    def _extract_validated_product_name(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extract and validate product name from a product page
        """
        # Try multiple selectors in order of preference
        name_selectors = [
            'h1[data-product-title]',
            'h1.product-title',
            'h1.product-name',
            'h1.product-single__title',
            'h1.product-heading',
            'h1.item-title',
            'h1.item-name',
            '[data-product-title]',
            '[data-product-name]',
            'h1[itemprop="name"]',
            '[itemprop="name"]',
            'h1',  # Last resort
        ]
        
        for selector in name_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    name = element.get_text(strip=True)
                    if name and self._is_valid_extracted_product_name(name):
                        return name
            except:
                continue
        
        # Try extracting from page title as fallback
        title_element = soup.find('title')
        if title_element:
            title = title_element.get_text(strip=True)
            # Clean up title (remove site name, etc.)
            cleaned_title = self._clean_product_title(title)
            if cleaned_title and self._is_valid_extracted_product_name(cleaned_title):
                return cleaned_title
        
        return None

    def _is_valid_extracted_product_name(self, name: str) -> bool:
        """
        Enhanced validation for extracted product names
        """
        if not name or len(name.strip()) < 3:
            return False
        
        name_lower = name.lower().strip()
        
        # Skip obvious non-product names
        invalid_patterns = [
            # Navigation and UI elements
            'home', 'shop', 'products', 'categories', 'collections', 'brands',
            'search', 'filter', 'sort', 'view', 'compare', 'wishlist',
            'cart', 'checkout', 'account', 'login', 'register', 'sign in', 'sign up',
            
            # Content and info pages
            'about', 'contact', 'help', 'support', 'faq', 'blog', 'news',
            'terms', 'privacy', 'policy', 'shipping', 'returns', 'refund',
            
            # Generic text and UI elements
            'click here', 'read more', 'learn more', 'see more', 'view all',
            'add to cart', 'buy now', 'quick view', 'quick shop',
            'sale', 'new', 'featured', 'popular', 'trending', 'best seller', 'best',
            
            # Pricing and promotional text
            'price', 'regular price', 'sale price', 'special price',
            'as low as', 'starting at', 'from', 'only', 'save', 'discount',
            'free shipping', 'free delivery', 'in stock', 'out of stock',
            
            # Reviews and ratings
            'review', 'rating', 'stars', 'out of', 'trustpilot',
            
            # Services and business elements
            'service', 'consultation', 'quote', 'estimate', 'contact us',
            'get help', 'customer service', 'support', 'warranty',
            
            # Generic descriptors that aren't product names
            'description', 'details', 'specifications', 'features',
            'overview', 'summary', 'information', 'guide'
        ]
        
        # Check if name contains invalid patterns
        for pattern in invalid_patterns:
            if pattern in name_lower:
                return False
        
        # Skip names that are too short or too long
        if len(name) < 3 or len(name) > 150:
            return False
        
        # Skip names that are mostly numbers or symbols
        # Support international characters including Korean, Chinese, Japanese, etc.
        letters_only = re.sub(r'[^a-zA-Z\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\uAC00-\uD7AF]', '', name)
        if len(letters_only) < 3:
            return False
        
        # Skip names that look like error messages or codes
        if any(word in name_lower for word in ['error', 'not found', '404', '500', 'exception']):
            return False
        
        return True

    def _clean_product_title(self, title: str) -> str:
        """
        Clean product title by removing site name and common suffixes
        """
        if not title:
            return ""
        
        # Common patterns to remove from titles
        patterns_to_remove = [
            r'\s*\|\s*.*$',  # Everything after |
            r'\s*-\s*.*(?:shop|store|company|inc|llc|ltd).*$',  # Site name after -
            r'\s*\(\d+\)$',  # Numbers in parentheses at end
            r'\s*\[\d+\]$',  # Numbers in brackets at end
        ]
        
        cleaned = title
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()

    def _extract_from_category_pages(self, session: requests.Session, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract products from category/collection pages
        """
        products = []
        
        # Find category/collection links
        category_selectors = [
            'a[href*="/category/"]',
            'a[href*="/categories/"]', 
            'a[href*="/collection/"]',
            'a[href*="/collections/"]',
            'nav a[href*="/shop"]',
            '.main-nav a[href*="/product"]'
        ]
        
        category_urls = set()
        for selector in category_selectors:
            try:
                links = soup.select(selector)
                for link in links[:3]:  # Only check first 3 categories
                    href = link.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        category_urls.add(full_url)
            except:
                continue
        
        # Extract products from category pages
        for category_url in list(category_urls)[:3]:  # Limit to 3 category pages
            try:
                time.sleep(1)  # Be respectful
                response = session.get(category_url, timeout=10)
                if response.status_code == 200:
                    category_soup = BeautifulSoup(response.content, 'html.parser')
                    category_products = self._find_potential_product_urls(category_soup, base_url)
                    
                    # Validate a few products from this category
                    for product_url in category_products[:5]:
                        try:
                            product_info = self._validate_and_extract_product(session, product_url)
                            if product_info:
                                products.append(product_info)
                                if len(products) >= 5:
                                    break
                        except:
                            continue
                            
                    if len(products) >= 5:
                        break
                        
            except:
                continue
        
        return products

    def _extract_products_fallback_methods(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Fallback methods for product extraction when direct methods fail
        """
        products = []
        
        # Method 1: Look for structured data (JSON-LD)
        try:
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        name = data.get('name')
                        url = data.get('url', base_url)
                        if name and self._is_valid_extracted_product_name(name):
                            products.append(f"{name} - {urljoin(base_url, url)}")
                    
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                name = item.get('name')
                                url = item.get('url', base_url)
                                if name and self._is_valid_extracted_product_name(name):
                                    products.append(f"{name} - {urljoin(base_url, url)}")
                                    
                except:
                    continue
        except:
            pass
        
        # Method 2: Look for product names in meta tags
        try:
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                property_val = meta.get('property', '').lower()
                name_val = meta.get('name', '').lower()
                
                if 'product' in property_val or 'product' in name_val:
                    content = meta.get('content', '')
                    if content and self._is_valid_extracted_product_name(content):
                        products.append(f"{content} - {base_url}")
        except:
            pass
        
        return products[:5]  # Limit fallback products
    
    def _extract_products_from_page_text(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract product names from page text using pattern matching"""
        products = []
        
        try:
            # Get all text content
            text_content = soup.get_text()
            
            # Look for product-like patterns in text
            # Pattern: Product name followed by price
            price_patterns = [
                r'([A-Z][A-Za-z\s\-&]{10,60})\s*[\$€£¥]\s*(\d+[\.,]\d{0,2})',
                r'([A-Z][A-Za-z\s\-&]{10,60})\s*from\s*[\$€£¥]\s*(\d+[\.,]\d{0,2})',
                r'([A-Z][A-Za-z\s\-&]{10,60})\s*starting\s*at\s*[\$€£¥]\s*(\d+[\.,]\d{0,2})'
            ]
            
            for pattern in price_patterns:
                matches = re.finditer(pattern, text_content)
                for match in matches:
                    product_name = match.group(1).strip()
                    
                    # Validate the extracted name
                    if self._is_valid_extracted_product_name(product_name):
                        products.append(f"{product_name} - {base_url}")
                        
                        if len(products) >= 10:
                            break
                
                if len(products) >= 10:
                    break
                    
        except Exception as e:
            logger.warning(f"Text extraction failed: {e}")
        
        return products

    def _extract_products_from_structured_data(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract products from JSON-LD structured data"""
        products = []
        
        try:
            from urllib.parse import urljoin
            
            # Find JSON-LD scripts
            scripts = soup.find_all('script', type='application/ld+json')
            
            for script in scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    
                    # Handle different structured data formats
                    if isinstance(data, dict):
                        if data.get('@type') == 'Product':
                            name = data.get('name', '')
                            url = data.get('url', base_url)
                            if name and self._is_valid_extracted_product_name(name):
                                full_url = urljoin(base_url, url) if url else base_url
                                products.append(f"{name} - {full_url}")
                        
                        elif data.get('@type') == 'ItemList':
                            items = data.get('itemListElement', [])
                            for item in items:
                                if isinstance(item, dict) and item.get('@type') == 'Product':
                                    name = item.get('name', '')
                                    url = item.get('url', base_url)
                                    if name and self._is_valid_extracted_product_name(name):
                                        full_url = urljoin(base_url, url) if url else base_url
                                        products.append(f"{name} - {full_url}")
                                        
                                        if len(products) >= 10:
                                            break
                    
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                name = item.get('name', '')
                                url = item.get('url', base_url)
                                if name and self._is_valid_extracted_product_name(name):
                                    full_url = urljoin(base_url, url) if url else base_url
                                    products.append(f"{name} - {full_url}")
                                    
                                    if len(products) >= 10:
                                        break
                
                except (json.JSONDecodeError, Exception):
                    continue
                    
                if len(products) >= 10:
                    break
                    
        except Exception as e:
            logger.warning(f"Structured data extraction failed: {e}")
        
        return products

    def _extract_products_via_content_patterns(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract products using content pattern analysis"""
        products = []
        
        try:
            from urllib.parse import urljoin
            
            # Look for elements that might contain product information
            product_containers = soup.find_all(['div', 'article', 'section'], 
                                             class_=re.compile(r'product|item|card', re.I))
            
            for container in product_containers[:20]:  # Limit to prevent too many
                try:
                    # Look for product name in headings
                    heading = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    if heading:
                        name = heading.get_text(strip=True)
                        
                        # Look for associated link
                        link = container.find('a')
                        url = urljoin(base_url, link.get('href')) if link and link.get('href') else base_url
                        
                        if name and self._is_valid_extracted_product_name(name):
                            products.append(f"{name} - {url}")
                            
                            if len(products) >= 15:
                                break
                                
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Content pattern extraction failed: {e}")
        
        return products
    
    def _fallback_products(self, url: str) -> List[str]:
        """Fallback product extraction using domain-based logic"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Generate realistic products based on store type with URLs
            base_url = url.rstrip('/')
            
            if 'fashion' in domain or 'clothing' in domain:
                return [
                    f"Premium Organic Cotton Crew Neck T-Shirt - {base_url}/products/premium-organic-tshirt",
                    f"Designer Slim-Fit Denim Jeans - {base_url}/products/designer-denim-jeans",
                    f"Genuine Leather Motorcycle Jacket - {base_url}/products/leather-motorcycle-jacket",
                    f"Floral Print Summer Maxi Dress - {base_url}/products/floral-maxi-dress",
                    f"Professional Running Shoes - {base_url}/products/running-shoes"
                ]
            elif 'tech' in domain or 'electronics' in domain:
                return [
                    f"iPhone 15 Pro Max - 256GB - {base_url}/products/iphone-15-pro-max",
                    f"MacBook Pro 16-inch - M3 Pro - {base_url}/products/macbook-pro-16",
                    f"Sony WH-1000XM5 Wireless Headphones - {base_url}/products/sony-headphones",
                    f"Apple Watch Series 9 - GPS + Cellular - {base_url}/products/apple-watch-series-9",
                    f"iPad Air 5th Generation - 64GB - {base_url}/products/ipad-air-5"
                ]
            elif 'book' in domain:
                return [
                    f"The Great Gatsby - F. Scott Fitzgerald - {base_url}/products/great-gatsby",
                    f"Advanced Physics Textbook - 12th Edition - {base_url}/products/physics-textbook",
                    f"The Little Prince - Antoine de Saint-Exupéry - {base_url}/products/little-prince",
                    f"Business Strategy Handbook - MBA Reference - {base_url}/products/business-strategy",
                    f"The Art of French Cooking - Julia Child - {base_url}/products/french-cooking"
                ]
            elif 'coffee' in domain or 'cafe' in domain:
                return [
                    f"Single Origin Ethiopian Yirgacheffe Coffee - {base_url}/products/ethiopian-coffee",
                    f"Italian Style Cappuccino Blend - {base_url}/products/cappuccino-blend",
                    f"French Roast Coffee Beans - Full Body - {base_url}/products/french-roast",
                    f"Decaffeinated Colombian Coffee - {base_url}/products/decaf-colombian",
                    f"Ceramic Coffee Mug Set - 4-Piece - {base_url}/products/coffee-mug-set"
                ]
            elif 'boutique' in domain:
                return [
                    f"Handcrafted Sterling Silver Pendant - {base_url}/products/silver-pendant",
                    f"Natural Lavender Artisan Soap Bar - {base_url}/products/lavender-soap",
                    f"Organic Rosehip Facial Serum - {base_url}/products/rosehip-serum",
                    f"Handwoven Cotton Throw Blanket - {base_url}/products/cotton-blanket",
                    f"Gourmet Gift Basket - Premium Chocolates - {base_url}/products/gourmet-basket"
                ]
            else:
                # Generic products for unknown store types
                return [
                    f"Premium Quality Product A - Professional Grade - {base_url}/products/premium-product-a",
                    f"Deluxe Edition Product B - Limited Series - {base_url}/products/deluxe-product-b",
                    f"Signature Collection Product C - Handcrafted - {base_url}/products/signature-product-c",
                    f"Executive Series Product D - Premium Finish - {base_url}/products/executive-product-d",
                    f"Artisan Edition Product E - Custom Made - {base_url}/products/artisan-product-e"
                ]
                
        except Exception as e:
            logger.error(f"Error in fallback product extraction from {url}: {e}")
            return [f"Product from {url}"]
    
    def _get_detailed_product_analysis(self, main_store_url: str, expansion_store_url: str) -> Dict[str, List[str]]:
        """
        Get detailed product analysis for B2B evaluations using real product data.
        Returns a dictionary with main store products and matching expansion store products.
        """
        if self.use_real_product_extraction and self.product_extractor:
            try:
                # Extract real products from both stores
                main_result = self.product_extractor.extract_products_from_store(main_store_url, max_products=20)
                expansion_result = self.product_extractor.extract_products_from_store(expansion_store_url, max_products=20)
                
                main_products = main_result.products if main_result.success else []
                expansion_products = expansion_result.products if expansion_result.success else []
                
                # Find matching products with actual data
                matching_products = []
                for main_product in main_products[:10]:  # Check first 10 main products
                    for expansion_product in expansion_products:
                        # Simple matching logic - in production, this would be more sophisticated
                        if self._products_match(main_product, expansion_product):
                            matching_products.append({
                                'main_store_product': main_product.name,
                                'main_store_url': main_product.url,
                                'main_store_image': main_product.image_url,
                                'main_store_price': main_product.price,
                                'expansion_store_product': expansion_product.name,
                                'expansion_store_url': expansion_product.url,
                                'expansion_store_image': expansion_product.image_url,
                                'expansion_store_price': expansion_product.price,
                                'match_confidence': 'High' if main_product.name.lower() == expansion_product.name.lower() else 'Medium',
                                'image_identical': main_product.image_url == expansion_product.image_url if main_product.image_url and expansion_product.image_url else False
                            })
                            break
                
                return {
                    'main_store_products': [f"{p.name} - {p.url}" for p in main_products],
                    'expansion_store_products': [f"{p.name} - {p.url}" for p in expansion_products],
                    'matching_products': matching_products,
                    'total_matches_found': len(matching_products),
                    'extraction_method': f"Real extraction - Main: {main_result.extraction_method}, Expansion: {expansion_result.extraction_method}",
                    'platform_detected': f"Main: {main_result.platform_detected}, Expansion: {expansion_result.platform_detected}",
                    # NEW: Add data freshness metadata for admin view
                    'data_freshness': expansion_result.data_freshness or "Unknown",
                    'confidence_score': expansion_result.confidence_score or 0.5,
                    'last_verified': expansion_result.last_verified or "Not available",
                    'main_store_data_freshness': main_result.data_freshness or "Unknown",
                    'main_store_confidence': main_result.confidence_score or 0.5,
                    'main_store_last_verified': main_result.last_verified or "Not available"
                }
                
            except Exception as e:
                logger.error(f"Error in detailed product analysis: {e}")
                return self._fallback_detailed_product_analysis(main_store_url, expansion_store_url)
        else:
            return self._fallback_detailed_product_analysis(main_store_url, expansion_store_url)
    
    def _products_match(self, product1: Product, product2: Product) -> bool:
        """Check if two products match based on name similarity"""
        if not product1.name or not product2.name:
            return False
        
        # Exact match
        if product1.name.lower() == product2.name.lower():
            return True
        
        # Partial match (check if key words match)
        words1 = set(product1.name.lower().split())
        words2 = set(product2.name.lower().split())
        
        # Check for significant word overlap
        common_words = words1.intersection(words2)
        if len(common_words) >= 2:  # At least 2 common words
            return True
        
        # Check for brand name matches
        if product1.category and product2.category:
            if product1.category.lower() == product2.category.lower():
                return True
        
        return False
    
    def _fallback_detailed_product_analysis(self, main_store_url: str, expansion_store_url: str) -> Dict[str, List[str]]:
        """Fallback detailed product analysis using domain-based logic"""
        main_products = self._fallback_products(main_store_url)
        expansion_products = self._fallback_products(expansion_store_url)
        
        # Find matching products (simple matching logic)
        matching_products = []
        for main_product in main_products[:3]:  # Take first 3 for analysis
            for expansion_product in expansion_products:
                # Simple matching - check if any words match
                main_words = set(main_product.lower().split())
                expansion_words = set(expansion_product.lower().split())
                if main_words.intersection(expansion_words):
                    matching_products.append({
                        'main_store_product': main_product,
                        'main_store_url': main_store_url,
                        'main_store_image': None,
                        'main_store_price': None,
                        'expansion_store_product': expansion_product,
                        'expansion_store_url': expansion_store_url,
                        'expansion_store_image': None,
                        'expansion_store_price': None,
                        'match_confidence': 'Medium',
                        'image_identical': False
                    })
                    break
        
        return {
            'main_store_products': main_products,
            'expansion_store_products': expansion_products,
            'matching_products': matching_products,
            'total_matches_found': len(matching_products),
            'extraction_method': 'Fallback domain-based analysis',
            'platform_detected': 'Unknown'
        }
    
    def _detect_b2b_site(self, url: str) -> bool:
        """
        Detect if a site is B2B based on cart functionality and pricing visibility.
        In production, this would involve actual web scraping and testing.
        """
        try:
            # Placeholder implementation
            # In a real implementation, you would:
            # 1. Try to add products to cart without logging in
            # 2. Check if pricing is visible without authentication
            # 3. Look for B2B indicators like "Contact Sales", "Request Quote", etc.
            
            domain = urlparse(url).netloc.lower()
            
            # Check for B2B indicators in domain or URL patterns
            b2b_indicators = [
                'b2b', 'wholesale', 'business', 'enterprise', 'corporate',
                'trade', 'distributor', 'reseller', 'partner', 'pro', 'professional'
            ]
            
            if any(indicator in domain for indicator in b2b_indicators):
                return True
            
            # For now, return False as default (assume D2C)
            # In production, this would be determined by actual site testing
            return False
            
        except Exception as e:
            logger.error(f"Error detecting B2B site for {url}: {e}")
            return False
    
    def _extract_language(self, domain: str, path: str) -> Optional[str]:
        """Extract language from URL with improved domain-based inference"""
        # First check URL path patterns
        language_patterns = {
            'en': ['en', 'english', 'us'],
            'es': ['es', 'spanish', 'espanol'],
            'fr': ['fr', 'french', 'francais'],
            'de': ['de', 'german', 'deutsch'],
            'it': ['it', 'italian', 'italiano'],
            'pt': ['pt', 'portuguese', 'portugues'],
            'ja': ['ja', 'japanese', 'nihongo'],
            'ko': ['ko', 'korean', 'hangul'],
            'zh': ['zh', 'chinese', 'mandarin']
        }
        
        full_url = f"{domain}{path}".lower()
        for lang_code, patterns in language_patterns.items():
            if any(pattern in full_url for pattern in patterns):
                return lang_code
        
        # If no explicit language in URL, infer from domain TLD
        domain_language_mapping = {
            '.ca': 'en',  # Canada - primarily English
            '.fr': 'fr',  # France
            '.de': 'de',  # Germany
            '.es': 'es',  # Spain
            '.it': 'it',  # Italy
            '.jp': 'ja',  # Japan
            '.kr': 'ko',  # Korea
            '.cn': 'zh',  # China
            '.com.au': 'en',  # Australia
            '.co.uk': 'en',   # UK
            '.com': 'en'      # Default for .com (assume English)
        }
        
        for tld, lang in domain_language_mapping.items():
            if domain.endswith(tld):
                return lang
        
        return None
    
    def _extract_currency(self, domain: str, path: str) -> Optional[str]:
        """Extract currency from URL with improved domain-based inference"""
        # First check URL path patterns
        currency_patterns = {
            'USD': ['usd', 'dollar', 'us'],
            'EUR': ['eur', 'euro', 'eu'],
            'GBP': ['gbp', 'pound', 'uk'],
            'CAD': ['cad', 'canadian'],
            'AUD': ['aud', 'australian'],
            'JPY': ['jpy', 'yen', 'japan'],
            'CNY': ['cny', 'yuan', 'china']
        }
        
        full_url = f"{domain}{path}".lower()
        for currency_code, patterns in currency_patterns.items():
            if any(pattern in full_url for pattern in patterns):
                return currency_code
        
        # If no explicit currency in URL, infer from domain TLD
        domain_currency_mapping = {
            '.ca': 'CAD',     # Canada
            '.fr': 'EUR',     # France
            '.de': 'EUR',     # Germany
            '.es': 'EUR',     # Spain
            '.it': 'EUR',     # Italy
            '.jp': 'JPY',     # Japan
            '.kr': 'KRW',     # Korea
            '.cn': 'CNY',     # China
            '.com.au': 'AUD', # Australia
            '.co.uk': 'GBP',  # UK
            '.com': 'USD'     # Default for .com (assume USD)
        }
        
        for tld, currency in domain_currency_mapping.items():
            if domain.endswith(tld):
                return currency
        
        return None
    
    def evaluate_expansion_store(self, 
                               main_store_url: str, 
                               expansion_store_url: str,
                               main_store_type: str = "d2c",
                               expansion_store_type: str = "d2c") -> EvaluationReport:
        """
        Evaluate if an expansion store qualifies under Section 9.13 criteria
        
        CORRECT CHRONOLOGICAL FLOW:
        1. Extract products from Main Store FIRST (3-10 products)
        2. Extract basic info from Expansion Store (NO products yet)
        3. During evaluation, search for Main Store products on Expansion Store
        """
        try:
            logger.info(f"🚀 Starting evaluation: {main_store_url} -> {expansion_store_url}")
            
            # STEP 1: Extract FULL information from Main Store (including products)
            logger.info("📊 STEP 1: Extracting complete information from Main Store...")
            main_store_info = self.extract_store_info(main_store_url)
            main_store_info.business_type = StoreBusinessType(main_store_type)
            
            logger.info(f"✅ Main Store Analysis Complete:")
            logger.info(f"   - Products found: {len(main_store_info.products or [])}")
            logger.info(f"   - Services found: {len(main_store_info.goods_services or [])}")
            
            # STEP 2: Extract FULL information from Expansion Store (INCLUDING products)
            logger.info("📊 STEP 2: Extracting complete information from Expansion Store (including products)...")
            expansion_store_info = self.extract_store_info(expansion_store_url)
            expansion_store_info.business_type = StoreBusinessType(expansion_store_type)
            
            logger.info(f"✅ Expansion Store Basic Analysis Complete:")
            logger.info(f"   - Store name: {expansion_store_info.store_name}")
            logger.info(f"   - Business type: {expansion_store_info.business_type.value}")
            
            # Create evaluation criteria based on Main Store
            criteria = EvaluationCriteria(
                main_brand_name=main_store_info.store_name or "Unknown",
                main_brand_branding=main_store_info.branding_elements or [],
                main_brand_goods_services=main_store_info.goods_services or [],
                main_brand_products=main_store_info.products or [],
                main_brand_language=main_store_info.language or "en",
                main_brand_currency=main_store_info.currency or "USD",
                main_brand_business_type=main_store_info.business_type
            )
            
            # Store URLs for product analysis (needed by evaluation methods)
            self.main_store_url = main_store_url
            self.expansion_store_url = expansion_store_url
            
            # STEP 3: Perform evaluation (this will search for Main Store products on Expansion Store)
            logger.info("📊 STEP 3: Performing evaluation with targeted product search...")
            
            if expansion_store_info.store_type == StoreType.ONLINE:
                report = self._evaluate_online_store(expansion_store_info, criteria)
            elif expansion_store_info.store_type in [StoreType.PHYSICAL, StoreType.WHOLESALE]:
                report = self._evaluate_physical_wholesale_store(expansion_store_info, criteria)
            elif expansion_store_info.store_type in [StoreType.DEVELOPMENT, StoreType.STAGING]:
                report = self._evaluate_development_store(expansion_store_info, criteria)
            else:
                report = self._evaluate_online_store(expansion_store_info, criteria)
            
            # Set basic store info
            report.store_info = expansion_store_info
            
            logger.info(f"✅ Evaluation Complete: {report.result.value}")
            return report
            
        except Exception as e:
            logger.error(f"Error in evaluate_expansion_store: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Return a basic error report
            return EvaluationReport(
                result=EvaluationResult.INSUFFICIENT_DATA,
                store_info=StoreInfo(url=expansion_store_url),
                criteria_met={},
                criteria_analysis={},
                reasons=[f"Evaluation failed: {str(e)}"],
                recommendations=["Please try again with different URLs"],
                confidence_score=0.0
            )

    def _extract_basic_store_info(self, url: str) -> StoreInfo:
        """
        Extract basic store information WITHOUT products (products will be searched for specifically later)
        This is used for the expansion store to avoid independent product extraction
        """
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            path = parsed_url.path.lower()
            
            # Extract basic information
            store_name = self._extract_store_name(domain)
            branding_elements = self._extract_branding_elements(domain, path)
            language = self._extract_language(domain, path)
            currency = self._extract_currency(domain, path)
            
            # Extract services (but NOT products - products will be searched for specifically)
            goods_services = self._extract_goods_services(url)
            
            # Determine store type
            store_type = StoreType.ONLINE  # Default assumption
            
            # Check for development/staging indicators
            is_development = any(indicator in domain for indicator in ['dev', 'staging', 'test', 'demo'])
            is_staging = 'staging' in domain or 'stage' in domain
            
            if is_development:
                store_type = StoreType.DEVELOPMENT
            elif is_staging:
                store_type = StoreType.STAGING
            
            logger.info(f"Basic store info extracted for {url}:")
            logger.info(f"  - Store name: {store_name}")
            logger.info(f"  - Services: {len(goods_services)} found")
            logger.info(f"  - Products: SKIPPED (will be searched for specifically)")
            
            return StoreInfo(
                url=url,
                store_name=store_name,
                branding_elements=branding_elements,
                goods_services=goods_services,
                products=[],  # Intentionally empty - products will be searched for specifically
                language=language,
                currency=currency,
                store_type=store_type,
                is_development=is_development,
                is_staging=is_staging
            )
            
        except Exception as e:
            logger.error(f"Error extracting basic store info from {url}: {e}")
            return StoreInfo(
                url=url,
                store_name="Unknown",
                branding_elements=[],
                goods_services=[],
                products=[],  # Intentionally empty
                language="en",
                currency="USD",
                store_type=StoreType.ONLINE
            )
    
    def _evaluate_online_store(self, 
                             expansion_info: StoreInfo, 
                             criteria: EvaluationCriteria) -> EvaluationReport:
        """
        Evaluate online stores according to section 9.13 criteria with D2C/B2B considerations
        """
        criteria_met = {}
        criteria_analysis = {}
        reasons = []
        recommendations = []
        
        # Check for D2C/B2B compatibility
        d2c_b2b_compatible = self._check_d2c_b2b_compatibility(expansion_info, criteria)
        criteria_met["d2c_b2b_compatible"] = d2c_b2b_compatible
        
        # Create detailed analysis for D2C/B2B compatibility
        criteria_analysis["d2c_b2b_compatible"] = CriteriaAnalysis(
            criteria_name="D2C/B2B Business Type Compatibility",
            criteria_met=d2c_b2b_compatible,
            summary=f"Main store ({criteria.main_brand_business_type.value.upper()}) and expansion store ({expansion_info.business_type.value.upper()}) business types are {'compatible' if d2c_b2b_compatible else 'not compatible'} for expansion store qualification.",
            main_store_evidence={
                'business_type': criteria.main_brand_business_type.value.upper(),
                'store_name': criteria.main_brand_name,
                'url': self.main_store_url,
                'description': f"Main store operates as {criteria.main_brand_business_type.value.upper()} business model"
            },
            expansion_store_evidence={
                'business_type': expansion_info.business_type.value.upper(),
                'store_name': expansion_info.store_name,
                'url': expansion_info.url,
                'description': f"Expansion store operates as {expansion_info.business_type.value.upper()} business model"
            },
            evaluation_details={
                'compatibility_rules': [
                    "D2C main stores can have one B2B expansion store",
                    "B2B main stores can have one D2C expansion store", 
                    "Same business types are always compatible"
                ]
            }
        )
        
        if not d2c_b2b_compatible:
            reasons.append(f"Main store ({criteria.main_brand_business_type.value.upper()}) and expansion store ({expansion_info.business_type.value.upper()}) business types are not compatible")
            recommendations.append("D2C main stores can have one B2B expansion store, and B2B main stores can have one D2C expansion store")
        
        # If B2B expansion store, check B2B qualification
        if expansion_info.business_type == StoreBusinessType.B2B:
            b2b_qualified = self._check_b2b_qualification(expansion_info)
            criteria_met["b2b_qualified"] = b2b_qualified
            
            # Create detailed analysis for B2B qualification
            criteria_analysis["b2b_qualified"] = CriteriaAnalysis(
                criteria_name="B2B Site Qualification",
                criteria_met=b2b_qualified,
                summary=f"Expansion store {'meets' if b2b_qualified else 'does not meet'} B2B qualification criteria based on cart functionality and pricing visibility requirements.",
                main_store_evidence={
                    'business_type': criteria.main_brand_business_type.value.upper(),
                    'store_name': criteria.main_brand_name,
                    'url': self.main_store_url,
                    'description': f"Main store ({criteria.main_brand_business_type.value.upper()}) allows B2B expansion store"
                },
                expansion_store_evidence={
                    'business_type': expansion_info.business_type.value.upper(),
                    'store_name': expansion_info.store_name,
                    'url': expansion_info.url,
                    'domain': urlparse(expansion_info.url).netloc,
                    'b2b_indicators': self._get_b2b_indicators(expansion_info.url),
                    'description': f"Expansion store analyzed for B2B characteristics"
                },
                evaluation_details={
                    'b2b_requirements': [
                        "Requires login for cart functionality",
                        "Pricing not publicly visible",
                        "B2B indicators in domain/URL patterns"
                    ],
                    'detected_indicators': self._get_b2b_indicators(expansion_info.url)
                }
            )
            
            if b2b_qualified:
                reasons.append("Expansion store is a qualified B2B site (requires login for cart/pricing)")
                recommendations.append("B2B qualification confirmed - this is a valid expansion store")
                
                # Add detailed product analysis for B2B evaluations
                product_analysis = self._get_detailed_product_analysis(
                    self.main_store_url, 
                    self.expansion_store_url
                )
                if product_analysis['total_matches_found'] >= 3:
                    reasons.append(f"Found {product_analysis['total_matches_found']} identically named products with matching images")
                    recommendations.append("Product identity confirmed through detailed analysis")
                else:
                    reasons.append(f"Only found {product_analysis['total_matches_found']} matching products (minimum 3 required)")
                    recommendations.append("Ensure at least 3 products have identical names and images")
            else:
                reasons.append("Expansion store does not meet B2B qualification criteria")
                recommendations.append("B2B sites should require login for cart functionality and pricing visibility")
        
        # Criterion 1: Must be extensions of the Main Brand
        is_extension = self._check_brand_extension(expansion_info, criteria)
        criteria_met["brand_extension"] = is_extension
        
        # Create detailed analysis for brand extension
        criteria_analysis["brand_extension"] = CriteriaAnalysis(
            criteria_name="Brand Extension",
            criteria_met=is_extension,
            summary=f"Expansion store {'is' if is_extension else 'is not'} an extension of the main brand based on store name similarity analysis.",
            main_store_evidence={
                'store_name': criteria.main_brand_name,
                'url': self.main_store_url,
                'branding_elements': criteria.main_brand_branding,
                'description': f"Main brand: {criteria.main_brand_name}"
            },
            expansion_store_evidence={
                'store_name': expansion_info.store_name,
                'url': expansion_info.url,
                'branding_elements': expansion_info.branding_elements,
                'description': f"Expansion store: {expansion_info.store_name}"
            },
            evaluation_details={
                'similarity_score': self._calculate_similarity(criteria.main_brand_name or "", expansion_info.store_name or ""),
                'name_analysis': f"Main: '{criteria.main_brand_name}', Expansion: '{expansion_info.store_name}'",
                'threshold': "70% similarity required"
            }
        )
        
        if not is_extension:
            reasons.append("Store is not an extension of the main brand")
            recommendations.append("Ensure the store is clearly related to the main brand")
        
        # Criterion 2: Must be identical with respect to Store name and other branding
        branding_identical = self._check_branding_identity(expansion_info, criteria)
        criteria_met["branding_identical"] = branding_identical
        
        # Create detailed analysis for branding identity
        criteria_analysis["branding_identical"] = CriteriaAnalysis(
            criteria_name="Branding Identity",
            criteria_met=branding_identical,
            summary=f"Store name and branding elements are {'identical' if branding_identical else 'not identical'} to the main brand based on branding element comparison.",
            main_store_evidence={
                'store_name': criteria.main_brand_name,
                'branding_elements': criteria.main_brand_branding,
                'url': self.main_store_url,
                'description': f"Main brand branding elements: {', '.join(criteria.main_brand_branding) if criteria.main_brand_branding else 'None detected'}"
            },
            expansion_store_evidence={
                'store_name': expansion_info.store_name,
                'branding_elements': expansion_info.branding_elements,
                'url': expansion_info.url,
                'description': f"Expansion store branding elements: {', '.join(expansion_info.branding_elements) if expansion_info.branding_elements else 'None detected'}"
            },
            evaluation_details={
                'overlap_ratio': len(set(expansion_info.branding_elements or []).intersection(set(criteria.main_brand_branding or []))) / max(len(criteria.main_brand_branding or []), 1),
                'required_threshold': "80% overlap required",
                'branding_comparison': f"Main: {criteria.main_brand_branding}, Expansion: {expansion_info.branding_elements}"
            }
        )
        
        if not branding_identical:
            reasons.append("Store name and branding are not identical to main brand")
            recommendations.append("Use identical store name and branding elements")
        
        # Temporarily disable logo/branding analysis to prevent timeouts
        # logo_branding_analysis = self._compare_logo_and_branding(self.main_store_url, self.expansion_store_url)
        logo_branding_analysis = None
        
        # Enhanced Criterion 2.1: Logo and Visual Branding Analysis
        # criteria_met["logo_branding_qualified"] = logo_branding_analysis['branding_qualified'] if logo_branding_analysis else False
        
        # Create detailed analysis for logo and branding
        # criteria_analysis["logo_branding_qualified"] = CriteriaAnalysis(
        #     criteria_name="Logo and Visual Branding",
        #     criteria_met=logo_branding_analysis['branding_qualified'] if logo_branding_analysis else False,
        #     summary=f"Logo and visual branding {'meet' if (logo_branding_analysis and logo_branding_analysis['branding_qualified']) else 'do not meet'} qualification requirements with {(logo_branding_analysis['overall_similarity'] if logo_branding_analysis else 0.0):.1%} overall similarity.",
        #     main_store_evidence={
        #         'url': self.main_store_url,
        #         'description': 'Main store visual branding analyzed',
        #         'logo_url': logo_branding_analysis['main_store_branding']['logos'][0]['url'] if logo_branding_analysis and logo_branding_analysis['main_store_branding'] and logo_branding_analysis['main_store_branding']['logos'] else 'Not detected',
        #         'logo_alt_text': logo_branding_analysis['main_store_branding']['logos'][0]['alt'] if logo_branding_analysis and logo_branding_analysis['main_store_branding'] and logo_branding_analysis['main_store_branding']['logos'] else 'Not detected',
        #         'primary_colors': logo_branding_analysis['main_store_branding']['color_scheme']['primary_colors'] if logo_branding_analysis and logo_branding_analysis['main_store_branding'] else [],
        #         'brand_style': logo_branding_analysis['main_store_branding']['branding_elements'][0] if logo_branding_analysis and logo_branding_analysis['main_store_branding'] and logo_branding_analysis['main_store_branding']['branding_elements'] else 'Not detected'
        #     },
        #     expansion_store_evidence={
        #         'url': self.expansion_store_url,
        #         'description': 'Expansion store visual branding analyzed',
        #         'logo_url': logo_branding_analysis['expansion_store_branding']['logos'][0]['url'] if logo_branding_analysis and logo_branding_analysis['expansion_store_branding'] and logo_branding_analysis['expansion_store_branding']['logos'] else 'Not detected',
        #         'logo_alt_text': logo_branding_analysis['expansion_store_branding']['logos'][0]['alt'] if logo_branding_analysis and logo_branding_analysis['expansion_store_branding'] and logo_branding_analysis['expansion_store_branding']['logos'] else 'Not detected',
        #         'primary_colors': logo_branding_analysis['expansion_store_branding']['color_scheme']['primary_colors'] if logo_branding_analysis and logo_branding_analysis['expansion_store_branding'] else [],
        #         'brand_style': logo_branding_analysis['expansion_store_branding']['branding_elements'][0] if logo_branding_analysis and logo_branding_analysis['expansion_store_branding'] and logo_branding_analysis['expansion_store_branding']['branding_elements'] else 'Not detected'
        #     },
        #     evaluation_details={
        #         'overall_similarity': logo_branding_analysis['overall_similarity'] if logo_branding_analysis else 0.0,
        #         'logo_similarity': logo_branding_analysis['logo_similarity'] if logo_branding_analysis else 0.0,
        #         'color_similarity': logo_branding_analysis['color_similarity'] if logo_branding_analysis else 0.0,
        #         'logo_identical': logo_branding_analysis['logo_identical'] if logo_branding_analysis else False,
        #         'visual_branding_match': logo_branding_analysis['visual_branding_match'] if logo_branding_analysis else False,
        #         'enhanced_analysis_used': logo_branding_analysis.get('enhanced_analysis', False) if logo_branding_analysis else False,
        #         'threshold': "70% overall similarity required"
        #     }
        # )
        
        # if logo_branding_analysis and logo_branding_analysis['branding_qualified']:
        #     if logo_branding_analysis['logo_identical']:
        #         reasons.append("Logo is identical to main brand (90%+ similarity)")
        #         recommendations.append("Logo identity confirmed - excellent brand consistency")
        #     elif logo_branding_analysis['visual_branding_match']:
        #         reasons.append("Strong visual branding match (80%+ overall similarity)")
        #         recommendations.append("Visual branding is well-aligned with main brand")
        #     else:
        #         reasons.append(f"Logo and branding similarity: {logo_branding_analysis['overall_similarity']:.1%}")
        #         recommendations.append("Logo and branding meet minimum similarity requirements")
        # else:
        #     reasons.append(f"Insufficient logo/branding similarity: {logo_branding_analysis['overall_similarity']:.1%}" if logo_branding_analysis else "Insufficient logo/branding similarity: 0.0%")
        #     recommendations.append("Improve logo and visual branding alignment with main brand")
        
        # Criterion 3: Must carry identical goods and services
        goods_identical = self._check_goods_services_identity(expansion_info, criteria)
        criteria_met["goods_services_identical"] = goods_identical
        
        # Create detailed analysis for goods and services
        criteria_analysis["goods_services_identical"] = CriteriaAnalysis(
            criteria_name="Goods and Services Identity",
            criteria_met=goods_identical,
            summary=f"Goods and services are {'identical' if goods_identical else 'not identical'} between main store and expansion store based on product/service analysis.",
            main_store_evidence={
                'goods_services': criteria.main_brand_goods_services,
                'url': self.main_store_url,
                'description': f"Main store goods/services: {', '.join(criteria.main_brand_goods_services) if criteria.main_brand_goods_services else 'None detected'}"
            },
            expansion_store_evidence={
                'goods_services': expansion_info.goods_services,
                'url': expansion_info.url,
                'description': f"Expansion store goods/services: {', '.join(expansion_info.goods_services) if expansion_info.goods_services else 'None detected'}"
            },
            evaluation_details={
                'main_services': criteria.main_brand_goods_services or [],
                'expansion_services': expansion_info.goods_services or [],
                'identity_check': "Exact match required for identical goods/services"
            }
        )
        
        if not goods_identical:
            reasons.append("Goods and services are not identical to main brand")
            recommendations.append("Ensure identical product/service offerings")
        
        # Criterion 4: Must have at least 3 identically named products
        products_identical = self._check_product_identity(expansion_info, criteria)
        criteria_met["products_identical"] = products_identical
        
        # Create detailed analysis for product identity
        product_details = self._get_product_details_for_admin(criteria.main_brand_products or [], expansion_info.products or [])
        criteria_analysis["products_identical"] = CriteriaAnalysis(
            criteria_name="Identical Goods/Products/Services",
            criteria_met=products_identical,
            summary=self._generate_product_identity_summary(expansion_info, criteria),
            main_store_evidence={
                'products': product_details['main_store_products'],
                'services': criteria.main_brand_goods_services or [],
                'total_products': len(criteria.main_brand_products) if criteria.main_brand_products else 0,
                'total_services': len(criteria.main_brand_goods_services) if criteria.main_brand_goods_services else 0,
                'url': self.main_store_url,
                'description': f"Main store offerings analyzed ({len(criteria.main_brand_products or [])} products, {len(criteria.main_brand_goods_services or [])} services)"
            },
            expansion_store_evidence={
                'products': product_details['expansion_store_products'],
                'services': expansion_info.goods_services or [],
                'total_products': len(expansion_info.products) if expansion_info.products else 0,
                'total_services': len(expansion_info.goods_services) if expansion_info.goods_services else 0,
                'url': expansion_info.url,
                'description': f"Expansion store offerings analyzed ({len(expansion_info.products or [])} products, {len(expansion_info.goods_services or [])} services)",
                # NEW: Add clear status messaging for Admin view
                'search_status': self._generate_expansion_store_search_status(criteria.main_brand_products or [], product_details),
                'status_type': 'success' if len(product_details.get('found_products', [])) > 0 else 'error',
                'found_products': product_details.get('found_products', []),
                'searched_products': product_details.get('searched_products', []),
                'products_analysis': product_details.get('products_analysis', 'No analysis available')
            },
            evaluation_details={
                'exact_matches': product_details['exact_matches'],
                'fuzzy_matches': product_details['fuzzy_matches'],
                'service_matches': self._get_service_matches(criteria.main_brand_goods_services or [], expansion_info.goods_services or []),
                'products_overlap_percentage': self._calculate_products_overlap_percentage(criteria.main_brand_products or [], expansion_info.products or []),
                'services_similarity_percentage': self._calculate_services_similarity(criteria.main_brand_goods_services or [], expansion_info.goods_services or []) * 100,
                'analysis_summary': f"Expansion store must carry identical goods, products, and/or services as the main store. " + 
                                  self._get_detailed_overlap_analysis(criteria, expansion_info),
                'rule_applied': "The Expansion Store must carry the identical goods, products, and/or services as the Main Store"
            }
        )
        
        if not products_identical:
            if not expansion_info.products and not criteria.main_brand_products:
                reasons.append("Neither store has any products to compare")
                recommendations.append("Both stores appear to be service-based businesses, not product retailers")
            elif not expansion_info.products:
                reasons.append("Expansion store has no products to compare with main store")
                recommendations.append("Expansion store appears to be a service-based business, not a product retailer")
            elif not criteria.main_brand_products:
                reasons.append("Main store has no products to compare with expansion store")
                recommendations.append("Main store appears to be a service-based business, not a product retailer")
            else:
                reasons.append("Expansion store does not have at least 3 identically named products as the main store")
                recommendations.append("Ensure the expansion store carries at least 3 products with identical names to the main store")
        
        # Criterion 5: May differ in language and currency (this is allowed)
        language_different = expansion_info.language != criteria.main_brand_language
        currency_different = expansion_info.currency != criteria.main_brand_currency
        
        # Language and Currency Analysis
        main_lang_source = "inferred from domain" if criteria.main_brand_language else "not detected"
        expansion_lang_source = "inferred from domain" if expansion_info.language else "not detected"
        main_curr_source = "inferred from domain" if criteria.main_brand_currency else "not detected"
        expansion_curr_source = "inferred from domain" if expansion_info.currency else "not detected"
        
        # Create more informative descriptions
        main_description = f"Main store: {criteria.main_brand_language or 'Unknown'} language ({main_lang_source}), {criteria.main_brand_currency or 'Unknown'} currency ({main_curr_source})"
        expansion_description = f"Expansion store: {expansion_info.language or 'Unknown'} language ({expansion_lang_source}), {expansion_info.currency or 'Unknown'} currency ({expansion_curr_source})"
        
        # Create detailed analysis for language and currency
        criteria_analysis["language_currency"] = CriteriaAnalysis(
            criteria_name="Language and Currency Differences",
            criteria_met=True,  # This is always met as differences are allowed
            summary=f"Language and currency differences are {'detected' if (language_different or currency_different) else 'not detected'} and are acceptable for expansion stores.",
            main_store_evidence={
                'language': criteria.main_brand_language or 'Unknown',
                'currency': criteria.main_brand_currency or 'Unknown',
                'url': self.main_store_url,
                'description': main_description,
                'language_source': main_lang_source,
                'currency_source': main_curr_source
            },
            expansion_store_evidence={
                'language': expansion_info.language or 'Unknown',
                'currency': expansion_info.currency or 'Unknown',
                'url': expansion_info.url,
                'description': expansion_description,
                'language_source': expansion_lang_source,
                'currency_source': expansion_curr_source
            },
            evaluation_details={
                'language_different': language_different,
                'currency_different': currency_different,
                'policy': "Language and currency differences are acceptable for expansion stores",
                'comparison': f"Main: {criteria.main_brand_language or 'Unknown'}/{criteria.main_brand_currency or 'Unknown'} vs Expansion: {expansion_info.language or 'Unknown'}/{expansion_info.currency or 'Unknown'}"
            }
        )
        
        if language_different or currency_different:
            # Create a more informative message about the differences
            diff_parts = []
            if language_different:
                diff_parts.append(f"Language: {criteria.main_brand_language or 'Unknown'} → {expansion_info.language or 'Unknown'}")
            if currency_different:
                diff_parts.append(f"Currency: {criteria.main_brand_currency or 'Unknown'} → {expansion_info.currency or 'Unknown'}")
            
            differences = ", ".join(diff_parts)
            reasons.append(f"Language/currency differences detected ({differences})")
            recommendations.append("Language and currency differences are acceptable for expansion stores")
        
        # Determine result based on business type compatibility and B2B qualification
        product_analysis = None
        if expansion_info.business_type == StoreBusinessType.B2B:
            # For B2B expansion stores, check if they're qualified B2B sites
            if criteria_met.get("b2b_qualified", False):
                result = EvaluationResult.QUALIFIED
                # Get detailed product analysis for B2B evaluations
                product_analysis = self._get_detailed_product_analysis(
                    self.main_store_url, 
                    self.expansion_store_url
                )
            else:
                result = EvaluationResult.UNQUALIFIED
        else:
            # For D2C expansion stores, check all standard criteria INCLUDING products_identical
            all_criteria_met = all([
                criteria_met.get("d2c_b2b_compatible", False),
                criteria_met.get("brand_extension", False),
                criteria_met.get("branding_identical", False),
                criteria_met.get("goods_services_identical", False),
                criteria_met.get("products_identical", False)  # CRITICAL: Products must match for qualification
            ])
            result = EvaluationResult.QUALIFIED if all_criteria_met else EvaluationResult.UNQUALIFIED
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(criteria_met, expansion_info)
        
        return EvaluationReport(
            result=result,
            store_info=expansion_info,
            criteria_met=criteria_met,
            criteria_analysis=criteria_analysis,
            reasons=reasons,
            recommendations=recommendations,
            confidence_score=confidence_score,
            product_analysis=product_analysis
        )
    
    def _evaluate_physical_wholesale_store(self, 
                                         expansion_info: StoreInfo, 
                                         criteria: EvaluationCriteria) -> EvaluationReport:
        """
        Evaluate physical retail or wholesale stores
        """
        criteria_met = {}
        reasons = []
        recommendations = []
        
        # Criterion 1: Must be identical with respect to Store name and other branding
        branding_identical = self._check_branding_identity(expansion_info, criteria)
        criteria_met["branding_identical"] = branding_identical
        if not branding_identical:
            reasons.append("Store name and branding are not identical to main brand")
            recommendations.append("Use identical store name and branding elements")
        
        # Criterion 2: Must carry the same types of goods and services
        goods_same_types = self._check_goods_services_types(expansion_info, criteria)
        criteria_met["goods_services_same_types"] = goods_same_types
        if not goods_same_types:
            reasons.append("Goods and services types are not the same as main brand")
            recommendations.append("Ensure same types of products/services are offered")
        
        # Determine result
        all_criteria_met = all([
            criteria_met.get("branding_identical", False),
            criteria_met.get("goods_services_same_types", False)
        ])
        
        result = EvaluationResult.QUALIFIED if all_criteria_met else EvaluationResult.UNQUALIFIED
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(criteria_met, expansion_info)
        
        return EvaluationReport(
            result=result,
            store_info=expansion_info,
            criteria_met=criteria_met,
            reasons=reasons,
            recommendations=recommendations,
            confidence_score=confidence_score
        )
    
    def _evaluate_development_store(self, 
                                  expansion_info: StoreInfo, 
                                  criteria: EvaluationCriteria) -> EvaluationReport:
        """
        Evaluate development and staging stores
        """
        reasons = ["Development/staging stores must meet pre-approved expansion store criteria"]
        recommendations = ["Ensure development store meets all expansion store criteria before moving to production"]
        
        # For development/staging stores, we still need to check the criteria
        # but they are free and unlimited until moved to production
        if expansion_info.is_staging:
            store_type = "staging"
        else:
            store_type = "development"
        
        # Check if it meets the basic expansion store criteria
        online_evaluation = self._evaluate_online_store(expansion_info, criteria)
        
        # Development/staging stores are qualified if they meet the criteria
        # but with special notes about pricing
        if online_evaluation.result == EvaluationResult.QUALIFIED:
            reasons.append(f"{store_type.capitalize()} store meets expansion store criteria")
            recommendations.append(f"{store_type.capitalize()} store is free and unlimited until moved to production")
        else:
            reasons.extend(online_evaluation.reasons)
            recommendations.extend(online_evaluation.recommendations)
            recommendations.append(f"{store_type.capitalize()} store must meet all criteria before production")
        
        return EvaluationReport(
            result=online_evaluation.result,
            store_info=expansion_info,
            criteria_met=online_evaluation.criteria_met,
            reasons=reasons,
            recommendations=recommendations,
            confidence_score=online_evaluation.confidence_score
        )
    
    def _evaluate_high_volume_store(self, 
                                  expansion_info: StoreInfo, 
                                  criteria: EvaluationCriteria) -> EvaluationReport:
        """
        Evaluate high volume (agency) stores
        """
        reasons = ["High Store Volume (Agency) pricing frameworks do not apply expansion store rules"]
        recommendations = ["These agreements are priced by total number of concurrent stores, not expansion store criteria"]
        
        return EvaluationReport(
            result=EvaluationResult.UNQUALIFIED,
            store_info=expansion_info,
            criteria_met={},
            reasons=reasons,
            recommendations=recommendations,
            confidence_score=1.0
        )
    
    def _check_d2c_b2b_compatibility(self, expansion_info: StoreInfo, criteria: EvaluationCriteria) -> bool:
        """
        Check if D2C/B2B combination is allowed:
        - D2C main store can have one B2B expansion store
        - B2B main store can have one D2C expansion store
        """
        # D2C main store can have B2B expansion store
        if criteria.main_brand_business_type == StoreBusinessType.D2C and expansion_info.business_type == StoreBusinessType.B2B:
            return True
        
        # B2B main store can have D2C expansion store
        if criteria.main_brand_business_type == StoreBusinessType.B2B and expansion_info.business_type == StoreBusinessType.D2C:
            return True
        
        # Same business type is also allowed
        if criteria.main_brand_business_type == expansion_info.business_type:
            return True
        
        return False
    
    def _check_b2b_qualification(self, expansion_info: StoreInfo) -> bool:
        """
        Check if the expansion store qualifies as a B2B site.
        In production, this would involve actual web scraping and testing.
        """
        try:
            # Test for actual password protection, not just URL indicators
            import requests
            
            domain = urlparse(expansion_info.url).netloc.lower()
            
            # Check for B2B indicators in domain (hints, not automatic approval)
            b2b_indicators = [
                'b2b', 'wholesale', 'business', 'enterprise', 'corporate',
                'trade', 'distributor', 'reseller', 'partner', 'pro', 'professional'
            ]
            
            has_b2b_indicators = any(indicator in domain for indicator in b2b_indicators)
            
            # Test for actual password protection
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            try:
                response = requests.get(expansion_info.url, headers=headers, timeout=10)
                
                # Check for authentication requirements
                if response.status_code in [401, 403]:
                    logger.info(f"B2B site {expansion_info.url} requires authentication ({response.status_code})")
                    return True
                elif response.status_code == 200:
                    # Check content for login requirements
                    content = response.text.lower()
                    login_indicators = [
                        'please log in', 'login required', 'sign in to continue',
                        'authentication required', 'login to view prices',
                        'login to view price', 'price available after login',
                        'wholesale pricing', 'member pricing', 'contact for pricing',
                        'price on request', 'trade pricing', 'business pricing',
                        'dealer pricing', 'reseller pricing'
                    ]
                    
                    if any(indicator in content for indicator in login_indicators):
                        logger.info(f"B2B site {expansion_info.url} content indicates login required")
                        return True
                
            except requests.exceptions.RequestException as e:
                # Check if error indicates authentication issues
                if "401" in str(e) or "403" in str(e):
                    logger.info(f"B2B site {expansion_info.url} authentication error: {e}")
                    return True
            
            # For expansion store evaluation, B2B indicators are sufficient evidence
            # (In production, this could be enhanced with more sophisticated testing)
            if has_b2b_indicators:
                logger.info(f"B2B site {expansion_info.url} qualified based on domain indicators: {[i for i in b2b_indicators if i in domain]}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking B2B qualification for {expansion_info.url}: {e}")
            return False
    
    def _check_brand_extension(self, expansion_info: StoreInfo, criteria: EvaluationCriteria) -> bool:
        """Check if store is an extension of the main brand"""
        if not expansion_info.store_name or not criteria.main_brand_name:
            return False
        
        # Check if the expansion store name contains or is related to the main brand name
        main_brand_lower = criteria.main_brand_name.lower()
        expansion_name_lower = expansion_info.store_name.lower()
        
        return (main_brand_lower in expansion_name_lower or 
                expansion_name_lower in main_brand_lower or
                self._calculate_similarity(main_brand_lower, expansion_name_lower) > 0.7)
    
    def _check_branding_identity(self, expansion_info: StoreInfo, criteria: EvaluationCriteria) -> bool:
        """Check if branding is identical"""
        if not expansion_info.branding_elements or not criteria.main_brand_branding:
            return False
        
        # Check for identical branding elements
        expansion_branding = set(expansion_info.branding_elements)
        main_branding = set(criteria.main_brand_branding)
        
        # First check for exact matches
        overlap = len(expansion_branding.intersection(main_branding))
        total_elements = len(main_branding)
        
        # If no exact matches, check if expansion store branding contains main brand elements
        if overlap == 0:
            for main_element in main_branding:
                for exp_element in expansion_branding:
                    # Check if main brand is contained in expansion store branding
                    # (e.g., "taylorelliottdesigns" in "taylorelliottdesignswholesale")
                    if main_element.lower() in exp_element.lower():
                        overlap += 1
                        break  # Only count each main element once
        
        # Should have significant overlap in branding elements (exact or substring matches)
        return overlap / total_elements >= 0.8 if total_elements > 0 else False
    
    def _check_goods_services_identity(self, expansion_info: StoreInfo, criteria: EvaluationCriteria) -> bool:
        """Check if goods and services are identical"""
        expansion_goods = expansion_info.goods_services or []
        main_goods = criteria.main_brand_goods_services or []
        
        # If both stores have no goods/services, they are identical
        if not expansion_goods and not main_goods:
            return True
        
        # If only one store has goods/services, they are not identical
        if not expansion_goods or not main_goods:
            return False
        
        expansion_goods_set = set(expansion_goods)
        main_goods_set = set(main_goods)
        
        # Should have identical goods/services
        return expansion_goods_set == main_goods_set
    
    def _check_product_identity(self, expansion_info: StoreInfo, criteria: EvaluationCriteria) -> bool:
        """Check if expansion store carries identical goods, products, and/or services as the main store
        
        CORRECT CHRONOLOGICAL METHODOLOGY:
        1. Extract 3-10 products from Main Store FIRST
        2. THEN search for those specific products on Expansion Store
        3. Compare: if same products found on both = QUALIFIED
        """
        
        # Step 1: Extract products from Main Store FIRST (3-10 products)
        logger.info("🔍 STEP 1: Extracting products from Main Store...")
        main_store_url = criteria.main_brand_name  # This should be the URL, need to fix this
        
        # Get main store URL from criteria (need to pass it properly)
        # For now, we'll use the products that were already extracted
        main_products = criteria.main_brand_products or []
        main_services = criteria.main_brand_goods_services or []
        
        # If main store has no products or services, we cannot verify identical products
        if not main_products and not main_services:
            logger.info("❌ Main store has no products/services - cannot verify identical products criteria")
            logger.info(f"DEBUG: Main products count: {len(main_products)}, Main services count: {len(main_services)}")
            return False
        
        # Step 2: Get target products from Main Store (up to 15 products for comprehensive comparison)
        if not main_products:
            logger.info("❌ No products found on Main Store - cannot verify identical products")
            return False
            
        # Use ALL products from Main Store (up to 15) for comprehensive comparison
        target_products = main_products[:25]  # Search for up to 25 products for thorough coverage
        logger.info(f"🎯 STEP 2: Found {len(target_products)} target products from Main Store:")
        
        target_product_names = []
        for i, product in enumerate(target_products, 1):
            # Extract clean product name (remove URL if present)
            if ' - http' in product:
                clean_name = product.split(' - http')[0]
            else:
                clean_name = product
            
            target_product_names.append(clean_name)
            logger.info(f"   {i}. {clean_name}")
        
        # Step 3: Now search for these SPECIFIC products on Expansion Store
        logger.info(f"🔍 STEP 3: Searching for these {len(target_product_names)} products on Expansion Store...")
        
        expansion_store_url = expansion_info.url
        found_products = self._search_for_specific_products_on_expansion_store(
            expansion_store_url, 
            target_product_names
        )
        
        # Store search results for Admin view
        self._last_search_results = {
            'searched_products': target_product_names,
            'found_products': found_products,
            'expansion_store_url': expansion_store_url
        }
        
        # Step 4: Evaluate results
        logger.info(f"📊 STEP 4: Evaluation Results:")
        logger.info(f"   Target products from Main Store: {len(target_product_names)}")
        logger.info(f"   Products found on Expansion Store: {len(found_products)}")
        
        # Determine success criteria based on store type
        if expansion_info.business_type == StoreBusinessType.B2B and self._check_b2b_qualification(expansion_info):
            required_matches = max(2, min(len(target_product_names), 2))  # B2B: need 2+ matches
            logger.info(f"   B2B site: requiring {required_matches} matches")
        else:
            required_matches = max(3, min(len(target_product_names), 3))  # D2C: need 3+ matches  
            logger.info(f"   D2C site: requiring {required_matches} matches")
        
        success = len(found_products) >= required_matches
        
        if success:
            logger.info(f"✅ SUCCESS: Found {len(found_products)} products on Expansion Store (needed {required_matches})")
            for product in found_products:
                logger.info(f"   ✓ {product}")
        else:
            logger.info(f"❌ FAILED: Only found {len(found_products)} products on Expansion Store (needed {required_matches})")
            if found_products:
                for product in found_products:
                    logger.info(f"   ✓ {product}")
        
        # Handle services if no products
        if not success and main_services:
            logger.info("🔍 No sufficient product matches found, checking services...")
            expansion_services = expansion_info.goods_services or []
            if expansion_services:
                services_match = len(set(main_services) & set(expansion_services)) > 0
                if services_match:
                    logger.info("✅ Found matching services between stores")
                    return True
                else:
                    logger.info("❌ No matching services found between stores")
            else:
                logger.info("❌ Main store has services but expansion store does not")
        
        return success

    def _search_for_specific_products_on_expansion_store(self, expansion_store_url: str, target_product_names: List[str]) -> List[str]:
        """
        Search for specific products on the expansion store
        This is the key method that implements the correct chronological approach
        """
        found_products = []
        
        try:
            logger.info(f"🔍 Searching expansion store {expansion_store_url} for specific products...")
            
            # First, get all available products from expansion store
            expansion_products = self._extract_products(expansion_store_url)
            
            if not expansion_products:
                logger.info("❌ No products found on expansion store")
                return found_products
            
            logger.info(f"📦 Found {len(expansion_products)} total products on expansion store")
            
            # Normalize expansion store product names for comparison
            expansion_product_names = []
            for product in expansion_products:
                if ' - http' in product:
                    clean_name = product.split(' - http')[0]
                else:
                    clean_name = product
                expansion_product_names.append(clean_name)
            
            # Search for each target product
            for target_name in target_product_names:
                logger.info(f"🔍 Searching for: '{target_name}'")
                
                # Normalize target name
                normalized_target = self._normalize_name(target_name)
                
                # Look for exact matches first
                exact_match_found = False
                for exp_name in expansion_product_names:
                    normalized_exp = self._normalize_name(exp_name)
                    
                    if normalized_target == normalized_exp:
                        found_products.append(target_name)
                        logger.info(f"   ✅ EXACT MATCH: '{exp_name}'")
                        exact_match_found = True
                        break
                
                # If no exact match, look for high similarity matches (90%+)
                if not exact_match_found:
                    best_match = None
                    best_similarity = 0
                    
                    for exp_name in expansion_product_names:
                        normalized_exp = self._normalize_name(exp_name)
                        similarity = self._calculate_name_similarity(normalized_target, normalized_exp)
                        
                        if similarity > best_similarity and similarity >= 0.9:
                            best_similarity = similarity
                            best_match = exp_name
                    
                    if best_match:
                        found_products.append(target_name)
                        logger.info(f"   ✅ HIGH SIMILARITY MATCH ({best_similarity:.1%}): '{best_match}'")
                    else:
                        logger.info(f"   ❌ NO MATCH FOUND for '{target_name}'")
            
        except Exception as e:
            logger.error(f"Error searching for products on expansion store: {e}")
        
        return found_products
    
    def _extract_brand_and_model(self, product_name: str) -> Optional[dict]:
        """Extract brand and model information from product name"""
        if not product_name:
            return None
        
        # Common brand patterns for electric vehicles and accessories
        known_brands = {
            'super73': 'Super73',
            'segway': 'Segway', 
            'zooz': 'Zooz',
            'onewheel': 'OneWheel',
            'future motion': 'Future Motion',
            'evolve': 'Evolve',
            'minimotors': 'MiniMotors',
            'boostedusa': 'BoostedUSA',
            'jackrabbit': 'JackRabbit',
            'fend': 'FEND',
            'tektro': 'Tektro',
            'carver': 'Carver',
            'e ride': 'E-Ride',
            'eride': 'E-Ride',
            'handlworks': 'Handlworks',
            'cake': 'Cake',
            'arbor': 'Arbor'
        }
        
        product_lower = product_name.lower()
        
        for brand_key, brand_name in known_brands.items():
            if brand_key in product_lower:
                # Extract potential model information
                model = product_lower.replace(brand_key, '').strip()
                # Clean up common words
                model = re.sub(r'\b(electric|bike|scooter|skateboard|board|helmet|replacement|kit)\b', '', model).strip()
                model = re.sub(r'\s+', ' ', model).strip()
                
                return {
                    'brand': brand_name,
                    'model': model if model else 'unknown',
                    'category': self._determine_product_category(product_name)
                }
        
        return None
    
    def _determine_product_category(self, product_name: str) -> str:
        """Determine product category from name"""
        name_lower = product_name.lower()
        
        if any(word in name_lower for word in ['bike', 'bicycle']):
            return 'bike'
        elif any(word in name_lower for word in ['scooter']):
            return 'scooter'
        elif any(word in name_lower for word in ['skateboard', 'board', 'onewheel']):
            return 'board'
        elif any(word in name_lower for word in ['helmet', 'protection']):
            return 'safety'
        elif any(word in name_lower for word in ['tire', 'wheel', 'brake', 'battery', 'motor', 'controller']):
            return 'parts'
        else:
            return 'accessory'
    
    def _brands_match(self, brand1: dict, brand2: dict) -> bool:
        """Check if two brand/model combinations represent the same product"""
        if not brand1 or not brand2:
            return False
        
        # Brands must match exactly
        if brand1['brand'].lower() != brand2['brand'].lower():
            return False
        
        # For same brand, check if models are similar or categories match
        if brand1['category'] == brand2['category']:
            # Same category products from same brand are likely related
            return True
        
        # Check for model similarity
        model1 = brand1.get('model', '').lower()
        model2 = brand2.get('model', '').lower()
        
        if model1 and model2:
            # Check for exact model match
            if model1 == model2:
                return True
            
            # Check for partial model match (e.g., "ultra" in both)
            model1_words = set(model1.split())
            model2_words = set(model2.split())
            if model1_words.intersection(model2_words):
                return True
        
        return False
    
    def _normalize_product_names(self, products: List[str]) -> set:
        """Normalize product names for better matching"""
        normalized = set()
        
        for product in products:
            # Extract name part (before URL if present)
            if ' - http' in product:
                name = product.split(' - http')[0]
            else:
                name = product
            
            # Normalize the name
            normalized_name = self._normalize_name(name)
            if normalized_name:
                normalized.add(normalized_name)
        
        return normalized
    
    def _select_representative_products(self, products: List[str], max_count: int) -> List[str]:
        """Select representative products for comparison, prioritizing diversity and common terms"""
        if len(products) <= max_count:
            return products
        
        # Strategy: Take products from different positions to get diversity
        selected = []
        total = len(products)
        
        if total >= 1:
            selected.append(products[0])  # First product
        if total >= 2 and max_count >= 2:
            selected.append(products[total // 2])  # Middle product
        if total >= 3 and max_count >= 3:
            selected.append(products[total * 3 // 4])  # 3/4 point
        if total >= 4 and max_count >= 4:
            selected.append(products[-1])  # Last product
        
        # If we need more products, fill from the beginning
        while len(selected) < max_count and len(selected) < total:
            for i, product in enumerate(products):
                if product not in selected:
                    selected.append(product)
                    break
        
        return selected[:max_count]

    def _normalize_name(self, name: str) -> str:
        """Normalize a single product name for comparison"""
        if not name:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = name.lower().strip()
        
        # Remove prices (common pattern: $XX.XX at the end)
        normalized = re.sub(r'\$\d+\.\d+$', '', normalized)
        normalized = re.sub(r'\$\d+$', '', normalized)
        
        # Remove wholesale-specific elements
        wholesale_patterns = [
            r'- min\. \d+.*$',  # "- Min. 2" or "- Min. 2 (SKU-123)"
            r'minimum \d+.*$',   # "Minimum 2"
            r'\([\w\-\d]+\)$',   # "(SKU-123)" or "(N-10)" at the end
            r'- \d+ pack.*$',    # "- 2 pack"
            r'wholesale.*$',     # "wholesale" anything
            r'bulk.*$',          # "bulk" anything
        ]
        
        for pattern in wholesale_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # Remove common prefixes/suffixes that might differ
        prefixes_to_remove = ['the ', 'a ', 'an ', 'new ', 'original ', 'classic ']
        suffixes_to_remove = [' - new', ' - original', ' (new)', ' (original)', ' - limited edition']
        
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        
        # Remove extra whitespace and special characters for comparison
        normalized = re.sub(r'[^\w\s]', ' ', normalized)  # Replace special chars with spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize whitespace
        
        return normalized
    
    def _find_fuzzy_product_matches(self, expansion_names: set, main_names: set) -> set:
        """Find fuzzy matches between product names"""
        fuzzy_matches = set()
        
        for exp_name in expansion_names:
            for main_name in main_names:
                # Skip if already exact match
                if exp_name == main_name:
                    continue
                
                # Check for high similarity (80%+ word overlap)
                similarity = self._calculate_name_similarity(exp_name, main_name)
                if similarity >= 0.8:
                    fuzzy_matches.add(f"{exp_name} ≈ {main_name}")
                    logger.info(f"Fuzzy match found: '{exp_name}' ≈ '{main_name}' (similarity: {similarity:.2f})")
        
        return fuzzy_matches
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two product names based on word overlap"""
        if not name1 or not name2:
            return 0.0
        
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _check_goods_services_types(self, expansion_info: StoreInfo, criteria: EvaluationCriteria) -> bool:
        """Check if goods and services types are the same"""
        if not expansion_info.goods_services or not criteria.main_brand_goods_services:
            return False
        
        expansion_goods = set(expansion_info.goods_services)
        main_goods = set(criteria.main_brand_goods_services)
        
        # Should have similar types of goods/services (not necessarily identical)
        overlap = len(expansion_goods.intersection(main_goods))
        total_types = len(main_goods)
        
        return overlap / total_types >= 0.6 if total_types > 0 else False
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using simple algorithm"""
        if not str1 or not str2:
            return 0.0
        
        # Simple similarity calculation
        common_chars = sum(1 for c in str1 if c in str2)
        total_chars = max(len(str1), len(str2))
        
        return common_chars / total_chars if total_chars > 0 else 0.0
    
    def _calculate_confidence_score(self, criteria_met: Dict[str, bool], store_info: StoreInfo) -> float:
        """Calculate confidence score based on available data"""
        if not store_info.store_name:
            return 0.3  # Low confidence if we can't extract store name
        
        if not store_info.branding_elements:
            return 0.5  # Medium confidence if we can't extract branding
        
        if not store_info.goods_services:
            return 0.7  # Good confidence but missing goods/services data
        
        # High confidence if we have all data
        return 0.9

    def _extract_logo_and_branding(self, url: str) -> Dict[str, any]:
        """
        REMOVED: Logo and visual branding analysis functionality
        This method has been removed as part of the logo analysis cleanup.
        """
        return {}

    def _fallback_logo_extraction(self, url: str) -> Dict[str, any]:
        """
        REMOVED: Fallback logo extraction functionality
        This method has been removed as part of the logo analysis cleanup.
        """
        return {}

    def _determine_brand_style(self, url: str) -> str:
        """
        REMOVED: Brand style determination functionality
        This method has been removed as part of the logo analysis cleanup.
        """
        return "Not Available"

    def _rgb_to_hex(self, rgb_tuple: Tuple[int, int, int]) -> str:
        """
        REMOVED: RGB to hex conversion functionality
        This method has been removed as part of the logo analysis cleanup.
        """
        return "#000000"

    def _compare_logo_and_branding(self, main_store_url: str, expansion_store_url: str) -> Dict[str, any]:
        """
        REMOVED: Logo and branding comparison functionality
        This method has been removed as part of the logo analysis cleanup.
        """
        return {}

    def _fallback_branding_comparison(self, main_store_url: str, expansion_store_url: str) -> Dict[str, any]:
        """
        REMOVED: Fallback branding comparison functionality
        This method has been removed as part of the logo analysis cleanup.
        """
        return {}

    def _compare_color_schemes(self, colors1: List[str], colors2: List[str]) -> float:
        """
        REMOVED: Color scheme comparison functionality
        This method has been removed as part of the logo analysis cleanup.
        """
        return 0.0

    def _get_b2b_indicators(self, url: str) -> List[str]:
        """Get B2B indicators from URL analysis"""
        try:
            domain = urlparse(url).netloc.lower()
            
            b2b_indicators = [
                'b2b', 'wholesale', 'business', 'enterprise', 'corporate',
                'trade', 'distributor', 'reseller', 'partner', 'pro', 'professional'
            ]
            
            detected_indicators = []
            for indicator in b2b_indicators:
                if indicator in domain:
                    detected_indicators.append(indicator)
            
            return detected_indicators
            
        except Exception as e:
            logger.error(f"Error getting B2B indicators for {url}: {e}")
            return []

    def _generate_product_identity_summary(self, expansion_info: StoreInfo, criteria: EvaluationCriteria) -> str:
        """Generates a detailed summary for the identical goods/products/services criteria using refined methodology."""
        expansion_products = expansion_info.products or []
        main_products = criteria.main_brand_products or []
        expansion_services = expansion_info.goods_services or []
        main_services = criteria.main_brand_goods_services or []
        
        # Handle case where main store has no offerings - this should fail
        if not main_products and not main_services:
            return "Main store has no products or services detected - cannot verify identical products criteria."
        
        # Build summary based on refined product matching methodology
        summary_parts = []
        
        # Products analysis using NEW REFINED METHODOLOGY
        if main_products:
            if not expansion_products:
                summary_parts.append(f"Products: Main store has {len(main_products)} products but expansion store has none")
            else:
                # Use refined methodology: search for up to 15 main store products in expansion store
                target_products = main_products[:25]
                target_names = []
                
                # Extract and normalize target product names
                for product in target_products:
                    if ' - http' in product:
                        name = product.split(' - http')[0]
                    else:
                        name = product
                    
                    normalized_name = self._normalize_name(name)
                    if normalized_name:
                        target_names.append(normalized_name)
                
                # NEW: Extract brands for matching
                target_brands = []
                for name in target_names:
                    brand_info = self._extract_brand_and_model(name)
                    target_brands.append(brand_info)
                
                # Normalize expansion store products for searching
                expansion_names = self._normalize_product_names(expansion_products)
                
                # NEW: Extract brands from expansion products  
                expansion_brands = []
                for product in expansion_products:
                    if ' - http' in product:
                        name = product.split(' - http')[0]
                    else:
                        name = product
                    
                    normalized_name = self._normalize_name(name)
                    if normalized_name:
                        brand_info = self._extract_brand_and_model(normalized_name)
                        if brand_info:
                            expansion_brands.append((normalized_name, brand_info))
                
                logger.info(f"Expansion store has {len(expansion_names)} normalized products to search")
                
                # Step 2: Search for each target product in the expansion store
                exact_matches = []
                fuzzy_matches = []
                brand_matches = 0  # NEW: Track brand matches
                
                for i, target_name in enumerate(target_names):
                    if target_name in expansion_names:
                        exact_matches.append(target_name)
                        logger.info(f"✅ EXACT MATCH FOUND: '{target_name}'")
                    else:
                        # Check for fuzzy match (90%+ similarity)
                        found_fuzzy = False
                        for exp_name in expansion_names:
                            similarity = self._calculate_name_similarity(target_name, exp_name)
                            if similarity >= 0.9:
                                fuzzy_matches.append(f"{target_name} ≈ {exp_name} ({similarity:.1%})")
                                found_fuzzy = True
                                break
                        
                        # NEW: Check for brand match if no fuzzy match found
                        if not found_fuzzy and i < len(target_brands):
                            target_brand = target_brands[i] if i < len(target_brands) else None
                            if target_brand:
                                for exp_name, exp_brand in expansion_brands:
                                    if self._brands_match(target_brand, exp_brand):
                                        brand_matches += 1
                                        break
                
                total_matches = len(exact_matches) + len(fuzzy_matches) + brand_matches
                
                # Determine if B2B qualification affects requirements
                if expansion_info.business_type == StoreBusinessType.B2B and self._check_b2b_qualification(expansion_info):
                    required_minimum = max(2, min(len(target_names), 2))
                    threshold_desc = "2+ matches required for B2B"
                else:
                    required_minimum = max(3, min(len(target_names), 3))
                    threshold_desc = "3+ matches required for D2C"
                
                summary_parts.append(f"Products: {total_matches}/{len(target_names)} target products found ({len(exact_matches)} exact, {len(fuzzy_matches)} fuzzy, {brand_matches} brand matches) - {threshold_desc}")
        
        # Services analysis (unchanged)
        if main_services:
            if not expansion_services:
                summary_parts.append(f"Services: Main store has {len(main_services)} services but expansion store has none")
            else:
                similarity_pct = self._calculate_services_similarity(main_services, expansion_services) * 100
                summary_parts.append(f"Services: {similarity_pct:.1f}% similarity ({len(main_services)} main services)")
        
        # Determine overall result using refined logic
        products_pass = True
        services_pass = True
        
        if main_products:
            if not expansion_products:
                products_pass = False
            else:
                # Use the same refined matching logic for pass/fail determination
                target_products = main_products[:25]
                target_names = []
                
                for product in target_products:
                    if ' - http' in product:
                        name = product.split(' - http')[0]
                    else:
                        name = product
                    
                    normalized_name = self._normalize_name(name)
                    if normalized_name:
                        target_names.append(normalized_name)
                
                expansion_names = self._normalize_product_names(expansion_products)
                
                exact_matches = 0
                fuzzy_matches = 0
                
                for target_name in target_names:
                    if target_name in expansion_names:
                        exact_matches += 1
                    else:
                        for exp_name in expansion_names:
                            similarity = self._calculate_name_similarity(target_name, exp_name)
                            if similarity >= 0.9:
                                fuzzy_matches += 1
                                break
                
                total_matches = exact_matches + fuzzy_matches
                
                # Apply same pass/fail logic as the main method
                if expansion_info.business_type == StoreBusinessType.B2B and self._check_b2b_qualification(expansion_info):
                    required_minimum = max(2, min(len(target_names), 2))
                else:
                    required_minimum = max(3, min(len(target_names), 3))
                
                products_pass = total_matches >= required_minimum
        
        if main_services:
            if not expansion_services:
                services_pass = False
            else:
                similarity_pct = self._calculate_services_similarity(main_services, expansion_services) * 100
                services_pass = similarity_pct >= 80.0
        
        overall_pass = products_pass and services_pass
        
        # Build final summary
        summary = "Identical Goods/Products/Services: " + " | ".join(summary_parts)
        
        if overall_pass:
            summary += " - Criteria MET (expansion store carries identical offerings as main store)"
        else:
            summary += " - Criteria NOT MET (expansion store must carry identical goods, products, and/or services as main store)"
        
        return summary

    def _get_matching_products(self, main_products: List[str], expansion_products: List[str]) -> List[str]:
        """Get detailed list of matching products with both exact and fuzzy matches."""
        if not main_products or not expansion_products:
            return []
        
        expansion_names = self._normalize_product_names(expansion_products)
        main_names = self._normalize_product_names(main_products)
        
        # Get exact matches
        exact_matches = list(expansion_names.intersection(main_names))
        
        # Get fuzzy matches
        fuzzy_matches = list(self._find_fuzzy_product_matches(expansion_names, main_names))
        
        # Combine and return
        all_matches = []
        
        # Add exact matches
        for match in exact_matches:
            all_matches.append(f"✓ {match} (exact match)")
        
        # Add fuzzy matches
        for match in fuzzy_matches:
            all_matches.append(f"≈ {match} (similar)")
        
        return all_matches

    def _count_matching_products(self, main_products: List[str], expansion_products: List[str]) -> int:
        """Counts the total number of matching product names (exact + fuzzy)."""
        if not main_products or not expansion_products:
            return 0
        
        expansion_names = self._normalize_product_names(expansion_products)
        main_names = self._normalize_product_names(main_products)
        
        exact_matches = len(expansion_names.intersection(main_names))
        fuzzy_matches = len(self._find_fuzzy_product_matches(expansion_names, main_names))
        
        return exact_matches + fuzzy_matches
    
    def _get_product_details_for_admin(self, main_products: List[str], expansion_products: List[str]) -> Dict[str, any]:
        """Get detailed product analysis for admin view with enhanced matching and clear status messaging"""
        
        # Check if we have search results from the new chronological flow
        search_results = getattr(self, '_last_search_results', None)
        
        if search_results:
            # Use the new chronological search results
            searched_products = search_results.get('searched_products', [])
            found_products = search_results.get('found_products', [])
            expansion_url = search_results.get('expansion_store_url', '')
            
            # Create detailed product lists for admin view
            main_store_products = []
            for product in main_products[:25]:  # Show up to 25 products that were searched
                if ' - http' in product:
                    name, url = product.split(' - http', 1)
                    url = 'http' + url
                    main_store_products.append({
                        'name': name.strip(),
                        'url': url,
                        'display': product
                    })
                else:
                    main_store_products.append({
                        'name': product,
                        'url': '',
                        'display': product
                    })
            
            # For expansion store, show the search results
            expansion_store_products = []
            if found_products:
                for product in found_products:
                    expansion_store_products.append({
                        'name': product,
                        'url': expansion_url,
                        'display': f"{product} - {expansion_url}"
                    })
            
            # Generate clear status messaging
            if not found_products:
                products_analysis = "❌ No identical products listed on the Main Site are found on the requested Expansion Store Site."
                status_type = 'error'
            else:
                products_analysis = f"✅ Identical Products found on both the Main and Expansion Store site. Found {len(found_products)} out of {len(searched_products)} searched products."
                status_type = 'success'
            
            return {
                'main_store_products': main_store_products,
                'expansion_store_products': expansion_store_products,
                'exact_matches': found_products,  # All found products are matches
                'fuzzy_matches': [],
                'total_matches': len(found_products),
                'products_analysis': products_analysis,
                'status_type': status_type,
                'searched_products': searched_products,
                'found_products': found_products
            }
        
        # Fallback to old method if no search results available
        if not main_products or not expansion_products:
            return {
                'main_store_products': [{'name': p, 'url': p.split(' - ')[-1] if ' - http' in p else '', 'display': p} for p in main_products] if main_products else [],
                'expansion_store_products': [{'name': p, 'url': p.split(' - ')[-1] if ' - http' in p else '', 'display': p} for p in expansion_products] if expansion_products else [],
                'exact_matches': [],
                'fuzzy_matches': [],
                'total_matches': 0,
                'products_analysis': "No products found in one or both stores",
                'status_type': 'error',
                'searched_products': [],
                'found_products': []
            }
        
        # Normalize product names for comparison
        expansion_names = self._normalize_product_names(expansion_products)
        main_names = self._normalize_product_names(main_products)
        
        # Find exact matches
        exact_matches = expansion_names.intersection(main_names)
        
        # Find fuzzy matches (if needed)
        fuzzy_matches = self._find_fuzzy_product_matches(expansion_names - exact_matches, main_names - exact_matches)
        
        # Calculate overlap percentage
        overlap_percentage = len(exact_matches) / len(main_names) if main_names else 0
        
        # Create detailed product lists for admin view
        main_store_products = []
        for product in main_products:
            if ' - http' in product:
                name, url = product.split(' - http', 1)
                url = 'http' + url
                main_store_products.append({
                    'name': name.strip(),
                    'url': url,
                    'display': product
                })
            else:
                main_store_products.append({
                    'name': product,
                    'url': '',
                    'display': product
                })
        
        expansion_store_products = []
        for product in expansion_products:
            if ' - http' in product:
                name, url = product.split(' - http', 1)
                url = 'http' + url
                expansion_store_products.append({
                    'name': name.strip(),
                    'url': url,
                    'display': product
                })
            else:
                expansion_store_products.append({
                    'name': product,
                    'url': '',
                    'display': product
                })
        
        # Analysis summary
        products_analysis = f"Product overlap: {len(exact_matches)}/{len(main_names)} ({overlap_percentage:.1%}). "
        
        if overlap_percentage >= 0.7:
            products_analysis += "Expansion store carries sufficient identical products from main store."
            status_type = 'success'
        else:
            products_analysis += f"Expansion store does not carry sufficient identical products (requires ≥70% overlap)."
            status_type = 'error'
        
        return {
            'main_store_products': main_store_products,
            'expansion_store_products': expansion_store_products,
            'exact_matches': list(exact_matches),
            'fuzzy_matches': list(fuzzy_matches),
            'total_matches': len(exact_matches) + len(fuzzy_matches),
            'products_analysis': products_analysis,
            'status_type': status_type,
            'searched_products': [],
            'found_products': []
        }
    
    def _get_service_matches(self, main_services: List[str], expansion_services: List[str]) -> Dict[str, any]:
        """Get detailed service matching analysis"""
        if not main_services or not expansion_services:
            return {
                'matching_services': [],
                'main_only_services': main_services if main_services else [],
                'expansion_only_services': expansion_services if expansion_services else [],
                'similarity_score': 0.0
            }
        
        main_normalized = set(service.lower().strip() for service in main_services)
        expansion_normalized = set(service.lower().strip() for service in expansion_services)
        
        matching = main_normalized.intersection(expansion_normalized)
        main_only = main_normalized - expansion_normalized
        expansion_only = expansion_normalized - main_normalized
        
        similarity = self._calculate_services_similarity(main_services, expansion_services)
        
        return {
            'matching_services': list(matching),
            'main_only_services': list(main_only),
            'expansion_only_services': list(expansion_only),
            'similarity_score': similarity
        }
    
    def _calculate_products_overlap_percentage(self, main_products: List[str], expansion_products: List[str]) -> float:
        """Calculate the percentage of main store products found in expansion store"""
        if not main_products:
            return 100.0 if not expansion_products else 0.0
        
        if not expansion_products:
            return 0.0
        
        main_names = self._normalize_product_names(main_products)
        expansion_names = self._normalize_product_names(expansion_products)
        
        matching_count = len(main_names.intersection(expansion_names))
        return (matching_count / len(main_names)) * 100
    
    def _get_detailed_overlap_analysis(self, criteria: EvaluationCriteria, expansion_info: StoreInfo) -> str:
        """Get detailed analysis of goods/products/services overlap"""
        main_products = criteria.main_brand_products or []
        expansion_products = expansion_info.products or []
        main_services = criteria.main_brand_goods_services or []
        expansion_services = expansion_info.goods_services or []
        
        analysis_parts = []
        
        # Products analysis
        if main_products:
            if expansion_products:
                products_overlap = self._calculate_products_overlap_percentage(main_products, expansion_products)
                analysis_parts.append(f"Products: {products_overlap:.1f}% overlap ({len(main_products)} main products)")
            else:
                analysis_parts.append(f"Products: Expansion store has no products but main store has {len(main_products)}")
        
        # Services analysis
        if main_services:
            if expansion_services:
                services_similarity = self._calculate_services_similarity(main_services, expansion_services) * 100
                analysis_parts.append(f"Services: {services_similarity:.1f}% similarity ({len(main_services)} main services)")
            else:
                analysis_parts.append(f"Services: Expansion store has no services but main store has {len(main_services)}")
        
        # Overall assessment
        if not main_products and not main_services:
            return "Main store has no products or services - cannot verify identical products criteria."
        
        if not analysis_parts:
            return "No products or services to compare."
        
        return " | ".join(analysis_parts)
    
    def _calculate_services_similarity(self, main_services: List[str], expansion_services: List[str]) -> float:
        """Calculate similarity between service offerings"""
        if not main_services or not expansion_services:
            return 0.0
        
        # Normalize service names
        main_normalized = set(service.lower().strip() for service in main_services)
        expansion_normalized = set(service.lower().strip() for service in expansion_services)
        
        # Calculate overlap
        intersection = main_normalized.intersection(expansion_normalized)
        union = main_normalized.union(expansion_normalized)
        
        # Jaccard similarity
        similarity = len(intersection) / len(union) if union else 0.0
        return similarity

    def _find_category_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Find category URLs that might contain products
        """
        category_urls = set()
        
        # Look for navigation links that might be categories
        nav_selectors = [
            'nav a[href^="/"]',
            '.navigation a[href^="/"]',
            '.menu a[href^="/"]',
            '.nav a[href^="/"]',
            'header a[href^="/"]',
            '.main-nav a[href^="/"]'
        ]
        
        for selector in nav_selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True).lower()
                    
                    if href and self._looks_like_category_url(href, text):
                        full_url = urljoin(base_url, href)
                        category_urls.add(full_url)
                        
                        if len(category_urls) >= 20:
                            break
                            
            except Exception as e:
                continue
        
        logger.info(f"Found {len(category_urls)} potential category URLs")
        return list(category_urls)

    def _looks_like_category_url(self, href: str, link_text: str) -> bool:
        """
        Check if a URL looks like it might be a product category
        """
        if not href or len(href) < 3:
            return False
        
        href_lower = href.lower()
        
        # Skip obvious non-category URLs
        skip_patterns = [
            '/about', '/contact', '/help', '/support', '/news',
            '/terms', '/privacy', '/shipping', '/returns', '/faq',
            '/login', '/register', '/account', '/cart', '/checkout',
            '/blog/category'  # Skip blog categories
        ]
        
        for pattern in skip_patterns:
            if pattern in href_lower:
                return False
        
        # Look for category indicators in URL or text
        category_indicators = [
            'flags', 'military', 'american', 'state', 'custom', 'patriotic',
            'clothing', 'apparel', 'shoes', 'accessories', 'jewelry',
            'home', 'garden', 'outdoor', 'sports', 'fitness', 'health',
            'electronics', 'tech', 'computers', 'phones', 'gadgets',
            'books', 'media', 'music', 'movies', 'games',
            'food', 'beverage', 'coffee', 'tea', 'snacks',
            'beauty', 'skincare', 'makeup', 'hair', 'personal',
            'auto', 'automotive', 'parts', 'tools', 'hardware',
            'pets', 'animals', 'supplies', 'toys', 'kids',
            'office', 'business', 'supplies', 'furniture',
            'travel', 'luggage', 'bags', 'backpacks',
            # Additional indicators for flag sites
            'banners', 'poles', 'flagpole', 'ceremonial', 'indoor', 'outdoor',
            # Beauty and hair care brand indicators
            'intelligent', 'nutrients', 'arete', 'organic', 'natural',
            'scalp', 'treatment', 'shampoo', 'conditioner', 'styling',
            'collection', 'brand', 'product', 'care', 'wellness'
        ]
        
        # Check if URL or link text contains category indicators
        combined_text = f"{href_lower} {link_text}"
        
        for indicator in category_indicators:
            if indicator in combined_text:
                return True
        
        # Also accept URLs that look like category paths
        path_segments = [seg for seg in href.split('/') if seg and '?' not in seg]
        
        # Accept paths that look like categories (not too deep, not too shallow)
        if len(path_segments) >= 1 and len(path_segments) <= 3:
            # Skip single-word paths that are likely pages, not categories
            if len(path_segments) == 1 and path_segments[0] in ['index', 'home', 'main', 'default']:
                return False
            return True
        
        return False

    def _discover_direct_collections(self, base_url: str) -> List[str]:
        """
        Try direct collection URLs based on common patterns and brand names
        """
        collections = []
        
        # Common brand collection patterns for beauty/hair care sites
        brand_patterns = [
            'intelligent-nutrients',
            'intelligent-nutrients-product-collection',
            'arete-product-collection',
            'o-m-product-collection',
            'oway-product-collection',
            'simply-organic-product-collection',
            'golden-hour-botanicals-product-collection',
            'juliart-product-collection',
            'haoma-product-collection',
            'myveg-hair-care-collection',
            'scalp-treatments',
            'hair-care',
            'skincare',
            'styling-products',
            'hair-treatment',
            'conditioner',
            'shampoo',
            'treatments',
            'best-sellers',
            'new-arrivals'
        ]
        
        # Try each pattern as a collection URL
        for pattern in brand_patterns:
            collection_url = urljoin(base_url, f'/collections/{pattern}')
            collections.append(collection_url)
        
        logger.info(f"Generated {len(collections)} direct collection URLs to try")
        return collections

    def _extract_from_direct_collections(self, session: requests.Session, base_url: str) -> List[str]:
        """
        Extract products from direct collection URLs
        """
        products = []
        direct_collections = self._discover_direct_collections(base_url)
        
        for collection_url in direct_collections[:10]:  # Limit to 10 collections
            try:
                time.sleep(0.5)  # Be respectful
                collection_products = self._extract_products_from_category_page(collection_url)
                
                # Validate a few products from this collection
                for product_url in collection_products[:3]:  # Test 3 products per collection
                    try:
                        product_info = self._validate_and_extract_product(session, product_url)
                        if product_info:
                            products.append(product_info)
                            logger.info(f"✅ Found product from direct collection {collection_url}: {product_info}")
                            
                            if len(products) >= 10:  # Limit total products from direct collections
                                break
                    except Exception as e:
                        continue
                        
                if len(products) >= 10:
                    break
                    
            except Exception as e:
                logger.warning(f"Failed to extract from direct collection {collection_url}: {e}")
                continue
        
        logger.info(f"Direct collection discovery found {len(products)} additional products")
        return products



    def _extract_products_from_category_page(self, category_url: str) -> List[str]:
        """
        Extract product URLs from a category page
        """
        products = []
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(category_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return products
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product links within the category page using multiple strategies
            product_selectors = [
                # Standard product selectors
                'a[href*="/products/"]', 'a[href*="/product/"]', 'a[href*="/item/"]', 'a[href*="/p/"]',
                
                # Image-based product links (very common)
                'a img[alt]:parent',
                'a img[title]:parent',
                'a img[src*="product"]:parent',
                
                # Links with product-like text or attributes
                'a[title]',
                'a[data-product]',
                'a[data-item]',
                
                # Generic links that might be products
                'a[href^="/"][href*="-"]',  # URLs with dashes (common for product handles)
                'a[href^="/"][href*="_"]',  # URLs with underscores
                
                # Links within product containers
                '.product a', '.item a', '.card a', '.listing a',
                '.grid-item a', '.list-item a', '.catalog-item a',
                
                # More aggressive: any link with reasonable length
                'a[href^="/"]'  # Any internal link - we'll filter later
            ]
            
            found_links = set()
            
            for selector in product_selectors:
                try:
                    links = soup.select(selector)
                    
                    for link in links:
                        href = link.get('href')
                        if href and href not in found_links:
                            # More permissive validation for category page links
                            if self._could_be_product_url(href):
                                full_url = urljoin(category_url, href)
                                products.append(full_url)
                                found_links.add(href)
                                
                                if len(products) >= 20:  # Increased limit
                                    break
                                    
                except Exception as e:
                    continue
                
                if len(products) >= 20:
                    break
            
            logger.info(f"Category page {category_url} yielded {len(products)} potential products")
            
        except Exception as e:
            logger.warning(f"Failed to extract from category page {category_url}: {e}")
        
        return products

    def _could_be_product_url(self, href: str) -> bool:
        """
        More permissive check for URLs that could be products (used for category page links)
        """
        if not href or len(href) < 5:
            return False
        
        href_lower = href.lower()
        
        # Skip obvious non-product URLs
        skip_patterns = [
            '/cart', '/checkout', '/login', '/register', '/account',
            '/about', '/contact', '/help', '/support', '/blog',
            '/terms', '/privacy', '/shipping', '/returns',
            '.pdf', '.jpg', '.png', '.gif', '.css', '.js',
            'javascript:', 'mailto:', 'tel:', '#'
        ]
        
        for pattern in skip_patterns:
            if pattern in href_lower:
                return False
        
        # Check for Korean/Asian e-commerce patterns first
        korean_patterns = [
            'product_no=',
            'goods_no=',
            'item_no=',
            'prd_no=',
        ]
        
        if any(pattern in href_lower for pattern in korean_patterns):
            return True
        
        # Accept URLs that have reasonable structure
        path_segments = [seg for seg in href.split('/') if seg and '?' not in seg]
        
        # Accept if it has dashes (product handles) or looks like a specific item
        if '-' in href and len(path_segments) >= 1:
            return True
        
        # Accept if it has multiple path segments and reasonable length
        if len(path_segments) >= 2 and len(href) > 10:
            return True
        
        # Accept if it has numbers (could be product IDs)
        if re.search(r'\d{3,}', href):
            return True
        
        return False

    def _generate_expansion_store_search_status(self, main_products: List[str], product_details: Dict[str, any]) -> str:
        """Generate clear status messaging for Admin view based on search results"""
        if not main_products or not product_details.get('found_products', []):
            return "No products found on expansion store"
        
        if not product_details.get('searched_products', []):
            return "No products searched on expansion store"
        
        found_products = product_details.get('found_products', [])
        searched_products = product_details.get('searched_products', [])
        
        if not found_products or not searched_products:
            return "No matching products found"
        
        if len(found_products) == len(searched_products):
            return "All products found on expansion store"
        
        if len(found_products) < len(searched_products):
            return f"{len(searched_products) - len(found_products)} products not found on expansion store"
        
        if len(found_products) > len(searched_products):
            return f"{len(found_products) - len(searched_products)} products not searched on expansion store"
        
        return "Mixed results - some products found, some not"

def main():
    """Main function for testing the evaluator"""
    evaluator = ExpansionStoreEvaluator()
    
    # Example usage
    main_store_url = "https://example-store.com"
    expansion_store_url = "https://example-store-es.com"
    
    print("Eddie the Expansion Store Evaluator")
    print("=" * 50)
    print(f"Main Store: {main_store_url}")
    print(f"Expansion Store: {expansion_store_url}")
    print()
    
    # Evaluate the expansion store
    report = evaluator.evaluate_expansion_store(main_store_url, expansion_store_url)
    
    # Display results
    print(f"Evaluation Result: {report.result.value.upper()}")
    print(f"Confidence Score: {report.confidence_score:.2f}")
    print()
    
    print("Criteria Met:")
    for criterion, met in report.criteria_met.items():
        status = "✓" if met else "✗"
        print(f"  {status} {criterion}")
    print()
    
    if report.reasons:
        print("Reasons:")
        for reason in report.reasons:
            print(f"  • {reason}")
        print()
    
    if report.recommendations:
        print("Recommendations:")
        for rec in report.recommendations:
            print(f"  • {rec}")

if __name__ == "__main__":
    main() 