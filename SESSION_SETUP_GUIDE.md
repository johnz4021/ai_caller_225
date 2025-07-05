# Personal Training Session Scheduling AI Agent Setup Guide

This guide will help you set up the AI calling system to work with your existing Firebase personal training platform.

## 🔥 Firebase Structure Overview

Your system uses the following Firebase collections:
- **clients**: Client profiles with session packages
- **sessions**: Training sessions (scheduled, completed, cancelled)
- **users**: Trainers and user accounts
- **payments**: Payment records
- **trainingPlans**: Workout plans
- **workoutLogs**: Session workout logs

## 📋 Prerequisites

1. **Firebase Project**: You already have this set up
2. **Firebase Service Account Key**: You have the JSON credentials
3. **Twilio Account**: For phone calls
4. **OpenAI API Key**: For AI responses
5. **Deepgram API Key**: For speech-to-text
6. **ElevenLabs API Key**: For text-to-speech (optional)

## 🚀 Quick Setup

### 1. Environment Variables

Update your `.env` file with your actual API keys:

```env
# Core API Keys (REQUIRED)
OPENAI_API_KEY=sk-your-actual-openai-key
TWILIO_ACCOUNT_SID=ACyour-actual-twilio-sid
TWILIO_AUTH_TOKEN=your-actual-twilio-token
DEEPGRAM_API_KEY=your-actual-deepgram-key

# Server Configuration
BASE_URL=https://your-ngrok-url.ngrok.io
TWILIO_PHONE_NUMBER=+1234567890

# Session System Configuration
USE_SESSION_AGENT=true

# Firebase Configuration (REQUIRED)
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"pt-e45ff","private_key_id":"your-private-key-id","private_key":"-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n","client_email":"your-service-account@pt-e45ff.iam.gserviceaccount.com","client_id":"your-client-id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40pt-e45ff.iam.gserviceaccount.com"}

# Optional: ElevenLabs for better voice quality
ELEVENLABS_API_KEY=your-elevenlabs-key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

**Note**: Replace the `FIREBASE_SERVICE_ACCOUNT_JSON` value with your actual Firebase service account JSON (all on one line).

### 2. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install firebase-admin google-cloud-firestore python-dateutil pytz schedule vocode fastapi uvicorn python-dotenv
```

### 3. Firebase Indexes

Create required Firebase indexes by clicking these links (generated from your test):

