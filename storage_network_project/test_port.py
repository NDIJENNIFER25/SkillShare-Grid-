from flask import Flask

# Create a Flask app
app = Flask(__name__)

# This is like a mailbox that responds when someone checks it
@app.route('/hello')
def say_hello():
    return "Hello! I'm listening on this port!"

# Tell me which port I'm running on
@app.route('/whoami')
def who_am_i():
    return f"I am running on port {app.config.get('PORT', 'unknown')}"

# Start the server
if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.config['PORT'] = port
    print(f"🚀 Starting server on port {port}")
    print(f"📬 My address is: http://127.0.0.1:{port}")
    app.run(port=port, debug=True)