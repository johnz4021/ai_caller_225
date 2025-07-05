#!/usr/bin/env python3
"""
Test script for the session management system
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Test Firebase connection
def test_firebase_connection():
    """Test Firebase connection"""
    print("🔥 Testing Firebase connection...")
    
    try:
        from firebase_config import firebase_config
        db = firebase_config.get_db()
        print("✅ Firebase connection successful")
        return True
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return False

# Test session manager
def test_session_manager():
    """Test session manager functionality"""
    print("\n📅 Testing Session Manager...")
    
    try:
        from utils.session_utils import session_manager
        
        # Test getting trainer
        trainer = session_manager.get_trainer_by_id("8QYQXt91Kzf4j4w0i2kogb4zEyN2")
        if trainer:
            print(f"✅ Trainer found: {trainer.get('name', 'Unknown')}")
        else:
            print("⚠️  Trainer not found")
        
        # Test getting client by phone
        client = session_manager.get_client_by_phone("9845282323")
        if client:
            print(f"✅ Client found: {client.get('name', 'Unknown')}")
            
            # Test getting sessions for client
            sessions = session_manager.get_sessions_for_client(client['id'], limit=3)
            print(f"✅ Found {len(sessions)} sessions for client")
            
            # Test remaining sessions
            remaining = session_manager.get_client_sessions_remaining(client['id'])
            print(f"✅ Client has {remaining} sessions remaining")
            
        else:
            print("⚠️  Test client not found")
        
        # Test upcoming sessions
        upcoming = session_manager.get_upcoming_sessions(
            trainer_id="8QYQXt91Kzf4j4w0i2kogb4zEyN2",
            days_ahead=7
        )
        print(f"✅ Found {len(upcoming)} upcoming sessions")
        
        # Test sessions needing reminders
        reminders = session_manager.get_sessions_needing_reminders(hours_ahead=24)
        print(f"✅ Found {len(reminders)} sessions needing reminders")
        
        return True
        
    except Exception as e:
        print(f"❌ Session manager test failed: {e}")
        return False

# Test session agent
def test_session_agent():
    """Test session agent functionality"""
    print("\n🤖 Testing Session Agent...")
    
    try:
        from session_agent import SessionSchedulingAgent, SessionAgentFactory
        from vocode.streaming.models.agent import ChatGPTAgentConfig
        from vocode.streaming.models.message import BaseMessage
        
        # Create agent config
        config = ChatGPTAgentConfig(
            initial_message=BaseMessage(text="Hello! I'm here to help you schedule your training session."),
            prompt_preamble="You are a training session assistant.",
            generate_responses=True,
        )
        
        # Create agent
        agent = SessionSchedulingAgent(config)
        
        # Test intent extraction
        test_messages = [
            "I want to schedule a training session",
            "Can I reschedule my appointment?",
            "What times are available tomorrow?",
            "How many sessions do I have left?"
        ]
        
        for message in test_messages:
            intent = agent.extract_session_intent(message)
            print(f"✅ Message: '{message}' -> Intent: {intent['intent']}")
        
        print("✅ Session agent tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Session agent test failed: {e}")
        return False

# Test environment variables
def test_environment():
    """Test required environment variables"""
    print("\n🔧 Testing Environment Variables...")
    
    required_vars = [
        "OPENAI_API_KEY",
        "TWILIO_ACCOUNT_SID", 
        "TWILIO_AUTH_TOKEN",
        "DEEPGRAM_API_KEY",
        "BASE_URL",
        "TWILIO_PHONE_NUMBER",
        "FIREBASE_SERVICE_ACCOUNT_JSON"
    ]
    
    missing_vars = []
    placeholder_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif value.startswith("your_") or value.endswith("_here"):
            placeholder_vars.append(var)
        else:
            print(f"✅ {var}: Set")
    
    if missing_vars:
        print(f"❌ Missing variables: {', '.join(missing_vars)}")
    
    if placeholder_vars:
        print(f"⚠️  Placeholder values (need to be updated): {', '.join(placeholder_vars)}")
    
    # Check Firebase JSON format
    firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if firebase_json:
        try:
            json.loads(firebase_json)
            print("✅ Firebase service account JSON is valid")
        except json.JSONDecodeError:
            print("❌ Firebase service account JSON is invalid")
            return False
    else:
        print("❌ Firebase service account JSON not found")
    
    return len(missing_vars) == 0

def main():
    """Run all tests"""
    print("🧪 Testing Personal Training Session System")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment),
        ("Firebase Connection", test_firebase_connection),
        ("Session Manager", test_session_manager),
        ("Session Agent", test_session_agent),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your session system is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 