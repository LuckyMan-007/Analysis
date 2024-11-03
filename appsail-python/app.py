from flask import Flask, render_template, request, redirect, url_for, g
from markupsafe import Markup
import os
import pandas as pd
import zcatalyst_sdk
from zcatalyst_sdk.catalyst_app import CatalystApp
from zcatalyst_sdk.exceptions import CatalystCredentialError

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def is_csv_file(filename):
    # Check if the file has a .csv extension
    return filename.lower().endswith('.csv')



@app.route('/analysis.htm')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    # Check if a file was selected and if it's a CSV
    if file.filename == '':
        return "No selected file"
    if not is_csv_file(file.filename):
        return "Uploaded file is not a CSV."
    
    # Save the file to the upload folder
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    
    # Load the CSV file using pandas
    try:
        data = pd.read_csv(filepath)
    except Exception as e:
        return f"An error occurred while reading the file: {e}"
    
    # Store the data for later access
    app.config['DATAFRAME'] = data
    return redirect(url_for('choose_action'))

@app.route('/choose_action')
def choose_action():
    return render_template('choose_action.html')

@app.route('/view_records', methods=['GET', 'POST'])
def view_records():
    data = app.config.get('DATAFRAME')
    if data is None:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get selected columns and number of rows
        selected_columns = request.form.getlist('columns')
        num_rows = int(request.form.get('num_rows'))
        
        # Filter the data based on selected columns and rows
        filtered_data = data[selected_columns].head(num_rows)
        
        # Convert the filtered data to HTML for display
        data_html = filtered_data.to_html(classes='table table-striped', index=False)
        return render_template('display.html', table=Markup(data_html))
    
    # For GET request, show column options and row input
    columns = data.columns.tolist()
    return render_template('view_records.html', columns=columns)

@app.route('/analysis')
def analysis():
    data = app.config.get('DATAFRAME')
    if data is None:
        return redirect(url_for('index'))
    
    # Perform data analysis and display summary statistics
    analysis_html = data.describe().to_html(classes='table table-striped', index=True)
    return render_template('analysis.html', analysis=Markup(analysis_html))

@app.route('/sdk')
def sdk():
    try:
        import zcatalyst_sdk as zcatalyst
        app = zcatalyst.initialize(req=request)
        cache_resp = app.cache().segment().put('Key', 'value')
        return cache_resp, 200
    except Exception as e:
        return 'Got exception: ' + repr(e)


# Main application entry point
if __name__ == '__main__':
    listen_port = int(os.getenv('X_ZOHO_CATALYST_LISTEN_PORT', 9000))
    app.run(host="0.0.0.0", port=listen_port)