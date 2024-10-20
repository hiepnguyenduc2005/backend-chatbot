import os
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from server.main_chat import generate_answer, extract_text_from_pdf


FLASK_RUN_HOST = os.environ.get('FLASK_RUN_HOST', "localhost")
FLASK_RUN_PORT = os.environ.get('FLASK_RUN_PORT', "8000")

UPLOAD_FOLDER = "data"
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """Check if the uploaded file is allowed (PDF only)."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return "Welcome to the PDF Chatbot!"


# @app.route('/upload_file', methods=["POST"])
# def upload_file():
#     global pdf_text
#     if 'file' not in request.files:
#         return jsonify({"message": "No file uploaded", "status": "False"}), 400
#     file = request.files['file']
    
#     if file.filename == '':
#         return jsonify({"message": "No selected file", "status": "False"}), 400
    
#     if file and allowed_file(file.filename):
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#         file.save(file_path)

#         # Extract text from the uploaded PDF
#         pdf_text = extract_text_from_pdf(file_path)

#         intro_message = "PDF successfully uploaded and processed. You can now start chatting."
#         return jsonify({"message": intro_message, "pdf_text": pdf_text, "status": "True"}), 200
#     else:
#         return jsonify({"message": "Invalid file type. Only PDF files are allowed.", "status": "False"}), 400
    
    
@app.route('/chat', methods=["POST"]) 
def chat():
    message = request.json.get("message")
    return Response(generate_answer(message),content_type="text/plain"),200
    
if __name__ == "__main__":
    app.run(host=FLASK_RUN_HOST,port=FLASK_RUN_PORT,debug=True)