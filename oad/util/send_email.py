import smtplib, ssl
import subprocess
import os

"""
https://pthree.org/2012/01/07/encrypted-mutt-imap-smtp-passwords/
https://gist.github.com/bnagy/8914f712f689cc01c267
"""


def send_email(receiver_email, subject, html):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "scott.m.kyle@gmail.com"  # Enter your address
    receiver_email = "scott.m.kyle@gmail.com"  # Enter receiver address
    # password = subprocess.check_output("gpg -dq ~/.mutt/passwords.gpg | awk '{print $4}'",shell=True).decode('utf-8').rstrip().replace("\"", "")
    
    password = 
    # print (password)
    message = "Subject: {}\n\n{}".format(subject, html)

    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL(smtp_server, port, context=context)
    server.ehlo()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)
    server.quit()
