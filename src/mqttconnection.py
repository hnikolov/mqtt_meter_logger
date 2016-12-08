import paho.mqtt.client as mqtt
# to start the server: /usr/local/sbin/mosquitto -c /etc/mosquitto/mosquitto.conf

class MQTTConnection(mqtt.Client):
    """ Class to manage MQTT connections """
    def __init__(self, client_id="", clean_session=False, userdata=None, protocol="MQTTv311", ip_address="localhost", port=1883, keepalive=60):
        mqtt.Client.__init__(self, client_id=client_id, clean_session=clean_session, userdata=userdata, protocol=protocol)

        self.ip_address = ip_address
        self.port       = port
        self.keepalive  = keepalive

        self.isConnected = False

    def connect(self):
        mqtt.Client.connect(self, self.ip_address, self.port, self.keepalive)
        self.loop_start()

    def disconnect(self):
        mqtt.Client.disconnect(self)
        self.loop_stop()
