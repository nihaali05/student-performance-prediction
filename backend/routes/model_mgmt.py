import os
import json
from flask import Blueprint, jsonify
from auth_middleware import token_required
from ml.train import train_and_evaluate

model_mgmt_bp = Blueprint('model_mgmt', __name__)

@model_mgmt_bp.route('/status', methods=['GET'])
@token_required(allowed_roles=['admin', 'faculty'])
def get_model_status(current_user):
    metadata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'model_metadata.json')
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        return jsonify(metadata), 200
    else:
        # Run training to generate metadata
        metadata = train_and_evaluate()
        return jsonify(metadata), 200

@model_mgmt_bp.route('/retrain', methods=['POST'])
@token_required(allowed_roles=['admin'])
def retrain_models(current_user):
    try:
        metadata = train_and_evaluate()
        return jsonify({
            'message': 'ML Models retrained successfully!',
            'best_model': metadata['best_model_name'],
            'best_r2': metadata['best_r2'],
            'metadata': metadata
        }), 200
    except Exception as e:
        return jsonify({'message': f'Retraining failed: {str(e)}'}), 500