1. **Client Sessions Query**: [Create Index](https://console.firebase.google.com/v1/r/project/pt-e45ff/firestore/indexes?create_composite=Cklwcm9qZWN0cy9wdC1lNDVmZi9kYXRhYmFzZXMvKGRlZmF1bHQpL2NvbGxlY3Rpb25Hcm91cHMvc2Vzc2lvbnMvaW5kZXhlcy9fEAEaDAoIY2xpZW50SWQQARoMCghkYXRlVGltZRABGgwKCF9fbmFtZV9fEAI)

2. **Reminders Query**: [Create Index](https://console.firebase.google.com/v1/r/project/pt-e45ff/firestore/indexes?create_composite=Cklwcm9qZWN0cy9wdC1lNDVmZi9kYXRhYmFzZXMvKGRlZmF1bHQpL2NvbGxlY3Rpb25Hcm91cHMvc2Vzc2lvbnMvaW5kZXhlcy9fEAEaFAoQYXV0b1JlbWluZGVyU2VudBABGgoKBnN0YXR1cxABGgwKCGRhdGVUaW1lEAEaDAoIX19uYW1lX18QAQ)

### 4. Test the System

```bash
python test_session_system.py
```

## 🎯 System Capabilities

### Inbound Call Handling
- **Session Scheduling**: Clients can call to book new sessions
- **Session Rescheduling**: Change existing session times
- **Session Cancellation**: Cancel sessions with reason tracking
- **Availability Checking**: Check trainer availability
- **Remaining Sessions**: Check how many sessions left in package

### Outbound Call Features
- **Automatic Reminders**: Call clients 24 hours before sessions
- **Follow-up Calls**: Re-engage clients who haven't scheduled recently
- **Scheduling Assistance**: Call leads to help them book sessions

### Integration with Your Data
- **Client Management**: Works with your existing client records
- **Session Tracking**: Uses your session collection structure
- **Package Management**: Tracks remaining sessions in client packages
- **Trainer Integration**: Uses your trainer data (John Zhang)

## 🔧 Configuration Details

### Default Settings
- **Trainer ID**: `8QYQXt91Kzf4j4w0i2kogb4zEyN2` (John Zhang)
- **Business Hours**: 9:00 AM - 6:00 PM, 7 days a week
- **Session Duration**: 60 minutes
- **Default Location**: "Gym"
- **Reminder Window**: 24 hours before session

### Customization Options
You can modify these in the code:
- Business hours in `session_utils.py`
- Default trainer ID in various files
- Session duration defaults
- Reminder timing

## 📞 Usage Examples

### 1. Inbound Session Scheduling Call

**Client calls your Twilio number**

```
AI: "Hello! I'm your personal training assistant. I can help you schedule, 
     reschedule, or cancel your training sessions. How can I help you today?"

Client: "Hi, I'd like to schedule a training session"

AI: "I'd be happy to help you schedule a session. Could you please tell me your name?"

Client: "This is Bill Nye"

AI: "Great! What date would you prefer for your training session?"

Client: "How about tomorrow at 2 PM?"

AI: "Perfect! I've scheduled your training session for [date] at 2:00 PM at the Gym. 
     You have 7 sessions remaining in your package. You'll receive a confirmation shortly."
```

### 2. Outbound Reminder Call

**System automatically calls client**

```
AI: "Hi Bill! This is a friendly reminder about your training session scheduled 
     for tomorrow at 2:00 PM at the Gym. Please confirm if you'll be able to make it."

Client: "Yes, I'll be there"

AI: "Excellent! We'll see you tomorrow at 2:00 PM. Have a great day!"
```

### 3. API Endpoints

Once running, you can access:

- **Health Check**: `GET /health`
- **Upcoming Sessions**: `GET /sessions/upcoming`
- **Send Reminders**: `POST /sessions/send-reminders`
- **Client Sessions**: `GET /clients/{client_id}/sessions`
- **Test Outbound**: `POST /test/outbound-call`

## 🏃‍♂️ Running the System

### Development Mode
```bash
python main.py
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### With ngrok (for development)
```bash
# Terminal 1: Start the server
python main.py

# Terminal 2: Start ngrok
ngrok http 8000

# Update BASE_URL in .env with ngrok URL
```

## 🔍 Monitoring & Debugging

### Check System Status
```bash
curl http://localhost:8000/health
```

### View Upcoming Sessions
```bash
curl http://localhost:8000/sessions/upcoming
```

### Test Firebase Connection
```bash
python test_session_system.py
```

### Send Manual Reminders
```bash
curl -X POST http://localhost:8000/sessions/send-reminders
```

## 📊 Data Structure Integration

### Your Client Structure
```json
{
  "name": "Bill Nye",
  "email": "bn@gmail.com", 
  "phone": "9845282323",
  "goals": "Mobility stuff",
  "sessionsRemaining": 8,
  "packageSize": 15,
  "trainerId": "8QYQXt91Kzf4j4w0i2kogb4zEyN2"
}
```

### Your Session Structure
```json
{
  "clientId": "FF89VZ88tCa0s6Oe2V2U",
  "clientName": "Bill Nye",
  "dateTime": "2025-01-30T14:30:00Z",
  "location": "Gym",
  "status": "scheduled",
  "duration": 60,
  "autoReminderSent": false,
  "trainerId": "8QYQXt91Kzf4j4w0i2kogb4zEyN2"
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Firebase Connection Failed**
   - Check that `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable is set
   - Verify the JSON format is valid (no line breaks, proper escaping)
   - Ensure service account has proper permissions

2. **Index Errors**
   - Click the index creation links provided in error messages
   - Wait for indexes to build (can take 5-10 minutes)

3. **API Key Issues**
   - Replace placeholder values in `.env`
   - Ensure all required keys are set
   - Check API key permissions

4. **Twilio Call Issues**
   - Verify Twilio credentials
   - Check phone number format (+1234567890)
   - Ensure webhook URL is accessible

### Debug Commands
```bash
# Test Firebase connection
python -c "from firebase_config import firebase_config; print('Connected:', firebase_config.get_db() is not None)"

# Test session manager
python -c "from utils.session_utils import session_manager; print('Trainer:', session_manager.get_trainer_by_id('8QYQXt91Kzf4j4w0i2kogb4zEyN2'))"

# Check environment variables
python -c "import os; print('Keys loaded:', bool(os.getenv('OPENAI_API_KEY')))"

# Validate Firebase JSON
python -c "import os, json; json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '{}'))"
```

## 🔐 Security Notes

- Keep your `.env` file secure and never commit it to version control
- Use environment variables for all sensitive data
- Regularly rotate API keys
- Monitor usage and costs for all services
- Ensure Firebase service account JSON is properly escaped in environment variables

## 📈 Next Steps

1. **Create Firebase Indexes**: Click the links above
2. **Update API Keys**: Replace placeholder values in `.env`
3. **Set Firebase JSON**: Copy your service account JSON to `FIREBASE_SERVICE_ACCOUNT_JSON`
4. **Test the System**: Run `python test_session_system.py`
5. **Configure Twilio**: Set up webhook URL
6. **Deploy**: Use ngrok for development or proper hosting for production

## 🆘 Support

If you encounter issues:
1. Check the test script output: `python test_session_system.py`
2. Verify all environment variables are set correctly
3. Ensure Firebase indexes are created
4. Validate Firebase service account JSON format
5. Check the system logs for detailed error messages

Your session scheduling AI system is now ready to handle both inbound and outbound calls for your personal training business! 