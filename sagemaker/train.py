#!/usr/bin/env python3
"""
SageMaker training script for AMEX transaction classification

This script trains a multi-output classification model to predict:
- Vendor
- Expense Account
- Cost Center
- Split recommendation flag
"""

import json
import os
import argparse
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
import joblib
import boto3


class AMEXClassificationModel:
	"""Model for classifying AMEX transactions"""
	
	def __init__(self):
		self.vendor_encoder = LabelEncoder()
		self.account_encoder = LabelEncoder()
		self.cost_center_encoder = LabelEncoder()
		self.description_vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
		self.category_vectorizer = TfidfVectorizer(max_features=100)
		self.model = None
	
	def prepare_features(self, df, fit=False):
		"""Extract and prepare features from transaction data"""
		features = []
		
		# Text features from description
		if fit:
			desc_features = self.description_vectorizer.fit_transform(df['vendor_description'].fillna(''))
		else:
			desc_features = self.description_vectorizer.transform(df['vendor_description'].fillna(''))
		
		features.append(desc_features.toarray())
		
		# Text features from category
		if 'amex_category' in df.columns:
			if fit:
				cat_features = self.category_vectorizer.fit_transform(df['amex_category'].fillna(''))
			else:
				cat_features = self.category_vectorizer.transform(df['amex_category'].fillna(''))
			features.append(cat_features.toarray())
		
		# Numerical features
		numerical_features = []
		
		# Amount buckets
		amount_buckets = pd.cut(df['amount'], bins=[-np.inf, 50, 100, 500, 1000, 5000, np.inf], labels=False)
		numerical_features.append(amount_buckets.values.reshape(-1, 1))
		
		# Day of week and month (if date available)
		if 'date' in df.columns:
			df['date'] = pd.to_datetime(df['date'], errors='coerce')
			df['day_of_week'] = df['date'].dt.dayofweek.fillna(0)
			df['month'] = df['date'].dt.month.fillna(0)
			numerical_features.append(df['day_of_week'].values.reshape(-1, 1))
			numerical_features.append(df['month'].values.reshape(-1, 1))
		
		# Combine all features
		if numerical_features:
			numerical_array = np.hstack(numerical_features)
			features.append(numerical_array)
		
		return np.hstack(features)
	
	def prepare_labels(self, df, fit=False):
		"""Prepare target labels"""
		labels = {}
		
		# Vendor
		if 'classification' in df.columns:
			vendors = df['classification'].apply(lambda x: x.get('vendor', 'Unknown') if isinstance(x, dict) else 'Unknown')
		else:
			vendors = df['original_vendor'].fillna('Unknown')
		
		if fit:
			labels['vendor'] = self.vendor_encoder.fit_transform(vendors)
		else:
			labels['vendor'] = self.vendor_encoder.transform(vendors)
		
		# Expense Account
		if 'classification' in df.columns:
			accounts = df['classification'].apply(lambda x: x.get('expense_account', 'Unknown') if isinstance(x, dict) else 'Unknown')
		else:
			accounts = pd.Series(['Unknown'] * len(df))
		
		if fit:
			labels['account'] = self.account_encoder.fit_transform(accounts)
		else:
			labels['account'] = self.account_encoder.transform(accounts)
		
		# Cost Center
		if 'classification' in df.columns:
			cost_centers = df['classification'].apply(lambda x: x.get('cost_center', 'Unknown') if isinstance(x, dict) else 'Unknown')
		else:
			cost_centers = pd.Series(['Unknown'] * len(df))
		
		if fit:
			labels['cost_center'] = self.cost_center_encoder.fit_transform(cost_centers)
		else:
			labels['cost_center'] = self.cost_center_encoder.transform(cost_centers)
		
		# Combine labels into array
		y = np.column_stack([labels['vendor'], labels['account'], labels['cost_center']])
		
		return y, labels
	
	def train(self, X, y, sample_weights=None):
		"""Train the model"""
		print("Training model...")
		
		# Use RandomForest for multi-output classification
		base_estimator = RandomForestClassifier(
			n_estimators=100,
			max_depth=20,
			min_samples_split=5,
			random_state=42,
			n_jobs=-1
		)
		
		self.model = MultiOutputClassifier(base_estimator)
		
		if sample_weights is not None:
			self.model.fit(X, y, sample_weight=sample_weights)
		else:
			self.model.fit(X, y)
		
		print("Training complete!")
	
	def predict(self, X):
		"""Make predictions"""
		if self.model is None:
			raise ValueError("Model has not been trained")
		
		predictions = self.model.predict(X)
		probabilities = None
		
		# Get prediction probabilities for confidence scores
		try:
			# Get probabilities for each output
			vendor_probs = np.max([est.predict_proba(X) for est in self.model.estimators_[0].estimators_], axis=0)
			probabilities = {'confidence': np.mean(vendor_probs, axis=1)}
		except:
			probabilities = {'confidence': np.ones(len(X)) * 0.5}
		
		return predictions, probabilities
	
	def decode_predictions(self, predictions):
		"""Decode predictions to original labels"""
		decoded = {
			'vendor': self.vendor_encoder.inverse_transform(predictions[:, 0]),
			'account': self.account_encoder.inverse_transform(predictions[:, 1]),
			'cost_center': self.cost_center_encoder.inverse_transform(predictions[:, 2])
		}
		return decoded
	
	def save_model(self, model_dir):
		"""Save model and encoders"""
		print(f"Saving model to {model_dir}")
		
		os.makedirs(model_dir, exist_ok=True)
		
		# Save model
		joblib.dump(self.model, os.path.join(model_dir, 'model.joblib'))
		
		# Save encoders and vectorizers
		joblib.dump(self.vendor_encoder, os.path.join(model_dir, 'vendor_encoder.joblib'))
		joblib.dump(self.account_encoder, os.path.join(model_dir, 'account_encoder.joblib'))
		joblib.dump(self.cost_center_encoder, os.path.join(model_dir, 'cost_center_encoder.joblib'))
		joblib.dump(self.description_vectorizer, os.path.join(model_dir, 'description_vectorizer.joblib'))
		joblib.dump(self.category_vectorizer, os.path.join(model_dir, 'category_vectorizer.joblib'))
		
		print("Model saved successfully!")
	
	@classmethod
	def load_model(cls, model_dir):
		"""Load model and encoders"""
		instance = cls()
		
		instance.model = joblib.load(os.path.join(model_dir, 'model.joblib'))
		instance.vendor_encoder = joblib.load(os.path.join(model_dir, 'vendor_encoder.joblib'))
		instance.account_encoder = joblib.load(os.path.join(model_dir, 'account_encoder.joblib'))
		instance.cost_center_encoder = joblib.load(os.path.join(model_dir, 'cost_center_encoder.joblib'))
		instance.description_vectorizer = joblib.load(os.path.join(model_dir, 'description_vectorizer.joblib'))
		instance.category_vectorizer = joblib.load(os.path.join(model_dir, 'category_vectorizer.joblib'))
		
		return instance


