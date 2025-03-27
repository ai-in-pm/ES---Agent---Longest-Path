"""Web server for the ES Analysis tool"""

import os
import json
import base64
from typing import Dict, List, Any
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_from_directory
import matplotlib.pyplot as plt
import io
import threading
import time

# Import our modules
import es_core
import path_analysis
import data_handler
import visualization
import database
from main import analyze_project

app = Flask(__name__)

# Global variable to store analysis status
analysis_status = {
    "in_progress": False,
    "progress": 0,
    "message": "",
    "completed": False,
    "error": None,
    "results": None
}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start analysis"""
    global analysis_status
    
    # Reset status
    analysis_status = {
        "in_progress": False,
        "progress": 0,
        "message": "",
        "completed": False,
        "error": None,
        "results": None
    }
    
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({"error": "Only Excel (.xlsx) files are supported"}), 400
    
    # Save the file
    upload_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)
    
    # Start analysis in background thread
    threading.Thread(target=run_analysis, args=(file_path,)).start()
    
    return jsonify({"message": "Analysis started"})

@app.route('/status')
def get_status():
    """Return the current status of the analysis"""
    global analysis_status
    return jsonify(analysis_status)

@app.route('/results')
def get_results():
    """Return the analysis results"""
    global analysis_status
    
    if not analysis_status["completed"]:
        return jsonify({"error": "Analysis not completed yet"}), 400
    
    if analysis_status["error"]:
        return jsonify({"error": analysis_status["error"]}), 500
    
    return jsonify(analysis_status["results"])

@app.route('/results/images/<path:filename>')
def get_image(filename):
    """Serve image files"""
    return send_from_directory(os.path.join(app.root_path, 'results'), filename)

def run_analysis(file_path):
    """Run analysis in background thread and update status"""
    global analysis_status
    
    try:
        analysis_status["in_progress"] = True
        analysis_status["message"] = "Starting analysis..."
        
        # Create a custom progress callback to update status
        def progress_callback(message, progress):
            analysis_status["message"] = message
            analysis_status["progress"] = progress
        
        # Mock progress updates for demo purposes
        progress_callback("Loading project data...", 10)
        time.sleep(0.5)  # Simulate processing time
        
        # Run the analysis
        project_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(app.root_path, 'results')
        os.makedirs(output_dir, exist_ok=True)
        
        # Run actual analysis
        results = analyze_project(file_path, output_dir, project_name)
        
        # Prepare results for JSON
        results_json = prepare_results_for_json(results, output_dir)
        
        # Update status
        analysis_status["completed"] = True
        analysis_status["in_progress"] = False
        analysis_status["progress"] = 100
        analysis_status["message"] = "Analysis completed successfully"
        analysis_status["results"] = results_json
    
    except Exception as e:
        analysis_status["error"] = str(e)
        analysis_status["in_progress"] = False
        analysis_status["completed"] = True
        analysis_status["message"] = f"Analysis failed: {str(e)}"
        import traceback
        print(traceback.format_exc())

def prepare_results_for_json(results, output_dir):
    """Prepare analysis results for JSON serialization"""
    # List of image files
    image_files = [
        "pv_ev_curves.png", 
        "es_metrics.png", 
        "ieac_forecasts.png", 
        "completion_forecast.png"
    ]
    
    # Convert complex data structures for JSON
    json_safe_results = {
        "overall_metrics": [
            {"period": i, "es": m[0], "spi_t": m[1], "ieac_t": m[2]}
            for i, m in enumerate(results["overall_metrics"])
        ],
        "controlling_path": [
            {"period": i, "path": path}
            for i, path in enumerate(results["controlling_path"])
        ],
        "images": [
            {"name": img, "url": f"/results/images/{img}"}
            for img in image_files if os.path.exists(os.path.join(output_dir, img))
        ],
        "anomalies": [
            {"period": period, "path": details[0], "ieac": details[1]}
            for period, details in results["anomalies"].items()
        ],
        "final_path": results["controlling_path"][-1] if results["controlling_path"] else None,
        "final_ieac": results["overall_metrics"][-1][2] if results["overall_metrics"] else None
    }
    
    # Add path metrics
    json_safe_results["path_metrics"] = {}
    for path, metrics in results["path_metrics"].items():
        json_safe_results["path_metrics"][path] = [
            {"period": i, "es": m[0], "spi_t": m[1], "sv_t": m[2], "ieac_t": m[3]}
            for i, m in enumerate(metrics)
        ]
    
    return json_safe_results

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs(os.path.join(app.root_path, 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'results'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
    
    print("Starting ES Analysis web server...")
    app.run(debug=True, port=5000)
