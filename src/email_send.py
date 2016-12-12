import smtplib
from email.mime.text import MIMEText

from collections import OrderedDict
import simplejson

#def emailResults(folder, filename):
def email_send( msg_content ):

    # Mesage body
#    doc = folder + filename + '.txt'
#    with open(doc, 'r') as readText:
#        msg = MIMEText(readText.read())

    msg = MIMEText( msg_content )
    
    # NOTE: e-mail and pswd read from file
    filename = "/.mqtt_logger"
    f = open( filename )
    try:
        json_struct = simplejson.load(f)
    except Exception as e:
        print "ERROR: Cannot load .json file: ", filename
        print "      ", e
        exit(1)
    f.close()
            
    # Settings
    FROM = json_struct['user']
    PSWD = json_struct['password']
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
        
#    print simplejson.dumps(day_history)
    
    # Send e-mail
    email_send( str(day_history) )
    
    # TODO: Create a class; Use simplejson

