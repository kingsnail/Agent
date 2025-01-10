# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText


def send_email(m_from, m_to, m_subject, m_body):

    print("body:")
    print(m_body)
    
    # Create a text/plain message
    msg = MIMEText(m_body)

    msg['Subject'] = m_subject
    msg['From'] = m_from
    msg['To'] = m_to

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(m_from, gmail_password) #login with mail_id and password
    s.sendmail(m_from, [m_to], msg.as_string())
    s.quit()
