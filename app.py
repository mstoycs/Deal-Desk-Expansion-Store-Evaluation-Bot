#!/usr/bin/env python3
"""
Flask Web Application for Expansion Store Evaluation Bot
"""

from flask import Flask, render_template, request, jsonify, flash
from flask_cors import CORS
from expansion_store_evaluator import ExpansionStoreEvaluator, StoreInfo, EvaluationCriteria
from product_extractor import background_extractor
import json
import logging
import signal
import threading
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

# Enable CORS for localhost development
CORS(app, 
     origins=[
         "http://localhost:*",
         "http://127.0.0.1:*",
         "file://*"  # Allow local file access
     ],
     methods=['GET', 'POST', 'OPTIONS'],
     allow_headers=['Content-Type', 'Accept'],
     supports_credentials=False)

# Initialize the evaluator
evaluator = ExpansionStoreEvaluator()

# Global timeout for evaluation (30 seconds)
EVALUATION_TIMEOUT = 30

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Evaluation timed out")

@app.route('/')
def index():
    """Main page with the evaluation form"""
    return render_template('index.html')

@app.route('/test', methods=['GET'])
def test():
    """Simple test endpoint"""
    return jsonify({'status': 'ok', 'message': 'Eddie is working'})

@app.route('/test-store-info', methods=['POST'])
def test_store_info():
    """Test if extract_store_info works properly"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        logger.info(f"Testing extract_store_info for {url}")
        
        from expansion_store_evaluator import ExpansionStoreEvaluator
        test_evaluator = ExpansionStoreEvaluator()
        
        logger.info("Extracting store info...")
        store_info = test_evaluator.extract_store_info(url)
        
        logger.info("Store info extracted successfully")
        return jsonify({
            'status': 'ok',
            'url': store_info.url,
            'store_name': store_info.store_name,
            'store_type': store_info.store_type.value,
            'business_type': store_info.business_type.value
        })
        
    except Exception as e:
        logger.error(f"Error extracting store info: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/test-evaluator', methods=['GET'])
def test_evaluator():
    """Test if ExpansionStoreEvaluator initializes properly"""
    try:
        logger.info("Testing ExpansionStoreEvaluator initialization...")
        from expansion_store_evaluator import ExpansionStoreEvaluator
        
        logger.info("Creating evaluator instance...")
        test_evaluator = ExpansionStoreEvaluator()
        
        logger.info("Evaluator created successfully")
        return jsonify({
            'status': 'ok',
            'message': 'ExpansionStoreEvaluator initialized successfully',
            'enhanced_analysis': hasattr(test_evaluator, 'enhanced_analyzer'),
            'product_extraction': hasattr(test_evaluator, 'product_extractor')
        })
        
    except Exception as e:
        logger.error(f"Error initializing evaluator: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/evaluate-simple', methods=['POST'])
def evaluate_simple():
    """Minimal evaluation endpoint for testing"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        main_store_url = data.get('main_store_url', '').strip()
        expansion_store_url = data.get('expansion_store_url', '').strip()
        
        if not main_store_url or not expansion_store_url:
            return jsonify({'error': 'Both URLs required'}), 400
        
        # Simple evaluation without complex features
        from urllib.parse import urlparse
        
        main_domain = urlparse(main_store_url).netloc
        expansion_domain = urlparse(expansion_store_url).netloc
        
        # Simple logic: if domains are similar, it's qualified
        main_words = set(main_domain.split('.'))
        expansion_words = set(expansion_domain.split('.'))
        
        if main_words.intersection(expansion_words):
            result = "qualified"
        else:
            result = "unqualified"
        
        return jsonify({
            'result': result,
            'main_domain': main_domain,
            'expansion_domain': expansion_domain,
            'message': 'Simple evaluation completed'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/evaluate', methods=['POST'])
def evaluate():
    """API endpoint for evaluating expansion stores"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        main_store_url = data.get('main_store_url', '').strip()
        expansion_store_url = data.get('expansion_store_url', '').strip()
        main_store_type = data.get('main_store_type', 'd2c').strip()
        expansion_store_type = data.get('expansion_store_type', 'd2c').strip()
        
        if not main_store_url or not expansion_store_url:
            return jsonify({'error': 'Both main_store_url and expansion_store_url are required'}), 400
        
        logger.info(f"Starting evaluation for {main_store_url} -> {expansion_store_url}")
        
        # Perform evaluation directly (simplified approach)
        report = evaluator.evaluate_expansion_store(
            main_store_url,
            expansion_store_url,
            main_store_type=main_store_type,
            expansion_store_type=expansion_store_type
        )
        
        logger.info("Evaluation completed, preparing response")
        
        response_data = {
            'result': report.result.value,
            'confidence_score': float(report.confidence_score),
            'store_info': {
                'url': report.store_info.url,
                'store_name': report.store_info.store_name,
                'store_type': report.store_info.store_type.value,
                'business_type': report.store_info.business_type.value,
                'language': report.store_info.language,
                'currency': report.store_info.currency,
                'branding_elements': report.store_info.branding_elements or [],
                'goods_services': report.store_info.goods_services or [],
                'products': report.store_info.products or []
            },
            'criteria_met': {k: bool(v) for k, v in report.criteria_met.items()},
            'criteria_analysis': {
                key: {
                    'criteria_name': str(analysis.criteria_name),
                    'criteria_met': bool(analysis.criteria_met),
                    'summary': str(analysis.summary),
                    'main_store_evidence': serialize_evidence(analysis.main_store_evidence),
                    'expansion_store_evidence': serialize_evidence(analysis.expansion_store_evidence),
                    'evaluation_details': serialize_evidence(analysis.evaluation_details)
                }
                for key, analysis in report.criteria_analysis.items()
            },
            'reasons': [str(reason) for reason in report.reasons],
            'recommendations': [str(rec) for rec in report.recommendations],
            'product_analysis': serialize_evidence(report.product_analysis) if report.product_analysis else None
        }
        
        logger.info("Evaluation completed successfully")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Evaluation failed: {str(e)}'}), 500

def serialize_evidence(evidence):
    """Helper method to serialize evidence data for JSON response"""
    if evidence is None:
        return None
    
    if isinstance(evidence, dict):
        serialized = {}
        for key, value in evidence.items():
            serialized[str(key)] = serialize_value(value)
        return serialized
    
    elif isinstance(evidence, list):
        return [serialize_value(item) for item in evidence]
    
    else:
        return serialize_value(evidence)

def serialize_value(value):
    """Helper method to serialize individual values for JSON"""
    if value is None:
        return None
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, list):
        return [serialize_value(item) for item in value]
    elif isinstance(value, dict):
        return {str(k): serialize_value(v) for k, v in value.items()}
    elif hasattr(value, '__dict__'):
        # Handle objects with __dict__ attribute
        return str(value)
    else:
        # Convert any other type to string
        return str(value)

@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """Alternative API endpoint for programmatic access"""
    return evaluate()

@app.route('/about')
def about():
    """About page explaining the evaluation criteria"""
    return render_template('about.html')

@app.route('/examples')
def examples():
    """Examples page showing sample evaluations"""
    return render_template('examples.html')

@app.route('/debug-products', methods=['POST'])
def debug_products():
    """Debug endpoint to test product extraction"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        # Initialize evaluator
        evaluator = ExpansionStoreEvaluator()
        
        # Test product extraction
        products = evaluator._extract_products(url)
        
        return jsonify({
            'url': url,
            'products_found': len(products),
            'products': products[:10],  # First 10 products
            'extraction_method': 'sophisticated' if evaluator.use_real_product_extraction else 'fallback'
        })
        
    except Exception as e:
        logger.error(f"Debug products error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug-basic', methods=['POST'])
def debug_basic():
    """Basic debug endpoint to test page fetching"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse
        
        # Try to fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return jsonify({
                'error': f'Failed to fetch page: {response.status_code}',
                'url': url
            })
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Count different types of links
        all_links = soup.find_all('a', href=True)
        
        # Analyze URL patterns
        url_patterns = {}
        domain = urlparse(url).netloc
        
        for link in all_links:
            href = link.get('href', '')
            if href and not href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                # Extract path pattern
                if href.startswith('http') and domain not in href:
                    continue  # Skip external links
                
                if href.startswith('/'):
                    path_parts = [part for part in href.split('/') if part and '?' not in part]
                    if path_parts:
                        pattern = '/' + path_parts[0] + '/'
                        url_patterns[pattern] = url_patterns.get(pattern, 0) + 1
        
        # Sort patterns by frequency
        sorted_patterns = sorted(url_patterns.items(), key=lambda x: x[1], reverse=True)
        
        # Look for specific e-commerce patterns
        ecommerce_patterns = [
            '/product', '/products', '/item', '/items', '/shop', '/store', 
            '/catalog', '/category', '/collection', '/collections', '/p/',
            '/buy', '/view', '/detail', '/details'
        ]
        
        found_ecommerce = {}
        for pattern in ecommerce_patterns:
            matching_links = [link.get('href') for link in all_links if pattern in link.get('href', '').lower()]
            if matching_links:
                found_ecommerce[pattern] = {
                    'count': len(matching_links),
                    'samples': matching_links[:3]
                }
        
        return jsonify({
            'url': url,
            'status_code': response.status_code,
            'page_title': soup.find('title').get_text() if soup.find('title') else 'No title',
            'total_links': len(all_links),
            'url_patterns': dict(sorted_patterns[:10]),  # Top 10 patterns
            'ecommerce_patterns': found_ecommerce,
            'sample_links': [link.get('href') for link in all_links[:15]]
        })
        
    except Exception as e:
        logger.error(f"Debug basic error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('FLASK_PORT', 5001))  # Default 5001, but configurable via FLASK_PORT env var
    app.run(debug=True, host='0.0.0.0', port=port) 