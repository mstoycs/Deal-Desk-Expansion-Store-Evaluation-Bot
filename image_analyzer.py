#!/usr/bin/env python3
"""
Image Analysis Module for Eddie the Expansion Store Evaluator
Implements Phase 1 and Phase 2 of image analysis capabilities
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import logging
from typing import Dict, List, Tuple, Optional
from urllib.parse import urljoin, urlparse
import re
from dataclasses import dataclass
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LogoInfo:
    """Information about a detected logo"""
    src: str
    alt: str
    width: Optional[int]
    height: Optional[int]
    selector: str
    confidence: float

@dataclass
class ColorScheme:
    """Color scheme information"""
    primary_colors: List[Tuple[int, int, int]]
    color_palette: List[str]
    dominant_colors: List[Tuple[int, int, int]]
    color_histogram: Dict[str, float]

@dataclass
class ImageSimilarityResult:
    """Result of image similarity analysis"""
    structural_similarity: float
    feature_matching: float
    color_histogram: float
    contour_similarity: float
    overall_similarity: float
    confidence: float

class WebImageExtractor:
    """Extract images from web pages"""
    
    def __init__(self):
        self.logo_selectors = [
            'img[alt*="logo" i]',
            'img[src*="logo" i]',
            '.logo img',
            '#logo img',
            'header img',
            'nav img',
            '[class*="logo"] img',
            '[id*="logo"] img'
        ]
        
        self.product_selectors = [
            '.product img',
            '.item img',
            '[data-product-image]',
            'img[alt*="product" i]',
            '.product-gallery img',
            '.product-image img',
            '.item-image img'
        ]
    
    def extract_logos_from_html(self, html_content: str, base_url: str) -> List[LogoInfo]:
        """Extract logo information from HTML content"""
        logos = []
        
        # Simple regex-based extraction (Phase 1 approach)
        # In Phase 2, this would use BeautifulSoup or Selenium
        
        # Find img tags with logo-related attributes
        img_pattern = r'<img[^>]+>'
        img_matches = re.findall(img_pattern, html_content, re.IGNORECASE)
        
        for img_match in img_matches:
            logo_info = self._parse_img_tag(img_match, base_url)
            if logo_info and self._is_likely_logo(logo_info):
                logos.append(logo_info)
        
        return logos
    
    def _parse_img_tag(self, img_tag: str, base_url: str) -> Optional[LogoInfo]:
        """Parse img tag and extract logo information"""
        try:
            # Extract src attribute
            src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag, re.IGNORECASE)
            if not src_match:
                return None
            
            src = src_match.group(1)
            if not src.startswith('http'):
                src = urljoin(base_url, src)
            
            # Extract alt attribute
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag, re.IGNORECASE)
            alt = alt_match.group(1) if alt_match else ""
            
            # Extract width and height
            width_match = re.search(r'width=["\'](\d+)["\']', img_tag)
            height_match = re.search(r'height=["\'](\d+)["\']', img_tag)
            
            width = int(width_match.group(1)) if width_match else None
            height = int(height_match.group(1)) if height_match else None
            
            # Determine selector used
            selector = self._determine_selector(img_tag)
            
            # Calculate confidence based on attributes
            confidence = self._calculate_logo_confidence(img_tag, alt, src)
            
            return LogoInfo(
                src=src,
                alt=alt,
                width=width,
                height=height,
                selector=selector,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error parsing img tag: {e}")
            return None
    
    def _is_likely_logo(self, logo_info: LogoInfo) -> bool:
        """Determine if an image is likely to be a logo"""
        # Check alt text for logo indicators
        alt_lower = logo_info.alt.lower()
        logo_indicators = ['logo', 'brand', 'company', 'site']
        
        if any(indicator in alt_lower for indicator in logo_indicators):
            return True
        
        # Check src URL for logo indicators
        src_lower = logo_info.src.lower()
        if any(indicator in src_lower for indicator in logo_indicators):
            return True
        
        # Check size (logos are typically small to medium)
        if logo_info.width and logo_info.height:
            if 50 <= logo_info.width <= 300 and 50 <= logo_info.height <= 300:
                return True
        
        return False
    
    def _determine_selector(self, img_tag: str) -> str:
        """Determine which selector matched this image"""
        # This is a simplified version - in practice, you'd use a proper HTML parser
        if 'class="logo' in img_tag or 'class=\'logo' in img_tag:
            return '.logo img'
        elif 'id="logo' in img_tag or 'id=\'logo' in img_tag:
            return '#logo img'
        elif 'alt="logo' in img_tag or 'alt=\'logo' in img_tag:
            return 'img[alt*="logo" i]'
        else:
            return 'img[src*="logo" i]'
    
    def _calculate_logo_confidence(self, img_tag: str, alt: str, src: str) -> float:
        """Calculate confidence that this is a logo"""
        confidence = 0.0
        
        # Alt text confidence
        alt_lower = alt.lower()
        if 'logo' in alt_lower:
            confidence += 0.4
        elif 'brand' in alt_lower:
            confidence += 0.3
        elif 'company' in alt_lower:
            confidence += 0.2
        
        # Src URL confidence
        src_lower = src.lower()
        if 'logo' in src_lower:
            confidence += 0.3
        elif 'brand' in src_lower:
            confidence += 0.2
        
        # Size confidence (if available)
        width_match = re.search(r'width=["\'](\d+)["\']', img_tag)
        height_match = re.search(r'height=["\'](\d+)["\']', img_tag)
        
        if width_match and height_match:
            width = int(width_match.group(1))
            height = int(height_match.group(1))
            if 50 <= width <= 300 and 50 <= height <= 300:
                confidence += 0.2
        
        return min(1.0, confidence)

class ImageProcessor:
    """Process and analyze images"""
    
    def __init__(self):
        self.max_image_size = (512, 512)
        self.feature_extractor = cv2.SIFT_create()
        self.matcher = cv2.BFMatcher()
    
    def download_and_preprocess(self, image_url: str) -> Optional[np.ndarray]:
        """Download and preprocess an image"""
        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Convert to numpy array
            img_array = np.frombuffer(response.content, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if img is None:
                return None
            
            # Resize for consistent processing
            img_resized = cv2.resize(img, self.max_image_size)
            
            return img_resized
            
        except Exception as e:
            logger.error(f"Error downloading/preprocessing image {image_url}: {e}")
            return None
    
    def extract_color_scheme(self, image_url: str) -> Optional[ColorScheme]:
        """Extract color scheme from an image"""
        try:
            img = self.download_and_preprocess(image_url)
            if img is None:
                return None
            
            # Convert BGR to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Resize for faster processing
            img_small = cv2.resize(img_rgb, (150, 150))
            
            # Reshape for clustering
            img_reshaped = img_small.reshape(-1, 3)
            
            # Apply k-means clustering
            kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
            kmeans.fit(img_reshaped)
            
            # Get dominant colors
            colors = kmeans.cluster_centers_.astype(int)
            
            # Calculate color histogram
            color_histogram = self._calculate_color_histogram(img_rgb)
            
            # Generate color palette
            color_palette = [self._rgb_to_hex(color) for color in colors]
            
            return ColorScheme(
                primary_colors=[tuple(color) for color in colors],
                color_palette=color_palette,
                dominant_colors=[tuple(color) for color in colors[:3]],
                color_histogram=color_histogram
            )
            
        except Exception as e:
            logger.error(f"Error extracting color scheme from {image_url}: {e}")
            return None
    
    def _calculate_color_histogram(self, img: np.ndarray) -> Dict[str, float]:
        """Calculate color histogram"""
        # Convert to HSV for better color analysis
        img_hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        
        # Calculate histogram for each channel
        h_hist = cv2.calcHist([img_hsv], [0], None, [180], [0, 180])
        s_hist = cv2.calcHist([img_hsv], [1], None, [256], [0, 256])
        v_hist = cv2.calcHist([img_hsv], [2], None, [256], [0, 256])
        
        # Normalize histograms
        h_hist = h_hist.flatten() / h_hist.sum()
        s_hist = s_hist.flatten() / s_hist.sum()
        v_hist = v_hist.flatten() / v_hist.sum()
        
        return {
            'hue': h_hist.tolist(),
            'saturation': s_hist.tolist(),
            'value': v_hist.tolist()
        }
    
    def _rgb_to_hex(self, rgb: np.ndarray) -> str:
        """Convert RGB values to hex color"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

