import os
from flask import Flask, render_template, request
import pdfplumber
import pytesseract
from PIL import Image

# Configure Tesseract path (Windows only)
# Uncomment below and update the path if on Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
TEMPLATE_FOLDER = 'templates'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads and templates folder if they don't exist
for folder in [UPLOAD_FOLDER, TEMPLATE_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Create result.html dynamically if it doesn't exist
result_html_path = os.path.join(TEMPLATE_FOLDER, 'result.html')
if not os.path.exists(result_html_path):
    with open(result_html_path, 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Plagiarism Check Result</title>
</head>
<body>
    <h1>Plagiarism Check Result</h1>
    {% if error %}
        <p style="color: red;"><strong>Error:</strong> {{ error }}</p>
    {% else %}
        <p><strong>File 1:</strong> {{ file1_name }}</p>
        <p><strong>File 2:</strong> {{ file2_name }}</p>
        <p><strong>Similarity Score:</strong> {{ similarity_score }}%</p>

        <h3>Extracted Text from File 1:</h3>
        <textarea rows="10" cols="80" readonly>{{ text1 }}</textarea>

        <h3>Extracted Text from File 2:</h3>
        <textarea rows="10" cols="80" readonly>{{ text2 }}</textarea>
    {% endif %}
    <br><br>
    <a href="/">Check another pair of PDFs</a>
</body>
</html>''')

# Function to extract text with fallback to OCR if needed
def extract_text_from_pdf(pdf_path):
    text = ''   
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Try extracting text using pdfplumber
                page_text = page.extract_text()
                
                # If no text found, use OCR on page image
                if not page_text or page_text.strip() == '':
                    im = page.to_image(resolution=300).convert('L')
                    page_text = pytesseract.image_to_string(im)
                
                text += page_text.strip() + '\n'
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return None
    return text

# Route for uploading and processing PDFs
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get uploaded files
        file1 = request.files['file1']
        file2 = request.files['file2']

        # Check if files were uploaded
        if file1 and file2:
            file1_path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
            file2_path = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)

            # Save the uploaded files
            file1.save(file1_path)
            file2.save(file2_path)

            # Extract text from both PDFs
            text1 = extract_text_from_pdf(file1_path)
            text2 = extract_text_from_pdf(file2_path)

            # Check if text extraction was successful
            if text1 is None or text2 is None:
                return render_template('result.html', error="Error during text extraction. Please check the PDFs.")

            # Basic plagiarism check (common words count)
            common_words = set(text1.split()) & set(text2.split())
            similarity_score = (len(common_words) / max(len(set(text1.split())), 1)) * 100

            # Display result
            return render_template('result.html',
                                   file1_name=file1.filename, file2_name=file2.filename,
                                   text1=text1, text2=text2,
                                   similarity_score=round(similarity_score, 2))
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Plagiarism Checker</title>
    </head>
    <body>
        <h2>Upload PDF Files to Check for Plagiarism</h2>
        <form action="/" method="post" enctype="multipart/form-data">
            <label>Select File 1:</label><br>
            <input type="file" name="file1" accept=".pdf" required><br><br>

            <label>Select File 2:</label><br>
            <input type="file" name="file2" accept=".pdf" required><br><br>

            <input type="submit" value="Check Plagiarism">
        </form>
    </body>
    </html>
    '''

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
