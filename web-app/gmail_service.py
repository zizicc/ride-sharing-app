import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")  

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    print("Authenticating Gmail API...")  
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        print("Using existing token.json")
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("Refreshed token")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8080, access_type="offline", prompt="consent")
            print("New OAuth authentication completed")
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def send_test_email():
    print("Preparing test email...")
    service = authenticate_gmail()
    
    message = MIMEMultipart()
    message['to'] = "dwarfhamsterzhang@gmail.com"  
    message['subject'] = "Test Email from Gmail API"
    message.attach(MIMEText("This is a test email sent via Gmail API.", 'plain'))

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_message = {'raw': raw_message}

    try:
        message = service.users().messages().send(userId="me", body=send_message).execute()
        print(f"Email sent successfully! Message ID: {message['id']}")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    print("Running gmail_service.py...")
    send_test_email()



def send_email(to, subject, body):
    service = authenticate_gmail()
    
    message = MIMEMultipart()
    message['to'] = to
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    send_message = {'raw': raw_message}

    try:
        message = service.users().messages().send(userId="me", body=send_message).execute()
        print(f"Email sent to {to}, Message Id: {message['id']}")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
