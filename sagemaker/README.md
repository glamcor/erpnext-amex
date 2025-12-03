# AMEX Transaction Classification - SageMaker Setup

This directory contains scripts for training and deploying the ML model on AWS SageMaker.

## Prerequisites

1. AWS account with SageMaker access
2. IAM role with permissions for SageMaker, S3
3. Historical transaction data from NetSuite in S3
4. Python 3.10+ with boto3, sagemaker SDK

## Step 1: Transform Training Data

First, transform your historical NetSuite data to ERPNext format:

```bash
# Install dependencies
pip install boto3 pandas

# Create mapping configuration (customize based on your needs)
cp ../scripts/mapping_config.example.json ../scripts/mapping_config.json
# Edit mapping_config.json with your actual mappings

# Run transformation
python ../scripts/transform_netsuite_to_erpnext.py \
  --s3-bucket your-bucket-name \
  --s3-prefix netsuite/transactions/ \
  --mapping-config ../scripts/mapping_config.json \
  --output-dir training_data
```

This will create `training_data/training_data.json` with transformed data.

## Step 2: Upload Training Data to S3

```bash
# Upload training data to S3
aws s3 cp training_data/training_data.json s3://your-bucket/amex-ml/training/training_data.json
```

## Step 3: Create SageMaker Training Job

You can either use the AWS Console or boto3 to create a training job.

### Option A: Using SageMaker Notebook

Create a Jupyter notebook with:

```python
import sagemaker
from sagemaker.sklearn import SKLearn

# Initialize session
sagemaker_session = sagemaker.Session()
role = 'arn:aws:iam::YOUR_ACCOUNT:role/SageMakerRole'

# Define SKLearn estimator
sklearn_estimator = SKLearn(
    entry_point='train.py',
    source_dir='.',
    role=role,
    instance_type='ml.m5.xlarge',
    framework_version='1.2-1',
    py_version='py3',
    hyperparameters={
        'n_estimators': 100,
        'max_depth': 20
    }
)

# Train
sklearn_estimator.fit({'training': 's3://your-bucket/amex-ml/training/'})
```

### Option B: Using AWS CLI

```bash
# Create training job config
aws sagemaker create-training-job \
  --training-job-name amex-classifier-$(date +%Y%m%d-%H%M%S) \
  --role-arn arn:aws:iam::YOUR_ACCOUNT:role/SageMakerRole \
  --algorithm-specification \
    TrainingImage=683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3 \
    TrainingInputMode=File \
  --input-data-config '[
    {
      "ChannelName": "training",
      "DataSource": {
        "S3DataSource": {
          "S3DataType": "S3Prefix",
          "S3Uri": "s3://your-bucket/amex-ml/training/",
          "S3DataDistributionType": "FullyReplicated"
        }
      }
    }
  ]' \
  --output-data-config S3OutputPath=s3://your-bucket/amex-ml/output \
  --resource-config \
    InstanceType=ml.m5.xlarge \
    InstanceCount=1 \
    VolumeSizeInGB=10
```

## Step 4: Deploy Model to Endpoint

After training completes:

```python
# Deploy the model
predictor = sklearn_estimator.deploy(
    initial_instance_count=1,
    instance_type='ml.t2.medium',
    endpoint_name='amex-classifier-endpoint'
)
```

Or using AWS CLI:

```bash
# Create model
aws sagemaker create-model \
  --model-name amex-classifier-model \
  --primary-container \
    Image=683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3 \
    ModelDataUrl=s3://your-bucket/amex-ml/output/model.tar.gz \
  --execution-role-arn arn:aws:iam::YOUR_ACCOUNT:role/SageMakerRole

# Create endpoint config
aws sagemaker create-endpoint-config \
  --endpoint-config-name amex-classifier-config \
  --production-variants \
    VariantName=main \
    ModelName=amex-classifier-model \
    InitialInstanceCount=1 \
    InstanceType=ml.t2.medium

# Create endpoint
aws sagemaker create-endpoint \
  --endpoint-name amex-classifier-endpoint \
  --endpoint-config-name amex-classifier-config
```

## Step 5: Configure ERPNext

In ERPNext AMEX Integration Settings:

1. Enable ML Classification
2. Set SageMaker Endpoint Name: `amex-classifier-endpoint`
3. Enter AWS Access Key ID and Secret Access Key
4. Set AWS Region (e.g., `us-east-1`)
5. Set ML Auto Accept Threshold (e.g., `0.90` for 90% confidence)

## Testing the Endpoint

Test with sample data:

```python
import boto3
import json

runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')

payload = {
    'vendor_description': 'google ads',
    'amount': 500.00,
    'amex_category': 'Business Services-Advertising Services',
    'date': '2025-11-22',
    'card_member': 'John Doe'
}

response = runtime.invoke_endpoint(
    EndpointName='amex-classifier-endpoint',
    ContentType='application/json',
    Body=json.dumps(payload)
)

result = json.loads(response['Body'].read())
print(json.dumps(result, indent=2))
```

Expected output:

```json
{
  "vendor": "Google Ads",
  "expense_account": "Advertising - Online - Your Company",
  "cost_center": "Marketing - Paid Ads - Google - Your Company",
  "confidence": 0.95,
  "split_recommended": false
}
```

## Model Retraining

To retrain the model with new data:

1. Export classified transactions from ERPNext
2. Combine with historical training data
3. Run transformation script with updated data
4. Create new training job
5. Deploy updated model
6. Update endpoint name in ERPNext settings

## Cost Optimization

- Use `ml.t2.medium` or `ml.t2.small` for endpoint (cost-effective for low traffic)
- Consider using SageMaker Serverless Inference for sporadic usage
- Set up auto-scaling if needed
- Monitor CloudWatch metrics for optimization opportunities

## Troubleshooting

### Model Returns Low Confidence

- Review training data quality
- Ensure sufficient examples for each vendor/account/cost center
- Check feature engineering in `train.py`
- Increase `n_estimators` or adjust hyperparameters

### Endpoint Timeout

- Increase instance size
- Optimize inference code
- Use batch prediction for multiple transactions

### Wrong Predictions

- Review mapping configuration
- Check if vendor names are normalized consistently
- Add more training examples for problematic categories
- Review classification memory rules in ERPNext





