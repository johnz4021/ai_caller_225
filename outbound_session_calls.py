import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.telephony.client.twilio_client import TwilioClient
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig
from vocode.streaming.models.transcriber import DeepgramTranscriberConfig

from utils.session_utils import session_manager
from session_agent import SessionAgentFactory

class SessionOutboundCaller:
    """
    Handles outbound calls for training session management
    """
    
    def __init__(self):
        self.session_manager = session_manager
        self.twilio_client = TwilioClient(
            TwilioConfig(
                account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
                auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            )
        )
        self.from_phone = os.getenv("TWILIO_PHONE_NUMBER")
        
        # Default trainer ID from your Firebase data
        self.default_trainer_id = "8QYQXt91Kzf4j4w0i2kogb4zEyN2"
        
    def create_session_agent_config(self, call_type: str, session_data: Dict = None) -> ChatGPTAgentConfig:
        """Create agent configuration for different call types"""
        
        base_instructions = """
You are a professional training session assistant calling on behalf of a personal training business. 
Be polite, professional, and concise. Keep calls brief and focused on the specific purpose.
"""
        
        if call_type == "reminder":
            if session_data:
                session_time = session_data.get('dateTime')
                if hasattr(session_time, 'strftime'):
                    formatted_time = session_time.strftime('%A, %B %d at %I:%M %p')
                else:
                    formatted_time = str(session_time)
                
                initial_message = f"Hi {session_data.get('clientName', 'there')}! This is a friendly reminder about your training session scheduled for {formatted_time} at {session_data.get('location', 'the gym')}. Please confirm if you'll be able to make it."
                
                prompt = base_instructions + f"""
This is a session reminder call. Key details:
- Client: {session_data.get('clientName', 'N/A')}
- Session Time: {formatted_time}
- Location: {session_data.get('location', 'Gym')}
- Duration: {session_data.get('duration', 60)} minutes

Your goals:
1. Confirm the client can attend the session
2. If they can't attend, offer to reschedule
3. Answer any questions about the session
4. Keep the call brief and professional

If they want to reschedule, collect their preferred new date and time.
"""
            else:
                initial_message = "Hi! This is a reminder about your upcoming training session."
                prompt = base_instructions + "This is a session reminder call. Confirm attendance and offer to reschedule if needed."
        
        elif call_type == "follow_up":
            initial_message = "Hi! I'm calling to follow up on your training progress and see if you'd like to schedule your next session."
            prompt = base_instructions + """
This is a follow-up call to:
1. Check on the client's progress
2. Encourage them to schedule their next session
3. Answer any questions about their training
4. Maintain a positive relationship

Be encouraging and supportive. Focus on their goals and progress.
"""
        
        elif call_type == "scheduling":
            initial_message = "Hi! I'm calling to help you schedule your training session. When would work best for you?"
            prompt = base_instructions + """
This is a scheduling call to:
1. Help the client book a training session
2. Find a time that works for both the client and trainer
3. Confirm session details (date, time, location)
4. Provide any necessary information about the session

Be flexible and offer multiple time options if possible.
"""
        
        else:
            initial_message = "Hi! I'm calling from your personal training service."
            prompt = base_instructions + "This is a general training-related call. Be helpful and professional."
        
        return ChatGPTAgentConfig(
            initial_message=BaseMessage(text=initial_message),
            prompt_preamble=prompt,
            generate_responses=True,
        )
    
    async def make_reminder_call(self, session_id: str) -> bool:
        """Make a reminder call for a specific session"""
        try:
            # Get session details
            session = self.session_manager.get_session_by_id(session_id)
            if not session:
                print(f"Session {session_id} not found")
                return False
            
            # Get client details
            client = self.session_manager.get_client_by_id(session['clientId'])
            if not client:
                print(f"Client {session['clientId']} not found")
                return False
            
            # Create agent config for reminder call
            agent_config = self.create_session_agent_config("reminder", session)
            
            # Make the call
            success = await self._make_call(
                to_phone=client['phone'],
                agent_config=agent_config,
                call_purpose=f"Session reminder for {session['clientName']}"
            )
            
            if success:
                # Mark reminder as sent
                self.session_manager.mark_reminder_sent(session_id, "phone")
                print(f"Reminder call completed for session {session_id}")
            
            return success
            
        except Exception as e:
            print(f"Error making reminder call for session {session_id}: {e}")
            return False
    
    async def make_follow_up_call(self, client_id: str) -> bool:
        """Make a follow-up call to a client"""
        try:
            # Get client details
            client = self.session_manager.get_client_by_id(client_id)
            if not client:
                print(f"Client {client_id} not found")
                return False
            
            # Create agent config for follow-up call
            agent_config = self.create_session_agent_config("follow_up")
            
            # Make the call
            success = await self._make_call(
                to_phone=client['phone'],
                agent_config=agent_config,
                call_purpose=f"Follow-up call for {client['name']}"
            )
            
            if success:
                print(f"Follow-up call completed for client {client_id}")
            
            return success
            
        except Exception as e:
            print(f"Error making follow-up call for client {client_id}: {e}")
            return False
    
    async def make_scheduling_call(self, phone_number: str, client_name: str = None) -> bool:
        """Make a scheduling call to a phone number"""
        try:
            # Create agent config for scheduling call
            agent_config = self.create_session_agent_config("scheduling")
            
            # Make the call
            success = await self._make_call(
                to_phone=phone_number,
                agent_config=agent_config,
                call_purpose=f"Scheduling call for {client_name or phone_number}"
            )
            
            if success:
                print(f"Scheduling call completed for {phone_number}")
            
            return success
            
        except Exception as e:
            print(f"Error making scheduling call to {phone_number}: {e}")
            return False
    
    async def _make_call(self, to_phone: str, agent_config: ChatGPTAgentConfig, call_purpose: str) -> bool:
        """Internal method to make a call"""
        try:
            print(f"Making call: {call_purpose} to {to_phone}")
            
            # Create session agent
            agent_factory = SessionAgentFactory()
            agent = agent_factory.create_agent(agent_config)
            
            # Configure transcriber and synthesizer
            transcriber_config = DeepgramTranscriberConfig(
                model="nova-2",
                language="en-US",
            )
            
            synthesizer_config = ElevenLabsSynthesizerConfig(
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Default voice
                stability=0.1,
                similarity_boost=0.75,
            )
            
            # Make the call using Twilio
            call = await self.twilio_client.create_call(
                to=to_phone,
                from_=self.from_phone,
                agent=agent,
                transcriber_config=transcriber_config,
                synthesizer_config=synthesizer_config,
            )
            
            print(f"Call initiated: {call.sid}")
            return True
            
        except Exception as e:
            print(f"Error making call to {to_phone}: {e}")
            return False
    
    async def process_reminder_queue(self, hours_ahead: int = 24) -> Dict[str, int]:
        """Process all sessions needing reminders"""
        try:
            sessions_needing_reminders = self.session_manager.get_sessions_needing_reminders(hours_ahead)
            
            stats = {
                'total_sessions': len(sessions_needing_reminders),
                'successful_calls': 0,
                'failed_calls': 0
            }
            
            print(f"Found {stats['total_sessions']} sessions needing reminders")
            
            for session in sessions_needing_reminders:
                try:
                    success = await self.make_reminder_call(session['id'])
                    if success:
                        stats['successful_calls'] += 1
                    else:
                        stats['failed_calls'] += 1
                    
                    # Add delay between calls to avoid overwhelming the system
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    print(f"Error processing reminder for session {session['id']}: {e}")
                    stats['failed_calls'] += 1
            
            print(f"Reminder processing complete: {stats['successful_calls']} successful, {stats['failed_calls']} failed")
            return stats
            
        except Exception as e:
            print(f"Error processing reminder queue: {e}")
            return {'total_sessions': 0, 'successful_calls': 0, 'failed_calls': 0}
    
    async def bulk_follow_up_calls(self, client_ids: List[str], delay_seconds: int = 10) -> Dict[str, int]:
        """Make follow-up calls to multiple clients"""
        try:
            stats = {
                'total_clients': len(client_ids),
                'successful_calls': 0,
                'failed_calls': 0
            }
            
            print(f"Making follow-up calls to {stats['total_clients']} clients")
            
            for client_id in client_ids:
                try:
                    success = await self.make_follow_up_call(client_id)
                    if success:
                        stats['successful_calls'] += 1
                    else:
                        stats['failed_calls'] += 1
                    
                    # Add delay between calls
                    await asyncio.sleep(delay_seconds)
                    
                except Exception as e:
                    print(f"Error making follow-up call to client {client_id}: {e}")
                    stats['failed_calls'] += 1
            
            print(f"Follow-up calls complete: {stats['successful_calls']} successful, {stats['failed_calls']} failed")
            return stats
            
        except Exception as e:
            print(f"Error making bulk follow-up calls: {e}")
            return {'total_clients': 0, 'successful_calls': 0, 'failed_calls': 0}

# Global instance
session_outbound_caller = SessionOutboundCaller() 