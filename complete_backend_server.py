#!/usr/bin/env python3
"""
Complete Python Backend Server for Chat Message Filter
Works with the existing HTML demo page to provide full functionality
Run this to get a fully functional web-based chat filter system
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string
import json
import os
import sys
import webbrowser
import threading
import time
from datetime import datetime

# Import our chat filter module
try:
    from chat_filter import ChatMessageFilter, FilterLevel, create_sample_curse_words_file
except ImportError:
    print("❌ chat_filter.py not found. Please ensure it's in the same directory.")
    sys.exit(1)

app = Flask(__name__)

# Global filter instance
filter_instance = None

def initialize_filter():
    """Initialize the chat filter with sample data"""
    global filter_instance
    
    # DO NOT create sample file - use existing curse_words.json
    if not os.path.exists("curse_words.json"):
        print("❌ curse_words.json not found!")
        print("   Please create curse_words.json with your words")
        sys.exit(1)
    
    # Initialize filter with YOUR curse_words.json
    filter_instance = ChatMessageFilter("curse_words.json")
    print(f"✅ Filter initialized with {len(filter_instance.curse_words)} words")
    print(f"   Loaded words: {list(filter_instance.curse_words)}")

@app.route('/')
def index():
    """Serve the main demo page"""
    try:
        with open('demo.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <h1>Demo HTML file not found</h1>
        <p>Please make sure 'demo.html' is in the same directory as this server.</p>
        <p>You can create it by running the coverage generator script.</p>
        """

