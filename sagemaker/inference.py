#!/usr/bin/env python3
"""
SageMaker inference script for AMEX transaction classification

This script handles model loading and predictions for deployed endpoints
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from train import AMEXClassificationModel


def model_fn(model_dir):
	"""
	Load the model for inference
	
	Args:
		model_dir: Directory where model artifacts are stored
	
	Returns:
		Loaded model instance
	"""
	print(f"Loading model from {model_dir}")
	model = AMEXClassificationModel.load_model(model_dir)
	return model


def input_fn(request_body, content_type='application/json'):
	"""
	Parse and prepare input data
	
	Args:
		request_body: The request body
		content_type: Content type of the request
	
	Returns:
		Parsed input data as DataFrame
	"""
	if content_type == 'application/json':
		data = json.loads(request_body)
		
		# Handle single transaction or batch
		if isinstance(data, dict):
			data = [data]
		
		df = pd.DataFrame(data)
		return df
	else:
		raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data, model):
	"""
	Make predictions
	
	Args:
		input_data: Prepared input DataFrame
		model: Loaded model instance
	
	Returns:
		Predictions
	"""
	# Prepare features
	X = model.prepare_features(input_data, fit=False)
	
	# Make predictions
	predictions, probabilities = model.predict(X)
	
	# Decode predictions
	decoded = model.decode_predictions(predictions)
	
	# Format output
	results = []
	for i in range(len(input_data)):
		result = {
			'vendor': decoded['vendor'][i],
			'expense_account': decoded['account'][i],
			'cost_center': decoded['cost_center'][i],
			'confidence': float(probabilities['confidence'][i]) if probabilities else 0.5,
			'split_recommended': False  # TODO: Add split recommendation logic
		}
		results.append(result)
	
	return results


def output_fn(predictions, content_type='application/json'):
	"""
	Format predictions for output
	
	Args:
		predictions: Model predictions
		content_type: Desired output content type
	
	Returns:
		Formatted output
	"""
	if content_type == 'application/json':
		return json.dumps(predictions)
	else:
		raise ValueError(f"Unsupported content type: {content_type}")






