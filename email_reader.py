import imaplib
import email
import time
from datetime import datetime

def read_email_from_gmail(account, password):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(account, password)
    mail.select('inbox')

    result, data = mail.search(None, 'ALL')
    mail_ids = data[0]

    id_list = mail_ids.split()   
    first_email_id = int(id_list[0])
    latest_email_id = int(id_list[-1])

    current_time_seconds = time.time()
    res = []

    for i in range(latest_email_id,first_email_id, -1):
        result, data = mail.fetch(str(i), '(RFC822)' )

        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                email_subject = msg['subject']
                email_from = msg['from']
                email_received_time = msg['Date']
                if 'GMT' in email_received_time:
                    received_time_obj = datetime.strptime(email_received_time, "%a, %d %b %Y %H:%M:%S %Z")
                elif 'UTC' in email_received_time:
                    received_time_obj = datetime.strptime(email_received_time, "%a, %d %b %Y %H:%M:%S %z (UTC)")
                else: 
                    received_time_obj = datetime.strptime(email_received_time, "%a, %d %b %Y %H:%M:%S %z")
                
                time_diff = current_time_seconds - received_time_obj.timestamp()
                if time_diff <= 60 * 10:
                    res.append({
                        'subject': email_subject,
                        'received_time': str(received_time_obj)
                    })
    
    return res