@app.route('/api/filter', methods=['POST'])
def filter_message_api():
    """API endpoint to filter a message"""
    try:
        data = request.get_json()
        print(f"📥 Received data: {data}")  # Debug
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        filter_level = data.get('filter_level', 'moderate')
        replacement_char = data.get('replacement_char', '*')
        preserve_length = data.get('preserve_length', True)
        
        print(f"🔍 Filtering message: '{message}' with level: {filter_level}")  # Debug
        
        # Set filter level
        level_map = {
            'strict': FilterLevel.STRICT,
            'moderate': FilterLevel.MODERATE,
            'lenient': FilterLevel.LENIENT
        }
        
        if filter_level in level_map:
            filter_instance.set_filter_level(level_map[filter_level])
        
        # Set replacement character
        if replacement_char and len(replacement_char) == 1:
            filter_instance.set_replacement_char(replacement_char)
        
        # Get comprehensive report
        report = filter_instance.get_filter_report(message)
        print(f"📤 Sending response: {report}")  # Debug
        
        # Add additional processing info
        report['processing_time'] = datetime.now().isoformat()
        report['filter_settings'] = {
            'level': filter_level,
            'replacement_char': replacement_char,
            'preserve_length': preserve_length
        }
        
        return jsonify(report)
        
    except Exception as e:
        print(f"❌ Error in filter_message_api: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch_filter', methods=['POST'])
def batch_filter_api():
    """API endpoint to filter multiple messages"""
    try:
        data = request.get_json()
        
        if not data or 'messages' not in data:
            return jsonify({'error': 'Messages array is required'}), 400
        
        messages = data['messages']
        if not isinstance(messages, list):
            return jsonify({'error': 'Messages must be an array'}), 400
        
        filter_level = data.get('filter_level', 'moderate')
        replacement_char = data.get('replacement_char', '*')
        
        # Set filter settings
        level_map = {
            'strict': FilterLevel.STRICT,
            'moderate': FilterLevel.MODERATE,
            'lenient': FilterLevel.LENIENT
        }
        
        if filter_level in level_map:
            filter_instance.set_filter_level(level_map[filter_level])
        
        if replacement_char and len(replacement_char) == 1:
            filter_instance.set_replacement_char(replacement_char)
        
        # Process all messages
        results = []
        for i, message in enumerate(messages):
            if isinstance(message, str):
                report = filter_instance.get_filter_report(message)
                report['message_index'] = i
                results.append(report)
            else:
                results.append({
                    'message_index': i,
                    'error': 'Invalid message type',
                    'original_message': str(message),
                    'filtered_message': '',
                    'is_clean': False
                })
        
        return jsonify({
            'results': results,
            'total_processed': len(results),
            'processing_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get filter statistics"""
    try:
        stats = filter_instance.get_statistics()
        stats['timestamp'] = datetime.now().isoformat()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/curse_words', methods=['GET'])
def get_curse_words():
    """Get list of curse words"""
    try:
        words = sorted(list(filter_instance.curse_words))
        return jsonify({
            'words': words,
            'count': len(words),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/curse_words', methods=['POST'])
def add_curse_word():
    """Add a new curse word"""
    try:
        data = request.get_json()
        
        if not data or 'word' not in data:
            return jsonify({'error': 'Word is required'}), 400
        
        word = data['word']
        success = filter_instance.add_curse_word(word)
        
        return jsonify({
            'success': success,
            'word': word,
            'message': 'Word added successfully' if success else 'Word already exists',
            'total_words': len(filter_instance.curse_words)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/curse_words/<word>', methods=['DELETE'])
def remove_curse_word(word):
    """Remove a curse word"""
    try:
        success = filter_instance.remove_curse_word(word)
        
        return jsonify({
            'success': success,
            'word': word,
            'message': 'Word removed successfully' if success else 'Word not found',
            'total_words': len(filter_instance.curse_words)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset_statistics', methods=['POST'])
def reset_statistics():
    """Reset filter statistics"""
    try:
        filter_instance.reset_statistics()
        return jsonify({
            'success': True,
            'message': 'Statistics reset successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_words', methods=['GET'])
def export_words():
    """Export curse words as JSON"""
    try:
        words = sorted(list(filter_instance.curse_words))
        return jsonify({
            'words': words,
            'count': len(words),
            'exported_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_examples', methods=['GET'])
def get_test_examples():
    """Get predefined test examples for demonstration"""
    examples = [
        {
            'category': 'Clean Messages',
            'messages': [
                "Hello world! How are you today?",
                "This is a beautiful sunny day ☀️",
                "I love programming and coding!",
                "Let's have a great conversation",
                "Technology is amazing these days"
            ]
        },
        {
            'category': 'Basic Profanity',
            'messages': [
                "You are so damn stupid!",
                "This is a hell of a problem",
                "That's just crap, honestly",
                "Don't be such an idiot",
                "This situation really sucks"
            ]
        },
        {
            'category': 'Leetspeak & Variations',
            'messages': [
                "D4mn th1s 1s b4d",
                "What the h3ll is this?",
                "5tup1d k1d5 th353 d4y5",
                "Th@t'5 ju5t cr@p",
                "D0n't b3 4n 1d10t"
            ]
        },
        {
            'category': 'Mixed Content',
            'messages': [
                "This is a damn good movie, honestly",
                "Hell yeah, that's awesome! 🎉",
                "Some clean words and some stupid dirty ones",
                "What a beautiful day, damn right!",
                "That's pretty cool, not gonna lie"
            ]
        }
    ]
    
    return jsonify({
        'examples': examples,
        'total_categories': len(examples),
        'generated_at': datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'filter_ready': filter_instance is not None,
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Static file serving
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

def open_browser():
    """Open the browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

def run_server(host='localhost', port=5000, debug=False, open_browser_tab=True):
    """Run the Flask server"""
    
    print("🚀 Starting Chat Message Filter Web Server")
    print("=" * 50)
    
    # Initialize the filter
    initialize_filter()
    
    print(f"🌐 Server starting at http://{host}:{port}")
    print("📱 API endpoints available:")
    print("   POST /api/filter - Filter a single message")
    print("   POST /api/batch_filter - Filter multiple messages")
    print("   GET  /api/statistics - Get filter statistics")
    print("   GET  /api/curse_words - Get curse words list")
    print("   POST /api/curse_words - Add curse word")
    print("   DELETE /api/curse_words/<word> - Remove curse word")
    print("   GET  /api/test_examples - Get test examples")
    print("   GET  /health - Health check")
    
    if open_browser_tab:
        # Open browser in a separate thread
        threading.Thread(target=open_browser, daemon=True).start()
    
    print(f"\n✅ Server ready! Visit http://{host}:{port} to use the chat filter")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Chat Message Filter Web Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    run_server(
        host=args.host, 
        port=args.port, 
        debug=args.debug,
        open_browser_tab=not args.no_browser
    )