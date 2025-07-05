import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
from vocode.streaming.telephony.config_manager.redis_config_manager import RedisConfigManager
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage

from utils.appointment_utils import appointment_manager
from appointment_agent import AppointmentAgentFactory

load_dotenv()

class AppointmentOutboundCaller:
    def __init__(self):
        self.base_url = os.environ.get("BASE_URL")
        self.twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
        self.config_manager = RedisConfigManager()
        self.appointment_manager = appointment_manager
        
        if not self.base_url:
            raise ValueError("BASE_URL must be set in environment variables")
        if not self.twilio_phone:
            raise ValueError("TWILIO_PHONE_NUMBER must be set in environment variables")
    
    def create_reminder_agent_config(self, appointment_details: Dict) -> ChatGPTAgentConfig:
        """Create agent configuration for appointment reminders"""
        
        appointment_time = appointment_details['appointment_time']
        client_name = appointment_details.get('client_name', 'there')
        
        reminder_instructions = f"""
You are calling to remind {client_name} about their upcoming personal training appointment.

APPOINTMENT DETAILS:
- Date: {appointment_time.strftime('%A, %B %d, %Y')}
- Time: {appointment_time.strftime('%I:%M %p')}
- Service: {appointment_details.get('service_type', 'Personal Training')}
- Duration: {appointment_details.get('duration_minutes', 60)} minutes

CALL OBJECTIVES:
1. Confirm they remember the appointment
2. Ask if they need to reschedule
3. Provide any preparation instructions
4. Answer any questions they might have

CONVERSATION GUIDELINES:
- Be friendly and professional
- Keep the call brief (2-3 minutes max)
- If they want to reschedule, collect their preferred new time
- If they want to cancel, ask for the reason and offer to reschedule instead
- End with a positive confirmation

SAMPLE OPENING:
"Hi {client_name}, this is calling from [Trainer Name]'s office to remind you about your personal training session scheduled for {appointment_time.strftime('%A at %I:%M %p')}. Do you have a quick moment to confirm?"

Remember to be understanding if they need to make changes and always end on a positive note.
"""
        
        return ChatGPTAgentConfig(
            initial_message=BaseMessage(text=f"Hi {client_name}, this is calling from your personal trainer's office to remind you about your upcoming appointment. Do you have a quick moment?"),
            prompt_preamble=reminder_instructions,
            generate_responses=True,
        )
    
    def create_followup_agent_config(self, client_details: Dict) -> ChatGPTAgentConfig:
        """Create agent configuration for follow-up calls"""
        
        client_name = client_details.get('name', 'there')
        
        followup_instructions = f"""
You are calling {client_name} to follow up on their personal training experience and potentially schedule future sessions.

CALL OBJECTIVES:
1. Ask about their experience with recent training sessions
2. Check if they'd like to schedule more sessions
3. Address any concerns or questions
4. Offer package deals or ongoing training programs

CONVERSATION GUIDELINES:
- Be friendly and genuinely interested in their fitness journey
- Listen to their feedback and concerns
- Don't be pushy about sales - focus on their needs
- Offer value and solutions based on their goals
- Keep the call conversational and helpful

SAMPLE OPENING:
"Hi {client_name}, this is calling from [Trainer Name]'s office. I wanted to check in and see how your recent training sessions have been going. Do you have a few minutes to chat?"

Focus on building a relationship and understanding their fitness goals.
"""
        
        return ChatGPTAgentConfig(
            initial_message=BaseMessage(text=f"Hi {client_name}, this is calling from your personal trainer's office to check in on how your training has been going. Do you have a few minutes?"),
            prompt_preamble=followup_instructions,
            generate_responses=True,
        )
    
    def create_scheduling_agent_config(self) -> ChatGPTAgentConfig:
        """Create agent configuration for scheduling calls"""
        
        scheduling_instructions = """
You are calling to help schedule personal training appointments for potential or existing clients.

CALL OBJECTIVES:
1. Introduce yourself and the personal training services
2. Understand their fitness goals and needs
3. Explain available training options
4. Schedule an initial consultation or training session
5. Collect necessary contact information

CONVERSATION GUIDELINES:
- Be professional and enthusiastic about fitness
- Ask about their current fitness level and goals
- Explain the benefits of personal training
- Offer flexible scheduling options
- Don't pressure - focus on finding the right fit
- Collect: name, phone, email, preferred times, fitness goals

SAMPLE OPENING:
"Hi, this is calling from [Trainer Name]'s personal training service. I'm reaching out to see if you might be interested in learning about our personal training programs. Do you have a quick moment?"

Focus on understanding their needs and providing value.
"""
        
        return ChatGPTAgentConfig(
            initial_message=BaseMessage(text="Hi, this is calling from your local personal training service. I'm reaching out to see if you might be interested in our fitness programs. Do you have a quick moment?"),
            prompt_preamble=scheduling_instructions,
            generate_responses=True,
        )
    
    async def make_reminder_call(self, appointment_id: str) -> bool:
        """Make a reminder call for a specific appointment"""
        try:
            # Get appointment details
            appointment = self.appointment_manager.get_appointment_by_id(appointment_id)
            if not appointment:
                print(f"Appointment {appointment_id} not found")
                return False
            
            # Get client details
            client = self.appointment_manager.get_client_by_id(appointment['client_id'])
            if not client:
                print(f"Client {appointment['client_id']} not found")
                return False
            
            # Prepare appointment details for agent
            appointment_details = {
                **appointment,
                'client_name': client['name']
            }
            
            # Create agent config
            agent_config = self.create_reminder_agent_config(appointment_details)
            
            # Make the call
            outbound_call = OutboundCall(
                base_url=self.base_url,
                to_phone=client['phone'],
                from_phone=self.twilio_phone,
                config_manager=self.config_manager,
                agent_config=agent_config,
            )
            
            print(f"Making reminder call to {client['name']} at {client['phone']}")
            await outbound_call.start()
            
            # Mark reminder as sent
            self.appointment_manager.mark_reminder_sent(appointment_id)
            
            return True
            
        except Exception as e:
            print(f"Error making reminder call: {e}")
            return False
    
    async def make_followup_call(self, client_id: str) -> bool:
        """Make a follow-up call to a client"""
        try:
            # Get client details
            client = self.appointment_manager.get_client_by_id(client_id)
            if not client:
                print(f"Client {client_id} not found")
                return False
            
            # Create agent config
            agent_config = self.create_followup_agent_config(client)
            
            # Make the call
            outbound_call = OutboundCall(
                base_url=self.base_url,
                to_phone=client['phone'],
                from_phone=self.twilio_phone,
                config_manager=self.config_manager,
                agent_config=agent_config,
            )
            
            print(f"Making follow-up call to {client['name']} at {client['phone']}")
            await outbound_call.start()
            
            return True
            
        except Exception as e:
            print(f"Error making follow-up call: {e}")
            return False
    
    async def make_scheduling_call(self, phone_number: str) -> bool:
        """Make a scheduling call to a potential client"""
        try:
            # Create agent config
            agent_config = self.create_scheduling_agent_config()
            
            # Make the call
            outbound_call = OutboundCall(
                base_url=self.base_url,
                to_phone=phone_number,
                from_phone=self.twilio_phone,
                config_manager=self.config_manager,
                agent_config=agent_config,
            )
            
            print(f"Making scheduling call to {phone_number}")
            await outbound_call.start()
            
            return True
            
        except Exception as e:
            print(f"Error making scheduling call: {e}")
            return False
    
    async def process_reminder_queue(self, hours_ahead: int = 24) -> List[str]:
        """Process all appointments that need reminders"""
        appointments_needing_reminders = self.appointment_manager.get_appointments_needing_reminders(hours_ahead)
        
        successful_calls = []
        failed_calls = []
        
        for appointment in appointments_needing_reminders:
            try:
                success = await self.make_reminder_call(appointment['id'])
                if success:
                    successful_calls.append(appointment['id'])
                else:
                    failed_calls.append(appointment['id'])
                
                # Add delay between calls to avoid overwhelming the system
                await asyncio.sleep(30)  # 30 second delay
                
            except Exception as e:
                print(f"Error processing reminder for appointment {appointment['id']}: {e}")
                failed_calls.append(appointment['id'])
        
        print(f"Reminder calls completed: {len(successful_calls)} successful, {len(failed_calls)} failed")
        return successful_calls
    
    async def bulk_scheduling_calls(self, phone_numbers: List[str], delay_seconds: int = 60) -> Dict[str, bool]:
        """Make scheduling calls to multiple phone numbers"""
        results = {}
        
        for phone_number in phone_numbers:
            try:
                success = await self.make_scheduling_call(phone_number)
                results[phone_number] = success
                
                # Add delay between calls
                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
                
            except Exception as e:
                print(f"Error calling {phone_number}: {e}")
                results[phone_number] = False
        
        return results

# Convenience functions for easy usage
async def send_appointment_reminders(hours_ahead: int = 24):
    """Send reminders for upcoming appointments"""
    caller = AppointmentOutboundCaller()
    return await caller.process_reminder_queue(hours_ahead)

async def make_single_reminder_call(appointment_id: str):
    """Make a single reminder call"""
    caller = AppointmentOutboundCaller()
    return await caller.make_reminder_call(appointment_id)

async def make_single_followup_call(client_id: str):
    """Make a single follow-up call"""
    caller = AppointmentOutboundCaller()
    return await caller.make_followup_call(client_id)

async def make_single_scheduling_call(phone_number: str):
    """Make a single scheduling call"""
    caller = AppointmentOutboundCaller()
    return await caller.make_scheduling_call(phone_number)

# Example usage
if __name__ == "__main__":
    # Example: Send reminders for appointments in the next 24 hours
    # asyncio.run(send_appointment_reminders(24))
    
    # Example: Make a single reminder call
    # asyncio.run(make_single_reminder_call("appointment_id_here"))
    
    # Example: Make a scheduling call
    # asyncio.run(make_single_scheduling_call("+1234567890"))
    
    print("Outbound calling system ready. Use the functions above to make calls.") 