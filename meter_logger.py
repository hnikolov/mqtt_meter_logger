#!/usr/bin/python

from mqttconnection import MQTTConnection
import datetime, sys
import time, schedule


class MeterLogger():
    """ Collect data via mqtt, re-publish processed data, log data to files """
    def __init__(self):

        self.temperature  = { 'name': 'temperature', 'samples':[] }
        self.electricity  = { 'name': 'electricity', 'samples':[] }
        self.water        = { 'name': 'water',       'samples':[] }
        self.gas          = { 'name': 'gas',         'samples':[] }

        self.current_hour = { 'T': '', 'E': '', 'W': '', 'G': ''}
        self.current_day  = { 'T': '', 'E': '', 'W': '', 'G': ''}
        
        self.temp_temperature = 0.0
        self.temp_electricity = 0.0
        
#        self.hour_temperature = 0.0
        self.hour_electricity = 0
        self.hour_water       = 0
        self.hour_gas         = 0.0
        
        self.day_temperature  = 0.0
        self.day_electricity  = 0
        self.day_water        = 0
        self.day_gas          = 0.0
        
        self.day_history = {}
        
        self.hour = time.localtime().tm_hour
        
        # MQTT connection
        self.mqtt_client = MQTTConnection( client_id     = "power_meter_logger"
                                         , clean_session = False
                                         , userdata      = None
                                         , protocol      = "MQTTv311"
                                         , ip_address    = "192.168.2.100"
                                         , port          = 1883
                                         , keepalive     = 60)
         
        self.QoS    = 0
        self.retain = True 

        self.mqtt_client.will_set(topic = "power_meter/logger/status", payload="offline", qos=self.QoS, retain=self.retain)
        self.mqtt_client.on_connect     = self.on_connect
        self.mqtt_client.on_message     = self.on_message
        self.mqtt_client.on_disconnect  = self.on_disconnect

        self.mqtt_topic_electricity     = "power_meter/electricity"
        self.mqtt_topic_temperature     = "power_meter/temperature"
        self.mqtt_topic_water           = "power_meter/water"
        self.mqtt_topic_gas             = "power_meter/gas"
        self.mqtt_topic_request         = "power_meter_logger/request"
        
        
    # MQTT handler ===============================================================================
    def on_connect(self, client, userdata, flags, rc):
        """ The callback for when the client receives a CONNACK response from the server.
            Subscribing in on_connect() means that if we lose the connection and
            reconnect then subscriptions will be renewed.
        """
        client.subscribe(self.mqtt_topic_temperature)
        client.subscribe(self.mqtt_topic_electricity)
        client.subscribe(self.mqtt_topic_water)
        client.subscribe(self.mqtt_topic_gas)
#        client.subscribe("power_meter/procesed/#")
        
        print "Connected with result code:", str(rc)
        print "Connected to: " + self.mqtt_client.ip_address

        self.mqtt_client.publish(topic="power_meter/logger/status",   payload="online",       qos=self.QoS, retain=self.retain)
        self.mqtt_client.publish(topic="power_meter/processed/water", payload=self.day_water, qos=self.QoS, retain=self.retain)
        self.mqtt_client.publish(topic="power_meter/processed/gas",   payload=self.day_gas,   qos=self.QoS, retain=self.retain)


    def on_message(self, client, userdata, msg):
        """ The callback for when a PUBLISH message is received from the server. """
        st = datetime.datetime.fromtimestamp(msg.timestamp).strftime('%Y-%m-%d %H:%M:%S')
#        print st,  ":", msg.topic, ":", msg.payload

        # Note: timestamps may be off because of retain = True
        if msg.topic == self.mqtt_topic_temperature:
            value = float(msg.payload)
            
            self.mqtt_client.publish("power_meter/processed/temperature", value, self.QoS, self.retain)
            
            if value != self.temp_temperature:
                self.temp_temperature = value
                self.temperature['samples'].append({'value': value, 'timestamp': msg.timestamp})
        
        elif msg.topic == self.mqtt_topic_electricity:
            value_kwh = round( 3.6/float(msg.payload), 3) 
                       
            self.mqtt_client.publish("power_meter/processed/electricity", value_kwh, self.QoS, self.retain)
            
            self.hour_electricity += 1 # 1 impulse == 1 watt
            
            if value_kwh != self.temp_electricity:
                self.temp_electricity = value_kwh
                self.electricity['samples'].append({'value': value_kwh, 'timestamp': msg.timestamp})

        elif msg.topic == self.mqtt_topic_water:
            self.hour_water += int(msg.payload) # +1 (Litre)
            self.day_water  += int(msg.payload) # +1 (Litre)
            self.mqtt_client.publish("power_meter/processed/water", self.day_water, self.QoS, self.retain)
            self.water['samples'].append({'value': self.day_water, 'timestamp': msg.timestamp})
        
        elif msg.topic == self.mqtt_topic_gas:
