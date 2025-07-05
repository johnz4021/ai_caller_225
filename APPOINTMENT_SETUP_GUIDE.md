# Personal Trainer Appointment Scheduling AI Agent Setup Guide

This guide will help you set up the AI agent to handle appointment scheduling for your personal trainer platform with Firebase integration and outbound calling capabilities.

## 🎯 Overview

The enhanced system now includes:
- **Firebase Integration**: Store appointments and client data in Firestore
- **Appointment Scheduling Agent**: AI agent specialized for booking appointments
- **Outbound Calling**: Automated reminders and follow-up calls
- **Comprehensive Management**: Full CRUD operations for appointments and clients

## 📋 Prerequisites

1. **Existing Setup**: You should have the base AI calling system working
2. **Firebase Project**: A Firebase project with Firestore enabled
3. **Twilio Account**: For outbound calling (same as your existing setup)
4. **Python Environment**: Python 3.9+ with the required dependencies

## 🔧 Setup Instructions

### Step 1: Install Additional Dependencies

Update your `pyproject.toml` (already done) and install the new dependencies:

```bash
poetry install
# or if using pip:
pip install firebase-admin google-cloud-firestore python-dateutil pytz schedule
```

### Step 2: Firebase Configuration

#### Option A: Using Service Account Key File
1. Go to your Firebase Console
2. Navigate to Project Settings > Service Accounts
3. Generate a new private key
4. Download the JSON file and save it as `serviceAccountKey.json` in your project root
5. Set the environment variable:
   ```bash
   export FIREBASE_SERVICE_ACCOUNT_PATH=serviceAccountKey.json
   ```

#### Option B: Using Environment Variable (Recommended for Production)
1. Copy the contents of your service account JSON file
2. Set it as an environment variable:
   ```bash
   export FIREBASE_SERVICE_ACCOUNT_JSON='{"type": "service_account", "project_id": "your-project-id", ...}'
   ```

### Step 3: Environment Variables

Add these environment variables to your `.env` file:

```env
# Existing variables (keep these)
OPENAI_API_KEY=your_openai_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
DEEPGRAM_API_KEY=your_deepgram_api_key
BASE_URL=your_base_url

# New variables for appointment scheduling
USE_APPOINTMENT_AGENT=true
TWILIO_PHONE_NUMBER=+1234567890  # Your Twilio phone number
FIREBASE_SERVICE_ACCOUNT_JSON=your_firebase_service_account_json
# OR
FIREBASE_SERVICE_ACCOUNT_PATH=serviceAccountKey.json
```

### Step 4: Firebase Firestore Setup

Your Firestore database will automatically create these collections:
- `clients`: Client information (name, phone, email, notes)
- `appointments`: Appointment details (client_id, trainer_id, time, status)
- `trainers`: Trainer information (optional, for multi-trainer setups)

No manual setup required - the collections will be created automatically.

### Step 5: Test the Setup

1. **Test Firebase Connection**:
   ```bash
   python -c "from firebase_config import firebase_config; print('Firebase connected successfully')"
   ```

2. **Test Appointment Creation**:
   ```bash
   python -c "
   from utils.appointment_utils import appointment_manager
   from datetime import datetime, timedelta
   
   # Create a test client
   client_id = appointment_manager.create_client('Test Client', '+1234567890', 'test@example.com')
   print(f'Created client: {client_id}')
   
   # Create a test appointment
   appointment_time = datetime.now() + timedelta(days=1)
   appointment_id = appointment_manager.create_appointment(client_id, 'default_trainer', appointment_time)
   print(f'Created appointment: {appointment_id}')
   "
   ```

3. **Test Inbound Calls**:
   - Call your Twilio number
   - The AI should now respond as an appointment scheduling assistant

## 🚀 Usage

### Inbound Calls (Appointment Scheduling)

When someone calls your number, the AI will:
1. Greet them professionally
2. Ask what they need (schedule, reschedule, cancel)
3. Collect necessary information (name, phone, preferred time)
4. Book the appointment in Firebase
5. Provide confirmation

### Outbound Calls (Reminders & Follow-ups)

#### Manual Outbound Calls
```bash
# Run the appointment scheduler CLI
python appointment_scheduler.py
```

#### Automated Reminders
```bash
# Send reminders for appointments in next 24 hours
python -c "
import asyncio
from outbound_appointment_calls import send_appointment_reminders
asyncio.run(send_appointment_reminders(24))
"
```

