import os
import json
from flask import Flask, request, jsonify, Response
from threading import Lock

app = Flask(__name__)

# Directory to store the Terraform state
# Update this path to suit your local system (Windows example)
STATE_FILE = '/app/terraform/terraform.tfstate'  # Updated to the container path
LOCK_FILE = 'D:/terraform/UAT/terraform.state.lock'  # Path to your lock file

# Simple in-memory lock (can be improved with more advanced locking mechanisms)
lock = Lock()

# Ensure the directory exists
if not os.path.exists(os.path.dirname(STATE_FILE)):
    os.makedirs(os.path.dirname(STATE_FILE))

# Root route (added)
@app.route('/')
def index():
    return jsonify({"message": "Terraform State Backend API"}), 200

# Endpoint to get the Terraform state (return as plain text for human-readable display)
@app.route('/terraform/state', methods=['GET'])
def get_state():
    if not os.path.exists(STATE_FILE):
        return jsonify({"error": "State file not found"}), 404

    # Open the state file and load it as a JSON object
    with open(STATE_FILE, 'r') as f:
        state_data = json.load(f)

    # Return the state data as plain text (formatted JSON for better readability)
    return Response(
        json.dumps(state_data, indent=4),  # Pretty-printed JSON
        mimetype='application/json'        # Sets the content type as JSON
    )

# Endpoint to update the Terraform state
@app.route('/terraform/state', methods=['PUT'])
def put_state():
    # Check if the lock file exists to prevent concurrent access
    if os.path.exists(LOCK_FILE):
        return jsonify({"error": "State file is locked"}), 423  # 423 Locked

    # Locking the state file
    with lock:
        # Create a lock file to prevent concurrent writes
        with open(LOCK_FILE, 'w') as lock_file:
            lock_file.write("locked")

        # Get the new state from the request body
        new_state = request.get_json()

        # Save the new state to the state file
        with open(STATE_FILE, 'w') as state_file:
            json.dump(new_state, state_file)

        # Remove the lock after saving the state
        os.remove(LOCK_FILE)

    return jsonify({"message": "State updated successfully"}), 200

# Endpoint to check if the state is locked
@app.route('/terraform/state/lock', methods=['GET'])
def check_lock():
    if os.path.exists(LOCK_FILE):
        return jsonify({"locked": True}), 200
    else:
        return jsonify({"locked": False}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
