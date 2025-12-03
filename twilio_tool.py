from twilio.rest import Client
import os
import logging

#Environment variables expected for Twilio
ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TwilioNotifierTool:
    """
    MCP Tool to send an SMS notification using Twilio.
    """



    def __init__(self):
        if not all([ACCOUNT_SID, AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            logger.error("FATAL: One or more Twilio credentials are missing.")
            raise ValueError("Twilio credentials must be set.")
            
        self.client = Client(ACCOUNT_SID, AUTH_TOKEN)
        self.from_number = TWILIO_PHONE_NUMBER
        logger.info("TwilioNotifierTool initialized.")

    def send_sms_notification(self, recipient: str, message_body: str) -> bool:
        """
        Sends the synthesized learning plan as an SMS to the recipient.
        
        This is the primary function called by the AI Agent as the final action.
        """
        try:
            # Twilio API call to send the message
            message = self.client.messages.create(
                to=recipient,
                from_=self.from_number,
                body=message_body
            )
            logger.info(f"SMS sent successfully to {recipient}. SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient}: {e}")
            return False