def evaluate_model(model, X_test, y_test):
	"""Evaluate model performance"""
	predictions, probabilities = model.predict(X_test)
	
	# Calculate accuracy for each output
	vendor_accuracy = np.mean(predictions[:, 0] == y_test[:, 0])
	account_accuracy = np.mean(predictions[:, 1] == y_test[:, 1])
	cost_center_accuracy = np.mean(predictions[:, 2] == y_test[:, 2])
	
	print(f"\nModel Evaluation:")
	print(f"  Vendor Accuracy: {vendor_accuracy:.2%}")
	print(f"  Account Accuracy: {account_accuracy:.2%}")
	print(f"  Cost Center Accuracy: {cost_center_accuracy:.2%}")
	print(f"  Average Accuracy: {np.mean([vendor_accuracy, account_accuracy, cost_center_accuracy]):.2%}")
	
	return {
		'vendor_accuracy': vendor_accuracy,
		'account_accuracy': account_accuracy,
		'cost_center_accuracy': cost_center_accuracy,
		'average_accuracy': np.mean([vendor_accuracy, account_accuracy, cost_center_accuracy])
	}


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--training-data', type=str, default=os.environ.get('SM_CHANNEL_TRAINING', 'training_data/training_data.json'))
	parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR', 'model'))
	parser.add_argument('--output-data-dir', type=str, default=os.environ.get('SM_OUTPUT_DATA_DIR', 'output'))
	
	args = parser.parse_args()
	
	print("Loading training data...")
	with open(args.training_data, 'r') as f:
		data = json.load(f)
	
	df = pd.DataFrame(data)
	print(f"Loaded {len(df)} training examples")
	
	# Initialize model
	model = AMEXClassificationModel()
	
	# Prepare features
	print("Preparing features...")
	X = model.prepare_features(df, fit=True)
	y, _ = model.prepare_labels(df, fit=True)
	
	# Get sample weights if available
	sample_weights = df['weight'].values if 'weight' in df.columns else None
	
	# Split data
	X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
		X, y, sample_weights,
		test_size=0.2,
		random_state=42
	)
	
	# Train model
	model.train(X_train, y_train, sample_weights=w_train)
	
	# Evaluate
	metrics = evaluate_model(model, X_test, y_test)
	
	# Save metrics
	metrics_file = os.path.join(args.output_data_dir, 'metrics.json')
	os.makedirs(args.output_data_dir, exist_ok=True)
	with open(metrics_file, 'w') as f:
		json.dump(metrics, f, indent=2)
	
	# Save model
	model.save_model(args.model_dir)
	
	print("\nTraining complete!")
	print(f"Model saved to: {args.model_dir}")
	print(f"Metrics saved to: {metrics_file}")


if __name__ == '__main__':
	main()

