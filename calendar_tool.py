import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from typing import List,Dict,Any,Optional
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE', 'credentials.json')

class CalendarEventTool:
    """
    MCP Tool to fetch today's learning events from Google Calendar
    """

    def __init__(self,calendar_id: Optional[str] = None):
        self.calendar_id = calendar_id or os.environ.get('LEARNING_CALENDAR_ID')

        if not self.calendar_id:
            logger.error("FATAL: LEARNING_CALENDAR_ID is not set.")
            raise ValueError("Calendar ID must be provided or set in env.")
        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )

            # Build the Calendar service client
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info(f"CalendarEventTool initialized for Calendar ID: {self.calendar_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar Service: {e}")
            raise

    def get_today_events(self) -> List[Dict[str,Any]]:
        """
        Retrieves all scheduled learning events for the current day.
        
        This is the primary function called by the AI Agent.
        """        

        now = datetime.datetime.now(datetime.timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

        try:
            events_result = self.service.events().list(
                calendarId = self.calendar_id,
                timeMin = start_of_day,
                timeMax = end_of_day,
                singleEvents = True,
                orderBy = 'startTime'
            ).execute()

            events = events_result.get('items',[])

            if not events:
                logger.info("No Events for Today")
            
            processed_events = []

            for event in events:
                start_time = event['start'].get('dateTime', event['start'].get('date'))

                processed_events.append(
                    {
                    'title': event['summary'],
                    'start_time_utc': start_time,
                    'link': event.get('htmlLink', 'N/A')
                    }
                )
        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}")
            # Return an empty list or raise an error for the agent to handle
            return []    

