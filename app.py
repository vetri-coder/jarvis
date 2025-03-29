from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=1000000, backupCount=3),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/process": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*", "http://192.168.*"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Load environment variables
load_dotenv()

# Validate environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.critical("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY is required")

# Initialize AI model
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        'gemini-pro',
        generation_config={
            "temperature": 0.7,
            "max_output_tokens": 2048,
            "top_p": 0.9
        },
        safety_settings=[
            {
                "category": "HARM_CATEGORY_DANGEROUS",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            }
        ]
    )
    logger.info("AI model configured successfully")
except Exception as e:
    logger.critical(f"AI configuration failed: {str(e)}")
    raise

@app.before_request
def before_request():
    request.start_time = time.time()
    if request.method == 'OPTIONS':
        return jsonify({'status': 'preflight'}), 200

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    response.headers['X-Response-Time'] = f"{duration:.3f}s"
    response.headers['Server'] = "JARVIS/1.0"
    response.headers['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    return response

@app.route('/process', methods=['POST'])
def process():
    try:
        logger.debug(f"Incoming request from {request.remote_addr}")
        logger.debug(f"Headers: {dict(request.headers)}")

        if not request.is_json:
            logger.error("Invalid content type")
            return jsonify({
                'error': 'Content-Type must be application/json',
                'status': 'error'
            }), 415

        try:
            data = request.get_json(force=True, silent=True)
            if data is None:
                raise ValueError("Invalid JSON format")
        except Exception as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return jsonify({
                'error': 'Invalid JSON format',
                'status': 'error'
            }), 400

        if not data:
            logger.error("Empty payload received")
            return jsonify({
                'error': 'No data received',
                'status': 'error'
            }), 400
            
        if 'query' not in data or not isinstance(data['query'], str):
            logger.error("Invalid query parameter")
            return jsonify({
                'error': 'Valid query parameter is required',
                'status': 'error'
            }), 400
            
        query = data['query'].strip()
        if not query:
            logger.error("Empty query string")
            return jsonify({
                'error': 'Query cannot be empty',
                'status': 'error'
            }), 400
            
        logger.info(f"Processing query: {query[:100]}...")  # Log first 100 chars
        
        try:
            start_time = time.time()
            response = model.generate_content(
                query,
                request_options={"timeout": 10}
            )
            processing_time = time.time() - start_time
            
            if not response.text:
                raise ValueError("Empty response from AI model")
                
            ai_response = response.text
            logger.info(f"Generated response in {processing_time:.2f}s")
            logger.debug(f"Full response: {ai_response}")
            
            return jsonify({
                'response': ai_response,
                'status': 'success',
                'model': 'gemini-1.5-flash',
                'processing_time': f"{processing_time:.2f}s",
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as ai_error:
            logger.error(f"AI processing error: {str(ai_error)}")
            return jsonify({
                'error': 'AI processing failed',
                'details': str(ai_error),
                'status': 'error'
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error'
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        'error': 'Method not allowed',
        'status': 'error'
    }), 405

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    try:
        port = int(os.getenv('PORT', 5000))
        logger.info(f"Starting server on port {port}")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}")
        raise