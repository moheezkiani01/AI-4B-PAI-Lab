from flask import Flask, request, send_file, render_template_string
import pandas as pd
import requests
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def scrape_emails(url):
    """Scrape emails from a single URL"""
    if not isinstance(url, str) or not url.startswith("http"):
        return "Invalid URL"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        emails = set(re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            response.text
        ))
        return ", ".join(emails) if emails else "No email found"
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return "Error fetching URL"


def scrape_emails_concurrent(urls, max_workers=5):
    """Scrape emails from a list of URLs concurrently"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(scrape_emails, urls))
    return results


HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Email Scraper App</title>
    <style>
        body {
            font-family: Arial;
            background: #f4f6f8;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .box {
            background: white;
            padding: 30px;
            width: 420px;
            border-radius: 10px;
            box-shadow: 0 0 15px #ccc;
            text-align: center;
        }
        h2 { color: #333; }
        input[type=file] {
            margin: 15px 0;
        }
        button {
            padding: 10px 20px;
            background: #007bff;
            border: none;
            color: white;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>

<div class="box">
    <h2>Email Scraper</h2>
    <p>Upload Excel or CSV file containing URLs (column name should contain "URL")</p>

    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" required><br>
        <button type="submit">Scrape Emails</button>
    </form>
</div>

</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return "No file uploaded", 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Read Excel or CSV
        try:
            if file.filename.endswith(".xlsx"):
                df = pd.read_excel(file_path)
            elif file.filename.endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                return "Invalid file type. Upload Excel or CSV.", 400
        except Exception as e:
            return f"Error reading file: {e}"

        # Detect URL column dynamically
        url_columns = [col for col in df.columns if 'url' in col.lower()]
        if not url_columns:
            return "No URL column found in file", 400
        url_column = url_columns[0]

        # Drop invalid/missing URLs
        urls = df[url_column].dropna().astype(str).tolist()

        # Scrape emails concurrently
        emails = scrape_emails_concurrent(urls)

        # Assign emails back to DataFrame
        df["Emails"] = pd.Series(emails)

        # Save output file
        timestamp = int(time.time())
        output_filename = f"emails_output_{timestamp}.xlsx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        df.to_excel(output_path, index=False)

        return send_file(
            output_path,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    return render_template_string(HTML_PAGE)


if __name__ == "__main__":
    app.run(debug=True)
