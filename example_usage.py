#!/usr/bin/env python3
"""
Example usage of the Personal Trainer Appointment Scheduling System

This script demonstrates how to use the various components of the system.
Run this after setting up Firebase and environment variables.
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def example_firebase_operations():
    """Example of basic Firebase operations"""
    print("=== Firebase Operations Example ===")
    
    try:
        from utils.appointment_utils import appointment_manager
        
        # Create a test client
        print("1. Creating a test client...")
        client_id = appointment_manager.create_client(
            name="John Doe",
            phone="+1234567890",
            email="john.doe@example.com",
            notes="Beginner level, interested in weight loss"
        )
        print(f"   Created client with ID: {client_id}")
        
        # Get client by phone
        print("2. Retrieving client by phone...")
        client = appointment_manager.get_client_by_phone("+1234567890")
        if client:
            print(f"   Found client: {client['name']} ({client['phone']})")
        
        # Create an appointment
        print("3. Creating an appointment...")
        appointment_time = datetime.now() + timedelta(days=1)
        appointment_id = appointment_manager.create_appointment(
            client_id=client_id,
            trainer_id="trainer_001",
            appointment_time=appointment_time,
            duration_minutes=60,
            service_type="Personal Training",
            notes="Focus on upper body strength"
        )
        print(f"   Created appointment with ID: {appointment_id}")
        
        # Get appointments for client
        print("4. Getting appointments for client...")
        appointments = appointment_manager.get_appointments_for_client(client_id)
        for apt in appointments:
            print(f"   Appointment: {apt['appointment_time']} - {apt['service_type']}")
        
        # Check available slots
        print("5. Checking available slots...")
        available_slots = appointment_manager.get_available_slots(
            trainer_id="trainer_001",
            date=datetime.now() + timedelta(days=2)
        )
        print(f"   Found {len(available_slots)} available slots")
        for slot in available_slots[:3]:  # Show first 3
            print(f"   Available: {slot.strftime('%I:%M %p')}")
        
        return client_id, appointment_id
        
    except ImportError:
        print("   Error: Firebase components not available. Please install firebase-admin.")
        return None, None
    except Exception as e:
        print(f"   Error: {e}")
        return None, None

async def example_outbound_calls(client_id, appointment_id):
    """Example of making outbound calls"""
    print("\n=== Outbound Calls Example ===")
    
    if not client_id or not appointment_id:
        print("   Skipping outbound calls - no test data available")
        return
    
    try:
        from outbound_appointment_calls import AppointmentOutboundCaller
        
        # Initialize the caller
        caller = AppointmentOutboundCaller()
        
        # Example 1: Make a reminder call (this would actually call the phone)
        print("1. Example reminder call setup...")
        print(f"   Would call client {client_id} for appointment {appointment_id}")
        print("   (Actual call commented out to avoid unwanted calls)")
        
        # Uncomment the following line to make an actual call:
        # success = await caller.make_reminder_call(appointment_id)
        # print(f"   Reminder call {'successful' if success else 'failed'}")
        
        # Example 2: Make a scheduling call to a new lead
        print("2. Example scheduling call setup...")
        print("   Would call +1234567890 for scheduling")
        print("   (Actual call commented out to avoid unwanted calls)")
        
        # Uncomment the following line to make an actual call:
        # success = await caller.make_scheduling_call("+1234567890")
        # print(f"   Scheduling call {'successful' if success else 'failed'}")
        
        # Example 3: Process reminder queue
        print("3. Example reminder queue processing...")
        reminders_needed = appointment_manager.get_appointments_needing_reminders(24)
        print(f"   Found {len(reminders_needed)} appointments needing reminders")
        
        # Uncomment the following line to actually process reminders:
        # successful_calls = await caller.process_reminder_queue(24)
        # print(f"   Processed {len(successful_calls)} reminder calls")
        
    except ImportError:
        print("   Error: Outbound calling components not available.")
    except Exception as e:
        print(f"   Error: {e}")

def example_scheduler_service():
    """Example of using the scheduler service"""
    print("\n=== Scheduler Service Example ===")
    
    try:
        from appointment_scheduler import scheduler_service
        
        # Get appointment statistics
        print("1. Getting appointment statistics...")
        stats = scheduler_service.get_appointment_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Example of manual triggers (these would make actual calls)
        print("2. Manual trigger examples...")
        print("   Manual triggers available but commented out to avoid unwanted calls")
        
        # Uncomment to make actual calls:
        # await scheduler_service.trigger_reminder_call("appointment_id")
        # await scheduler_service.trigger_followup_call("client_id")
        # await scheduler_service.trigger_scheduling_call("+1234567890")
        
    except ImportError:
        print("   Error: Scheduler service components not available.")
    except Exception as e:
        print(f"   Error: {e}")

def example_agent_configuration():
    """Example of agent configuration"""
    print("\n=== Agent Configuration Example ===")
    
    try:
        from appointment_agent import AppointmentSchedulingAgent
        from vocode.streaming.models.agent import ChatGPTAgentConfig
        
        # Create agent config
        config = ChatGPTAgentConfig(
            initial_message="Hello! I'm here to help with scheduling.",
            prompt_preamble="You are a scheduling assistant.",
            generate_responses=True
        )
        
        # Create agent
        agent = AppointmentSchedulingAgent(config)
        
        # Example of intent extraction
        test_message = "I'd like to schedule an appointment for tomorrow at 2 PM. My name is Jane Smith and my number is 555-1234."
        extracted_info = agent.extract_appointment_intent(test_message)
        
        print("1. Intent extraction example:")
        print(f"   Input: {test_message}")
        print(f"   Extracted intent: {extracted_info['intent']}")
        print(f"   Extracted name: {extracted_info['name']}")
        print(f"   Extracted phone: {extracted_info['phone']}")
        print(f"   Extracted dates: {extracted_info['dates']}")
        print(f"   Extracted times: {extracted_info['times']}")
        
    except ImportError:
        print("   Error: Agent components not available.")
    except Exception as e:
        print(f"   Error: {e}")

def check_environment():
    """Check if environment is properly configured"""
    print("=== Environment Check ===")
    
    required_vars = [
        'OPENAI_API_KEY',
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'DEEPGRAM_API_KEY',
        'BASE_URL'
    ]
    
    optional_vars = [
        'USE_APPOINTMENT_AGENT',
        'TWILIO_PHONE_NUMBER',
        'FIREBASE_SERVICE_ACCOUNT_JSON',
        'FIREBASE_SERVICE_ACCOUNT_PATH'
    ]
    
    print("Required environment variables:")
    for var in required_vars:
        value = os.environ.get(var)
        status = "✓ Set" if value else "✗ Missing"
        print(f"   {var}: {status}")
    
    print("\nOptional environment variables (for appointment scheduling):")
    for var in optional_vars:
        value = os.environ.get(var)
        status = "✓ Set" if value else "✗ Not set"
        print(f"   {var}: {status}")
    
    # Check if appointment scheduling is enabled
    use_appointment_agent = os.environ.get("USE_APPOINTMENT_AGENT", "false").lower() == "true"
    print(f"\nAppointment scheduling enabled: {use_appointment_agent}")

async def main():
    """Main example function"""
    print("Personal Trainer Appointment Scheduling System - Example Usage")
    print("=" * 70)
    
    # Check environment
    check_environment()
    
    # Example Firebase operations
    client_id, appointment_id = example_firebase_operations()
    
    # Example outbound calls
    await example_outbound_calls(client_id, appointment_id)
    
    # Example scheduler service
    example_scheduler_service()
    
    # Example agent configuration
    example_agent_configuration()
    
    print("\n" + "=" * 70)
    print("Example completed!")
    print("\nTo actually use the system:")
    print("1. Set up Firebase and environment variables")
    print("2. Run 'python main.py' to start the inbound call server")
    print("3. Run 'python appointment_scheduler.py' for outbound calls")
    print("4. Call your Twilio number to test appointment scheduling")

if __name__ == "__main__":
    asyncio.run(main()) 