from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Static information metric for Sentro workload
metrics.info('sentro_app_info', 'Sentro Application Information', version='1.0.0')

@app.route('/')
def home():
    return jsonify({"status": "success", "message": "Welcome to the Sentro Workload API!"}), 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
