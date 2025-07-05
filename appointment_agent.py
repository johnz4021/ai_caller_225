from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re
from dateutil import parser
import pytz

from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.agent.base_agent import BaseAgent
from vocode.streaming.agent.factory import AgentFactory

from utils.appointment_utils import appointment_manager

class AppointmentSchedulingAgent(BaseAgent):
    """
    Custom agent for handling appointment scheduling conversations
    """
    
    def __init__(self, agent_config: ChatGPTAgentConfig):
        super().__init__(agent_config)
        self.appointment_manager = appointment_manager
        self.conversation_context = {}
        
    def get_appointment_instructions(self) -> str:
        """Get specialized instructions for appointment scheduling"""
        return """
You are a professional appointment scheduling assistant for a personal training business. Your primary role is to help clients schedule, reschedule, or cancel their personal training sessions.

CAPABILITIES:
- Schedule new appointments
- Check appointment availability
- Reschedule existing appointments
- Cancel appointments
- Provide appointment confirmations
- Send appointment reminders

CONVERSATION GUIDELINES:
1. Be professional, friendly, and efficient
2. Always confirm appointment details before booking
3. Ask for essential information: name, phone number, preferred date/time
4. Offer alternative times if requested slot is unavailable
5. Confirm all changes and provide appointment details
6. Keep responses concise and action-oriented

REQUIRED INFORMATION FOR BOOKING:
- Client name
- Phone number
- Preferred date and time
- Type of training session (if applicable)

AVAILABLE ACTIONS:
- "SCHEDULE_APPOINTMENT" - Create new appointment
- "RESCHEDULE_APPOINTMENT" - Change existing appointment
- "CANCEL_APPOINTMENT" - Cancel appointment
- "CHECK_AVAILABILITY" - Check available time slots
- "CONFIRM_APPOINTMENT" - Confirm appointment details

Always end conversations with a clear summary of what was accomplished.
"""
    
    def extract_appointment_intent(self, message: str) -> Dict:
        """Extract appointment-related intent from user message"""
        message_lower = message.lower()
        
        # Intent detection
        if any(word in message_lower for word in ['schedule', 'book', 'appointment', 'session']):
            intent = 'schedule'
        elif any(word in message_lower for word in ['reschedule', 'change', 'move']):
            intent = 'reschedule'
        elif any(word in message_lower for word in ['cancel', 'remove']):
            intent = 'cancel'
        elif any(word in message_lower for word in ['available', 'availability', 'free']):
            intent = 'check_availability'
        else:
            intent = 'general'
        
        # Extract potential dates and times
        date_patterns = [
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(today|tomorrow|next week)\b'
        ]
        
        time_patterns = [
            r'\b(\d{1,2}:\d{2}\s*(?:am|pm))\b',
            r'\b(\d{1,2}\s*(?:am|pm))\b',
            r'\b(morning|afternoon|evening)\b'
        ]
        
        extracted_dates = []
        extracted_times = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, message_lower)
            extracted_dates.extend(matches)
        
        for pattern in time_patterns:
            matches = re.findall(pattern, message_lower)
            extracted_times.extend(matches)
        
        # Extract phone number
        phone_pattern = r'\b(\d{3}[-.]?\d{3}[-.]?\d{4})\b'
        phone_matches = re.findall(phone_pattern, message)
        
        # Extract name (simple heuristic)
        name_patterns = [
            r'my name is ([a-zA-Z\s]+)',
            r'i\'m ([a-zA-Z\s]+)',
            r'this is ([a-zA-Z\s]+)'
        ]
        
        extracted_names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, message_lower)
            extracted_names.extend(matches)
        
        return {
            'intent': intent,
            'dates': extracted_dates,
            'times': extracted_times,
            'phone': phone_matches[0] if phone_matches else None,
            'name': extracted_names[0].strip() if extracted_names else None
        }
    
    def format_available_slots(self, slots: List[datetime]) -> str:
        """Format available time slots for display"""
        if not slots:
            return "No available slots found for the requested date."
        
        formatted_slots = []
        for slot in slots[:5]:  # Show first 5 slots
            formatted_time = slot.strftime("%I:%M %p")
            formatted_slots.append(formatted_time)
        
        return f"Available times: {', '.join(formatted_slots)}"
    
    def process_scheduling_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Process appointment scheduling request"""
        intent = extracted_info['intent']
        
        if intent == 'schedule':
            return self.handle_schedule_request(extracted_info, conversation_id)
        elif intent == 'reschedule':
            return self.handle_reschedule_request(extracted_info, conversation_id)
        elif intent == 'cancel':
            return self.handle_cancel_request(extracted_info, conversation_id)
        elif intent == 'check_availability':
            return self.handle_availability_request(extracted_info, conversation_id)
        else:
            return "I can help you schedule, reschedule, or cancel appointments. What would you like to do?"
    
    def handle_schedule_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Handle appointment scheduling request"""
        # Store context for multi-turn conversation
        if conversation_id not in self.conversation_context:
            self.conversation_context[conversation_id] = {}
        
        context = self.conversation_context[conversation_id]
        
        # Update context with extracted information
        if extracted_info['name']:
            context['name'] = extracted_info['name']
        if extracted_info['phone']:
            context['phone'] = extracted_info['phone']
        if extracted_info['dates']:
            context['date'] = extracted_info['dates'][0]
        if extracted_info['times']:
            context['time'] = extracted_info['times'][0]
        
        # Check if we have all required information
        required_fields = ['name', 'phone', 'date', 'time']
        missing_fields = [field for field in required_fields if field not in context]
        
        if missing_fields:
            if 'name' in missing_fields:
                return "I'd be happy to schedule an appointment for you. Could you please tell me your name?"
            elif 'phone' in missing_fields:
                return "Great! Could you please provide your phone number for the appointment?"
            elif 'date' in missing_fields:
                return "What date would you prefer for your appointment?"
            elif 'time' in missing_fields:
                return "What time would work best for you?"
        
        # All information collected, attempt to schedule
        try:
            # Parse date and time
            date_str = context['date']
            time_str = context['time']
            
            # Simple date parsing (you may want to enhance this)
            if date_str.lower() == 'today':
                appointment_date = datetime.now().date()
            elif date_str.lower() == 'tomorrow':
                appointment_date = (datetime.now() + timedelta(days=1)).date()
            else:
                # Try to parse the date
                appointment_date = parser.parse(date_str).date()
            
            # Parse time
            appointment_time = parser.parse(time_str).time()
            
            # Combine date and time
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            
            # Check if client exists
            client = self.appointment_manager.get_client_by_phone(context['phone'])
            if not client:
                # Create new client
                client_id = self.appointment_manager.create_client(
                    name=context['name'],
                    phone=context['phone']
                )
            else:
                client_id = client['id']
            
            # Create appointment (using default trainer ID for now)
            appointment_id = self.appointment_manager.create_appointment(
                client_id=client_id,
                trainer_id="default_trainer",  # You can make this configurable
                appointment_time=appointment_datetime
            )
            
            # Clear context
            self.conversation_context[conversation_id] = {}
            
            return f"Perfect! I've scheduled your appointment for {appointment_datetime.strftime('%A, %B %d at %I:%M %p')}. Your appointment ID is {appointment_id}. You'll receive a confirmation shortly."
            
        except Exception as e:
            return f"I'm sorry, there was an issue scheduling your appointment. Could you please provide the date and time in a different format? For example: 'Monday at 2 PM' or '12/15/2023 at 3:30 PM'"
    
    def handle_reschedule_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Handle appointment rescheduling request"""
        return "I can help you reschedule your appointment. Could you please provide your phone number and the new date and time you'd prefer?"
    
    def handle_cancel_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Handle appointment cancellation request"""
        return "I can help you cancel your appointment. Could you please provide your phone number or appointment ID?"
    
    def handle_availability_request(self, extracted_info: Dict, conversation_id: str) -> str:
        """Handle availability check request"""
        if extracted_info['dates']:
            try:
                date_str = extracted_info['dates'][0]
                if date_str.lower() == 'today':
                    check_date = datetime.now()
                elif date_str.lower() == 'tomorrow':
                    check_date = datetime.now() + timedelta(days=1)
                else:
                    check_date = parser.parse(date_str)
                
                available_slots = self.appointment_manager.get_available_slots(
                    trainer_id="default_trainer",
                    date=check_date
                )
                
                return self.format_available_slots(available_slots)
            except:
                return "I'm sorry, I couldn't understand that date. Could you please specify the date you'd like to check availability for?"
        else:
            return "What date would you like to check availability for?"

class AppointmentAgentFactory(AgentFactory):
    """Factory for creating appointment scheduling agents"""
    
    def create_agent(self, agent_config: ChatGPTAgentConfig) -> BaseAgent:
        # Override the prompt for appointment scheduling
        appointment_instructions = AppointmentSchedulingAgent(agent_config).get_appointment_instructions()
        
        # Create a new config with appointment-specific instructions
        appointment_config = ChatGPTAgentConfig(
            initial_message=BaseMessage(text="Hello! I'm here to help you schedule your personal training appointment. How can I assist you today?"),
            prompt_preamble=appointment_instructions,
            generate_responses=True,
        )
        
        return AppointmentSchedulingAgent(appointment_config) 