class ImageSimilarityAnalyzer:
    """Analyze similarity between images"""
    
    def __init__(self):
        self.processor = ImageProcessor()
        self.feature_extractor = cv2.SIFT_create()
        self.matcher = cv2.BFMatcher()
    
    def compare_images(self, image1_url: str, image2_url: str) -> ImageSimilarityResult:
        """Compare two images and return similarity metrics"""
        
        # Download and preprocess images
        img1 = self.processor.download_and_preprocess(image1_url)
        img2 = self.processor.download_and_preprocess(image2_url)
        
        if img1 is None or img2 is None:
            return ImageSimilarityResult(
                structural_similarity=0.0,
                feature_matching=0.0,
                color_histogram=0.0,
                contour_similarity=0.0,
                overall_similarity=0.0,
                confidence=0.0
            )
        
        # Perform different types of comparison
        structural_sim = self._structural_similarity(img1, img2)
        feature_sim = self._feature_matching(img1, img2)
        color_sim = self._color_histogram_similarity(img1, img2)
        contour_sim = self._contour_similarity(img1, img2)
        
        # Calculate weighted overall similarity
        weights = {
            'structural': 0.3,
            'feature': 0.3,
            'color': 0.25,
            'contour': 0.15
        }
        
        overall_similarity = (
            structural_sim * weights['structural'] +
            feature_sim * weights['feature'] +
            color_sim * weights['color'] +
            contour_sim * weights['contour']
        )
        
        # Calculate confidence based on image quality
        confidence = self._calculate_confidence(img1, img2)
        
        return ImageSimilarityResult(
            structural_similarity=structural_sim,
            feature_matching=feature_sim,
            color_histogram=color_sim,
            contour_similarity=contour_sim,
            overall_similarity=overall_similarity,
            confidence=confidence
        )
    
    def _structural_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate structural similarity using SSIM"""
        try:
            from skimage.metrics import structural_similarity as ssim
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Calculate SSIM
            similarity = ssim(gray1, gray2)
            return max(0, similarity)  # Ensure non-negative
            
        except ImportError:
            # Fallback if skimage is not available
            logger.warning("skimage not available, using fallback structural similarity")
            return self._fallback_structural_similarity(img1, img2)
        except Exception as e:
            logger.error(f"Error in structural similarity: {e}")
            return 0.0
    
    def _fallback_structural_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Fallback structural similarity calculation"""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Calculate mean squared error
            mse = np.mean((gray1.astype(float) - gray2.astype(float)) ** 2)
            
            # Convert MSE to similarity (lower MSE = higher similarity)
            max_mse = 255 ** 2
            similarity = 1 - (mse / max_mse)
            
            return max(0, similarity)
            
        except Exception as e:
            logger.error(f"Error in fallback structural similarity: {e}")
            return 0.0
    
    def _feature_matching(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compare using SIFT feature matching"""
        try:
            # Detect keypoints and descriptors
            kp1, des1 = self.feature_extractor.detectAndCompute(img1, None)
            kp2, des2 = self.feature_extractor.detectAndCompute(img2, None)
            
            if des1 is None or des2 is None:
                return 0.0
            
            # Match features
            matches = self.matcher.knnMatch(des1, des2, k=2)
            
            # Apply ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.75 * n.distance:
                        good_matches.append(m)
            
            # Calculate similarity based on good matches
            if len(kp1) == 0 or len(kp2) == 0:
                return 0.0
            
            similarity = len(good_matches) / max(len(kp1), len(kp2))
            return min(1.0, similarity)
            
        except Exception as e:
            logger.error(f"Error in feature matching: {e}")
            return 0.0
    
    def _color_histogram_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compare color histograms"""
        try:
            # Convert to HSV
            hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
            hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
            
            # Calculate histograms
            hist1 = cv2.calcHist([hsv1], [0, 1], None, [180, 256], [0, 180, 0, 256])
            hist2 = cv2.calcHist([hsv2], [0, 1], None, [180, 256], [0, 180, 0, 256])
            
            # Normalize histograms
            cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
            
            # Calculate correlation
            similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # Convert to 0-1 range
            return max(0, (similarity + 1) / 2)
            
        except Exception as e:
            logger.error(f"Error in color histogram similarity: {e}")
            return 0.0
    
    def _contour_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compare contours/shapes"""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
            # Find contours
            _, thresh1 = cv2.threshold(gray1, 127, 255, cv2.THRESH_BINARY)
            _, thresh2 = cv2.threshold(gray2, 127, 255, cv2.THRESH_BINARY)
            
            contours1, _ = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours2, _ = cv2.findContours(thresh2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours1 or not contours2:
                return 0.0
            
            # Compare contour areas
            area1 = sum(cv2.contourArea(c) for c in contours1)
            area2 = sum(cv2.contourArea(c) for c in contours2)
            
            if area1 == 0 or area2 == 0:
                return 0.0
            
            # Calculate similarity based on area ratio
            area_ratio = min(area1, area2) / max(area1, area2)
            
            return area_ratio
            
        except Exception as e:
            logger.error(f"Error in contour similarity: {e}")
            return 0.0
    
    def _calculate_confidence(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate confidence in the comparison"""
        try:
            # Check image quality
            quality1 = self._assess_image_quality(img1)
            quality2 = self._assess_image_quality(img2)
            
            # Average quality
            avg_quality = (quality1 + quality2) / 2
            
            return avg_quality
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _assess_image_quality(self, img: np.ndarray) -> float:
        """Assess image quality"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance (sharpness)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-1 range
            quality = min(1.0, laplacian_var / 1000)
            
            return quality
            
        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            return 0.5

class EnhancedBrandingAnalyzer:
    """Enhanced branding analysis with actual image processing"""
    
    def __init__(self):
        self.extractor = WebImageExtractor()
        self.processor = ImageProcessor()
        self.similarity_analyzer = ImageSimilarityAnalyzer()
    
    def analyze_branding(self, url: str, html_content: str) -> Dict:
        """Analyze branding from a URL and HTML content"""
        try:
            # Extract logos
            logos = self.extractor.extract_logos_from_html(html_content, url)
            
            # Extract color scheme from the first logo (if available)
            color_scheme = None
            if logos:
                color_scheme = self.processor.extract_color_scheme(logos[0].src)
            
            # Fallback color scheme if no logos found
            if not color_scheme:
                color_scheme = self._generate_fallback_color_scheme(url)
            
            return {
                'logos': [self._logo_to_dict(logo) for logo in logos],
                'color_scheme': self._color_scheme_to_dict(color_scheme) if color_scheme else None,
                'branding_elements': self._extract_branding_elements(url, html_content),
                'analysis_confidence': self._calculate_analysis_confidence(logos, color_scheme)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing branding for {url}: {e}")
            return self._fallback_branding_analysis(url)
    
    def compare_branding(self, main_store_data: Dict, expansion_store_data: Dict) -> Dict:
        """Compare branding between main store and expansion store"""
        try:
            # Compare logos
            logo_similarities = []
            main_logos = main_store_data.get('logos', [])
            expansion_logos = expansion_store_data.get('logos', [])
            
            for main_logo in main_logos:
                for expansion_logo in expansion_logos:
                    similarity = self.similarity_analyzer.compare_images(
                        main_logo['src'], 
                        expansion_logo['src']
                    )
                    logo_similarities.append(similarity.overall_similarity)
            
            # Compare color schemes
            color_similarity = self._compare_color_schemes(
                main_store_data.get('color_scheme'),
                expansion_store_data.get('color_scheme')
            )
            
            # Calculate overall similarity
            max_logo_similarity = max(logo_similarities) if logo_similarities else 0.0
            overall_similarity = (max_logo_similarity * 0.6) + (color_similarity * 0.4)
            
            return {
                'logo_similarity': max_logo_similarity,
                'color_similarity': color_similarity,
                'overall_similarity': overall_similarity,
                'branding_qualified': overall_similarity >= 0.7,
                'logo_identical': max_logo_similarity >= 0.9,
                'visual_branding_match': overall_similarity >= 0.8,
                'main_store_branding': main_store_data,
                'expansion_store_branding': expansion_store_data,
                'analysis_details': {
                    'logo_similarities': logo_similarities,
                    'color_comparison': self._detailed_color_comparison(
                        main_store_data.get('color_scheme'),
                        expansion_store_data.get('color_scheme')
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing branding: {e}")
            return self._fallback_branding_comparison(main_store_data, expansion_store_data)
    
    def _logo_to_dict(self, logo: LogoInfo) -> Dict:
        """Convert LogoInfo to dictionary"""
        return {
            'src': logo.src,
            'alt': logo.alt,
            'width': logo.width,
            'height': logo.height,
            'selector': logo.selector,
            'confidence': logo.confidence
        }
    
    def _color_scheme_to_dict(self, color_scheme: ColorScheme) -> Dict:
        """Convert ColorScheme to dictionary"""
        return {
            'primary_colors': color_scheme.primary_colors,
            'color_palette': color_scheme.color_palette,
            'dominant_colors': color_scheme.dominant_colors,
            'color_histogram': color_scheme.color_histogram
        }
    
    def _extract_branding_elements(self, url: str, html_content: str) -> List[str]:
        """Extract branding elements from HTML"""
        elements = []
        
        # Extract domain name
        domain = urlparse(url).netloc
        elements.append(domain)
        
        # Look for brand-related text
        brand_patterns = [
            r'<title[^>]*>([^<]+)</title>',
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
            r'<h1[^>]*>([^<]+)</h1>'
        ]
        
        for pattern in brand_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            elements.extend(matches)
        
        return elements
    
    def _calculate_analysis_confidence(self, logos: List[LogoInfo], color_scheme: Optional[ColorScheme]) -> float:
        """Calculate confidence in the analysis"""
        confidence = 0.0
        
        # Logo confidence
        if logos:
            max_logo_confidence = max(logo.confidence for logo in logos)
            confidence += max_logo_confidence * 0.6
        
        # Color scheme confidence
        if color_scheme:
            confidence += 0.4
        
        return min(1.0, confidence)
    
    def _compare_color_schemes(self, scheme1: Optional[Dict], scheme2: Optional[Dict]) -> float:
        """Compare two color schemes"""
        if not scheme1 or not scheme2:
            return 0.0
        
        try:
            # Compare dominant colors
            colors1 = scheme1.get('dominant_colors', [])
            colors2 = scheme2.get('dominant_colors', [])
            
            if not colors1 or not colors2:
                return 0.0
            
            # Calculate color distance
            similarities = []
            for color1 in colors1:
                for color2 in colors2:
                    distance = self._color_distance(color1, color2)
                    similarity = 1 - (distance / 441.67)  # Max distance in RGB space
                    similarities.append(similarity)
            
            return max(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"Error comparing color schemes: {e}")
            return 0.0
    
    def _color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two colors"""
        return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(color1, color2)))
    
    def _detailed_color_comparison(self, scheme1: Optional[Dict], scheme2: Optional[Dict]) -> Dict:
        """Detailed color comparison"""
        if not scheme1 or not scheme2:
            return {'similarity': 0.0, 'details': 'No color schemes available'}
        
        similarity = self._compare_color_schemes(scheme1, scheme2)
        
        return {
            'similarity': similarity,
            'main_colors': scheme1.get('dominant_colors', []),
            'expansion_colors': scheme2.get('dominant_colors', []),
            'color_palette_match': self._compare_color_palettes(
                scheme1.get('color_palette', []),
                scheme2.get('color_palette', [])
            )
        }
    
    def _compare_color_palettes(self, palette1: List[str], palette2: List[str]) -> float:
        """Compare color palettes"""
        if not palette1 or not palette2:
            return 0.0
        
        # Simple comparison - count matching colors
        common_colors = set(palette1).intersection(set(palette2))
        return len(common_colors) / max(len(palette1), len(palette2))
    
    def _generate_fallback_color_scheme(self, url: str) -> ColorScheme:
        """Generate fallback color scheme based on domain"""
        domain = urlparse(url).netloc.lower()
        
        # Default color schemes based on domain type
        if 'fashion' in domain or 'clothing' in domain:
            colors = [(44, 62, 80), (231, 76, 60), (236, 240, 241)]  # Fashion colors
        elif 'tech' in domain or 'electronics' in domain:
            colors = [(0, 123, 255), (108, 117, 125), (255, 255, 255)]  # Tech colors
        else:
            colors = [(0, 123, 255), (108, 117, 125), (255, 255, 255)]  # Default colors
        
        return ColorScheme(
            primary_colors=colors,
            color_palette=[f"#{r:02x}{g:02x}{b:02x}" for r, g, b in colors],
            dominant_colors=colors[:3],
            color_histogram={'hue': [], 'saturation': [], 'value': []}
        )
    
    def _fallback_branding_analysis(self, url: str) -> Dict:
        """Fallback branding analysis"""
        return {
            'logos': [],
            'color_scheme': self._generate_fallback_color_scheme(url),
            'branding_elements': [urlparse(url).netloc],
            'analysis_confidence': 0.3
        }
    
    def _fallback_branding_comparison(self, main_store_data: Dict, expansion_store_data: Dict) -> Dict:
        """Fallback branding comparison"""
        return {
            'logo_similarity': 0.0,
            'color_similarity': 0.0,
            'overall_similarity': 0.0,
            'branding_qualified': False,
            'logo_identical': False,
            'visual_branding_match': False,
            'main_store_branding': main_store_data,
            'expansion_store_branding': expansion_store_data,
            'analysis_details': {
                'logo_similarities': [],
                'color_comparison': {'similarity': 0.0, 'details': 'Fallback analysis'}
            }
        } 