# Firebase Setup Guide - JSON Environment Variable Only

This guide explains how to set up Firebase authentication using only the `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable.

## 🔧 Setup Process

### Step 1: Convert Your Service Account Key

If you have a `serviceAccountKey.json` file, use the conversion script:

```bash
python convert_firebase_json.py
```

This will output the properly formatted environment variable.

### Step 2: Update Your .env File

Add the generated line to your `.env` file:

```env
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"pt-e45ff",...}
```

### Step 3: For Render Deployment

1. Go to your Render dashboard
2. Navigate to Environment Variables
3. Add new variable:
   - **Key**: `FIREBASE_SERVICE_ACCOUNT_JSON`
   - **Value**: (paste the entire JSON string)

## 🔍 Validation

Test your Firebase connection:

```bash
python -c "import os, json; json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '{}'))"
```

Or run the full test:

```bash
python test_session_system.py
```

## ⚠️ Important Notes

1. **No File Dependencies**: The system no longer looks for `serviceAccountKey.json`
2. **Single Line**: The JSON must be on a single line (no line breaks)
3. **Proper Escaping**: Make sure quotes and special characters are properly escaped
4. **Security**: Never commit the actual JSON to version control

## 🚨 Troubleshooting

### Invalid JSON Error
```bash
# Validate your JSON format
python -c "import os, json; print('Valid JSON' if json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '{}')) else 'Invalid JSON')"
```

### Missing Environment Variable
```bash
# Check if variable is set
python -c "import os; print('Set' if os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON') else 'Not set')"
```

### Connection Test
```bash
# Test Firebase connection
python -c "from firebase_config import firebase_config; print('Connected:', firebase_config.get_db() is not None)"
```

## 📋 Environment Variable Template

Your `.env` file should include:

```env
# Firebase Configuration (REQUIRED)
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"pt-e45ff","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}
```

Replace the `...` with your actual values from the Firebase service account key. 