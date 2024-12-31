from flask import Flask, Response, stream_with_context
import time

app = Flask(__name__)

def generate_stream(id: str):
    """
    A generator function that yields data chunks.
    For demonstration, it sends incremental data every second.
    """
    for i in range(1, 11):
        yield f"Data chunk {i} for ID {id}\n"
        time.sleep(1)  # Simulate delay between data chunks

@app.route('/api/<id>', methods=['GET'])
def stream_api(id: str):
    """
    Stream data to the client for the given ID.
    """
    return Response(
        stream_with_context(generate_stream(id)),
        mimetype='text/plain'  # Change MIME type as needed
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)