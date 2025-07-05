import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict
import logging

from utils.appointment_utils import appointment_manager
from outbound_appointment_calls import AppointmentOutboundCaller

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppointmentSchedulerService:
    """
    Main service that coordinates appointment management and outbound calls
    """
    
    def __init__(self):
        self.appointment_manager = appointment_manager
        self.outbound_caller = AppointmentOutboundCaller()
        self.is_running = False
    
    async def send_daily_reminders(self):
        """Send reminders for appointments in the next 24 hours"""
        logger.info("Starting daily reminder process...")
        
        try:
            appointments = self.appointment_manager.get_appointments_needing_reminders(24)
            logger.info(f"Found {len(appointments)} appointments needing reminders")
            
            successful_calls = []
            failed_calls = []
            
            for appointment in appointments:
                try:
                    success = await self.outbound_caller.make_reminder_call(appointment['id'])
                    if success:
                        successful_calls.append(appointment['id'])
                        logger.info(f"Successfully sent reminder for appointment {appointment['id']}")
                    else:
                        failed_calls.append(appointment['id'])
                        logger.warning(f"Failed to send reminder for appointment {appointment['id']}")
                    
                    # Add delay between calls
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error sending reminder for appointment {appointment['id']}: {e}")
                    failed_calls.append(appointment['id'])
            
            logger.info(f"Daily reminders completed: {len(successful_calls)} successful, {len(failed_calls)} failed")
            return successful_calls, failed_calls
            
        except Exception as e:
            logger.error(f"Error in daily reminder process: {e}")
            return [], []
    
    async def send_weekly_followups(self):
        """Send follow-up calls to clients who had appointments last week"""
        logger.info("Starting weekly follow-up process...")
        
        try:
            # Get appointments from last week
            end_date = datetime.now() - timedelta(days=7)
            start_date = end_date - timedelta(days=7)
            
            # This would need to be implemented in appointment_manager
            # past_appointments = self.appointment_manager.get_appointments_in_range(start_date, end_date)
            
            # For now, we'll skip this and just log
            logger.info("Weekly follow-up process would run here")
            
        except Exception as e:
            logger.error(f"Error in weekly follow-up process: {e}")
    
    async def process_scheduling_queue(self, phone_numbers: List[str]):
        """Process a queue of phone numbers for scheduling calls"""
        logger.info(f"Processing scheduling queue with {len(phone_numbers)} numbers")
        
        results = await self.outbound_caller.bulk_scheduling_calls(phone_numbers, delay_seconds=60)
        
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        logger.info(f"Scheduling calls completed: {successful} successful, {failed} failed")
        return results
    
    def schedule_daily_tasks(self):
        """Schedule daily automated tasks"""
        # Schedule daily reminders at 9 AM
        schedule.every().day.at("09:00").do(self._run_async_task, self.send_daily_reminders)
        
        # Schedule weekly follow-ups on Mondays at 10 AM
        schedule.every().monday.at("10:00").do(self._run_async_task, self.send_weekly_followups)
        
        logger.info("Daily tasks scheduled")
    
    def _run_async_task(self, coro):
        """Helper to run async tasks in the scheduler"""
        asyncio.run(coro())
    
    async def start_service(self):
        """Start the appointment scheduler service"""
        logger.info("Starting Appointment Scheduler Service")
        
        self.schedule_daily_tasks()
        self.is_running = True
        
        # Run the scheduler
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    def stop_service(self):
        """Stop the appointment scheduler service"""
        logger.info("Stopping Appointment Scheduler Service")
        self.is_running = False
    
    # Manual trigger methods for testing/admin use
    async def trigger_reminder_call(self, appointment_id: str):
        """Manually trigger a reminder call for a specific appointment"""
        logger.info(f"Manually triggering reminder call for appointment {appointment_id}")
        return await self.outbound_caller.make_reminder_call(appointment_id)
    
    async def trigger_followup_call(self, client_id: str):
        """Manually trigger a follow-up call for a specific client"""
        logger.info(f"Manually triggering follow-up call for client {client_id}")
        return await self.outbound_caller.make_followup_call(client_id)
    
    async def trigger_scheduling_call(self, phone_number: str):
        """Manually trigger a scheduling call to a phone number"""
        logger.info(f"Manually triggering scheduling call to {phone_number}")
        return await self.outbound_caller.make_scheduling_call(phone_number)
    
    def get_appointment_stats(self) -> Dict:
        """Get statistics about appointments"""
        try:
            upcoming_appointments = self.appointment_manager.get_upcoming_appointments(days_ahead=7)
            reminders_needed = self.appointment_manager.get_appointments_needing_reminders(24)
            
            return {
                'upcoming_appointments_7_days': len(upcoming_appointments),
                'reminders_needed_24_hours': len(reminders_needed),
                'total_appointments_today': len([apt for apt in upcoming_appointments if apt['appointment_time'].date() == datetime.now().date()]),
                'service_status': 'running' if self.is_running else 'stopped'
            }
        except Exception as e:
            logger.error(f"Error getting appointment stats: {e}")
            return {'error': str(e)}

# Global service instance
scheduler_service = AppointmentSchedulerService()

# CLI interface for manual operations
async def main():
    """Main CLI interface for the appointment scheduler"""
    print("Personal Trainer Appointment Scheduler")
    print("=====================================")
    
    while True:
        print("\nOptions:")
        print("1. Send daily reminders now")
        print("2. Make single reminder call")
        print("3. Make single follow-up call")
        print("4. Make single scheduling call")
        print("5. Show appointment statistics")
        print("6. Start automated service")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            print("Sending daily reminders...")
            successful, failed = await scheduler_service.send_daily_reminders()
            print(f"Completed: {len(successful)} successful, {len(failed)} failed")
        
        elif choice == '2':
            appointment_id = input("Enter appointment ID: ").strip()
            if appointment_id:
                success = await scheduler_service.trigger_reminder_call(appointment_id)
                print(f"Reminder call {'successful' if success else 'failed'}")
        
        elif choice == '3':
            client_id = input("Enter client ID: ").strip()
            if client_id:
                success = await scheduler_service.trigger_followup_call(client_id)
                print(f"Follow-up call {'successful' if success else 'failed'}")
        
        elif choice == '4':
            phone_number = input("Enter phone number (e.g., +1234567890): ").strip()
            if phone_number:
                success = await scheduler_service.trigger_scheduling_call(phone_number)
                print(f"Scheduling call {'successful' if success else 'failed'}")
        
        elif choice == '5':
            stats = scheduler_service.get_appointment_stats()
            print("\nAppointment Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        elif choice == '6':
            print("Starting automated service... (Press Ctrl+C to stop)")
            try:
                await scheduler_service.start_service()
            except KeyboardInterrupt:
                scheduler_service.stop_service()
                print("\nService stopped.")
        
        elif choice == '7':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main()) 