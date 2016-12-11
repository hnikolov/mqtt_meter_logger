import smtplib
from email.mime.text import MIMEText

from collections import OrderedDict

#def emailResults(folder, filename):
def email_send( msg_content ):

    # Mesage body
#    doc = folder + filename + '.txt'
#    with open(doc, 'r') as readText:
#        msg = MIMEText(readText.read())

    msg = MIMEText( msg_content )
    
    # Settings
    FROM = 'h_nikolov@mail.ru'
    PSWD = 'Buba'
    TO   = FROM
#    TO   = 'h.n.nikolov@gmail.com'    
    
    # Headers
    msg['To']      = TO
    msg['From']    = FROM
    msg['Subject'] = 'Test e-mail'

#    print msg
    
    # SMTP
    send = smtplib.SMTP('smtp.mail.ru', 587)
    send.starttls()
    send.login   ( FROM, PSWD)
    send.sendmail( FROM, TO, msg.as_string() )
    send.quit()

    
if __name__ == '__main__':
    msg = "My test e-mail sent from python."

    # Init a day history ordered dict
    keys = []    
    for i in range(1,25):
        topic = "power_meter/processed/" + str(i)
        keys.append(topic)
    
    items = [(key, None) for key in keys] 
    day_history = OrderedDict(items)
    
    # Initialize data
    for i in range(1,25):
        topic = "power_meter/processed/" + str(i)
        current_hour = { 'T': i, 'E': i, 'W': i, 'G': i }
        day_history[topic] = current_hour
        
    # Send e-mail
    email_send( str(day_history) )

