import os
import csv
import traceback
from wsgiref.simple_server import make_server

def application(environ, start_response):
    try:
        # Directory containing CSV files
        csv_dir = "/srv/www/htdocs/patching/reports/raw/2025-January"

        # Get the PATH_INFO and strip the `/web2` prefix
        raw_path_info = environ.get('PATH_INFO', '/')
        path_info = raw_path_info.lstrip('/web2').strip('/')

        if path_info == "":  # Home page: List CSV files
            # List all CSV files in the directory
            files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]

            # Generate an HTML page to display file links
            html = "<html><head><title>CSV Files</title></head><body>"
            html += "<h1>Available CSV Files</h1><ul>"
            for file in files:
                html += f'<li><a href="/web2/{file}">{file}</a></li>'
            html += "</ul></body></html>"

            start_response('200 OK', [('Content-Type', 'text/html')])
            return [html.encode("utf-8")]

        elif path_info.endswith(".csv"):  # Handle CSV file display
            file_path = os.path.join(csv_dir, path_info)

            if not os.path.exists(file_path):  # Handle file not found
                start_response('404 Not Found', [('Content-Type', 'text/plain')])
                return [b"File not found"]

            # Read CSV file and generate HTML table
            html = "<html><head><title>CSV Viewer</title></head><body>"
            html += f"<h1>{path_info}</h1><table border='1'>"

            with open(file_path, 'r') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"

            html += "</table></body></html>"

            start_response('200 OK', [('Content-Type', 'text/html')])
            return [html.encode("utf-8")]

        else:  # Handle unknown routes
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b"Not found"]

    except Exception as e:
        # Display detailed error information
        error_html = f"<html><head><title>Error</title></head><body>"
        error_html += "<h1>Application Error</h1>"
        error_html += f"<pre>{traceback.format_exc()}</pre>"
        error_html += "</body></html>"

        start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
        return [error_html.encode("utf-8")]
# Run the WSGI server
if __name__ == "__main__":

    print("Serving on http://localhost:8000")
    with make_server('0.0.0.0', 8000, application) as server:
        server.serve_forever()