#            self.day_gas = self.day_gas + int(msg.payload) # +1 (1 impuls == 10 Litres)
            self.hour_gas += 0.01 # m3
            self.day_gas  += 0.01 # m3
            self.mqtt_client.publish("power_meter/processed/gas", self.day_gas, self.QoS, self.retain)
            self.gas['samples'].append({'value': round(self.day_gas, 2), 'timestamp': msg.timestamp})
        
        elif msg.topic == self.mqtt_topic_request:
            for topic, payload in self.day_history.iteritems():
                self.mqtt_client.publish(topic, payload, self.QoS, self.retain)


    def on_disconnect(self, client, userdata, msg):
        """ The callback for when disconnect from the server. """
        print "Disconnected:", msg

        
    # Logger Job =================================================================================
    def job_logger(self):
        # TODO: Dump json objects to files
        
        hour_temperature = 0
        if len(self.temperature["samples"]) > 0:
            for t in self.temperature["samples"]:
                hour_temperature += t["value"]
#                print "T:", t["value"]
            hour_temperature = round( hour_temperature/len(self.temperature["samples"]), 2)
                
                                         
        hour_electricity_kwh = float(self.hour_electricity)/1000
        hour_gas_m3          = round(self.hour_gas, 3)

        self.hour            = time.localtime().tm_hour
        topic                = "power_meter/processed/" + str(self.hour)
        self.current_hour    = { 'T': hour_temperature, 'E': hour_electricity_kwh, 'W': self.hour_water, 'G': hour_gas_m3 }
        payload              = str(self.current_hour)        
        self.mqtt_client.publish(topic, payload, self.QoS, self.retain)
        
#        print payload

        self.day_history[topic] = self.current_hour
        
        #-------------------------------------------------------------------------------------------
        self.day_temperature = 0
        if len(self.day_history) > 0:
            for _, value in self.day_history.iteritems():
                self.day_temperature += value["T"]                
            self.day_temperature = round(self.day_temperature/len(self.day_history), 2)      
            
        self.day_electricity += hour_electricity_kwh
#        self.day_water       += self.hour_water
#        self.day_gas         += hour_gas_m3 

        topic             = "power_meter/processed/today"
        self.current_day  = { 'T': self.day_temperature, 'E': round(self.day_electricity, 3), 'W': self.day_water, 'G': self.day_gas }
        payload           = str(self.current_day)
        self.mqtt_client.publish(topic, payload, self.QoS, self.retain)
        
#        print payload
#        print "---------------------------------------------"

        # Clear the samples of the hour
#        self.hour_temperature = 0.0
        self.hour_electricity       = 0        
        self.hour_water             = 0
        self.hour_gas               = 0.0      
          
        self.temperature['samples'] = []
        self.electricity['samples'] = []
        self.water['samples']       = []
        self.gas['samples']         = []
        
        if self.hour == 0: # new day
            self.mqtt_client.publish("power_meter/processed/yesterday", payload, self.QoS, self.retain)
        
            self.temp_temperature = 0.0
            self.temp_electricity = 0.0
            
            self.day_temperature  = 0.0
            self.day_electricity  = 0
            self.day_water        = 0
            self.day_gas          = 0.0

            self.mqtt_client.publish("power_meter/processed/water", self.day_water, self.QoS, self.retain)
            self.mqtt_client.publish("power_meter/processed/gas",   self.day_gas,   self.QoS, self.retain)

        
    def job_mqtt_connect(self):
        self.mqtt_client.connect()
        return schedule.CancelJob # run the job only once

                
    # ============================================================================================            
    def run(self):
        schedule.every(10).seconds.do(self.job_mqtt_connect) # delay the connection to allow the mqtt broker to start (@reboot)
        schedule.every().hour.at(":00").do(self.job_logger)

#        schedule.every(10).seconds.do(self.job_logger)
#        schedule.every().minute.do(self.job_logger)        
#        schedule.every(2).minutes.do(self.job_logger)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
        
                        
if __name__ == '__main__':
    myApp = MeterLogger()
    myApp.run()