#### Single Reminder Call
```bash
python -c "
import asyncio
from outbound_appointment_calls import make_single_reminder_call
asyncio.run(make_single_reminder_call('appointment_id_here'))
"
```

#### Scheduling Call to New Leads
```bash
python -c "
import asyncio
from outbound_appointment_calls import make_single_scheduling_call
asyncio.run(make_single_scheduling_call('+1234567890'))
"
```

### Automated Service
```bash
# Start the automated scheduler service
python appointment_scheduler.py
# Choose option 6 to start automated service
```

## 📊 Firebase Data Structure

### Clients Collection
```json
{
  "id": "auto-generated-id",
  "name": "John Doe",
  "phone": "+1234567890",
  "email": "john@example.com",
  "notes": "Beginner level, focus on weight loss",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### Appointments Collection
```json
{
  "id": "auto-generated-id",
  "client_id": "client-id-reference",
  "trainer_id": "trainer-id-reference",
  "appointment_time": "2024-01-20T14:00:00Z",
  "duration_minutes": 60,
  "service_type": "Personal Training",
  "status": "scheduled",
  "notes": "Focus on upper body",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "reminder_sent": false,
  "confirmation_received": false
}
```

## 🔄 Integration with Your Existing App

### API Integration
You can integrate with your existing personal trainer app by:

1. **Reading from Firebase**: Your app can read appointment data directly from Firestore
2. **Webhook Integration**: Set up webhooks to sync data between systems
3. **REST API**: Create API endpoints to manage appointments programmatically

### Example Integration Code
```python
from utils.appointment_utils import appointment_manager

# Get all appointments for a client
appointments = appointment_manager.get_appointments_for_client('client_id')

# Get upcoming appointments
upcoming = appointment_manager.get_upcoming_appointments('trainer_id', days_ahead=7)

# Check availability
from datetime import datetime
available_slots = appointment_manager.get_available_slots('trainer_id', datetime.now())
```

## 🎛️ Configuration Options

### Agent Behavior
- Modify `appointment_agent.py` to customize conversation flow
- Update prompts for different business types
- Add custom validation rules

### Calling Schedule
- Modify `appointment_scheduler.py` to change reminder timing
- Adjust call frequency and retry logic
- Customize business hours

### Firebase Rules
Set up Firestore security rules:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /clients/{clientId} {
      allow read, write: if request.auth != null;
    }
    match /appointments/{appointmentId} {
      allow read, write: if request.auth != null;
    }
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **Firebase Connection Error**:
   - Check your service account JSON is valid
   - Verify Firebase project ID is correct
   - Ensure Firestore is enabled in Firebase Console

2. **Outbound Calls Not Working**:
   - Verify `TWILIO_PHONE_NUMBER` is set correctly
   - Check Twilio account is not in trial mode
   - Ensure sufficient Twilio credits

3. **Agent Not Responding Correctly**:
   - Check `USE_APPOINTMENT_AGENT=true` in environment
   - Verify OpenAI API key is valid
   - Review agent instructions in `appointment_agent.py`

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Scaling Considerations

### Production Deployment
1. **Use Redis**: Switch to Redis for call state management
2. **Load Balancing**: Deploy multiple instances behind a load balancer
3. **Monitoring**: Set up logging and monitoring for call success rates
4. **Backup**: Implement Firebase backup strategies

### Performance Optimization
1. **Connection Pooling**: Use connection pooling for Firebase
2. **Caching**: Cache frequently accessed data
3. **Rate Limiting**: Implement rate limiting for outbound calls

## 🔒 Security Best Practices

1. **Environment Variables**: Never commit sensitive data to version control
2. **Firebase Rules**: Implement proper Firestore security rules
3. **API Keys**: Rotate API keys regularly
4. **Logging**: Avoid logging sensitive information

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the Firebase Console for error logs
3. Check Twilio logs for call issues
4. Verify all environment variables are set correctly

## 🎉 Next Steps

Once set up, you can:
1. Customize the AI agent's personality and responses
2. Add more sophisticated scheduling logic
3. Integrate with your existing business systems
4. Set up automated marketing campaigns
5. Add analytics and reporting features

Your AI appointment scheduling system is now ready to handle both inbound and outbound calls for your personal training business! 