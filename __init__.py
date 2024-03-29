import time

from modules.kettle import *

from modules.core.props import Property, StepProperty
from modules.core.step import StepBase
from modules import cbpi

@cbpi.step
class SpargeStep(StepBase):
    '''
    Just put the decorator @cbpi.step on top of a method. The class name must be unique in the system
    '''
    # Properties
    kettle1 = StepProperty.Kettle("Boil Kettle")
    kettle2 = StepProperty.Kettle("HLT Kettle")
    actor1 = StepProperty.Actor("Wort Pump")
    actor2 = StepProperty.Actor("Water Pump")
    sensor1 = StepProperty.Sensor("BK Volume Sensor")
    sensor2 = StepProperty.Sensor("HLT Volume Sensor")
    volume1 = Property.Number("BK Volume Target", configurable=True)
    volume2 = Property.Number("HLT Volume Min", configurable=True)
    volumeStart = Property.Number("HLT Volume Start", configurable=True)
    volumeDiff = Property.Number("Volume Difference", configurable=True)
    timer = Property.Number("Timer in Minutes", configurable=True)
    temp = Property.Number("BK Temp", configurable=True)
    volumeBoil = Property.Number("BK Boil Volume", configurable=True)
    
    volumeState1 = 0
    volumeState2 = 0

    def init(self):
        '''
        Initialize Step. This method is called once at the beginning of the step
        :return: 
        '''
        # set target tep
        #self.set_target_temp(self.temp, self.kettle)

    def finish(self):
        self.set_target_temp(0, self.kettle2)

    def execute(self):
        '''
        This method is execute in an interval
        :return: 
        '''
        sensorValue1 = cbpi.get_sensor_value(int(self.sensor1))
        sensorValue2 = cbpi.get_sensor_value(int(self.sensor2))
        volumeChange1 = float(sensorValue1) - float(self.volumeState1)
        volumeChange2 = float(self.volumeState2) - float(sensorValue2)
        kettle1_state = cbpi.cache.get("kettle")[int(self.kettle1)].state
        kettle2_state = cbpi.cache.get("kettle")[int(self.kettle2)].state
        
        for key, value in cbpi.cache["actors"].iteritems():
            if key == int(self.actor1):
                actorState1 = value.state
            if key == int(self.actor2):
                actorState2 = value.state
                
        if float(sensorValue1) >= float(self.volumeBoil) and kettle1_state is False:
            Kettle2View().toggle(int(self.kettle1))
            self.notify("Kettle Update", "Kettle 1 Auto is on.", timeout=None)
            self.set_target_temp(self.temp, self.kettle1)
                
        # Check if kettle2 volume limit reached
        if float(sensorValue2) <= float(self.volume2):
            if kettle2_state is True:
                self.set_target_temp(0, self.kettle2)
                Kettle2View().toggle(int(self.kettle2))
                self.notify("Kettle Update", "Kettle 2 Auto is off.", timeout=None)
            if self.is_timer_finished() is None:
                self.start_timer(int(self.timer) * 60)
            # Make sure kettle1 hasn't reached target
            if float(sensorValue1) < float(self.volume1):
                self.actor_on(int(self.actor1))
                if self.is_timer_finished() == True:
                    self.actor_off(int(self.actor2))
                else:
                    self.actor_on(int(self.actor2))
        else:
            if self.volumeState1 > 0:
                totalDiff = float(volumeChange2) - float(volumeChange1)
                if totalDiff > 0:
                    if abs(totalDiff) > float(self.volumeDiff):
                        self.actor_off(int(self.actor2))
                        self.actor_on(int(self.actor1))
                    else:
                        self.actor_on(int(self.actor2))
                else:
                    if abs(totalDiff) > float(self.volumeDiff):
                        self.actor_off(int(self.actor1))
                        self.actor_on(int(self.actor2))
                    else:
                        self.actor_on(int(self.actor1))
            else:
                if volumeChange >= 10:
                    self.volumeState2 = sensorValue2
                    self.volumeState1 = sensorValue1
        
        # Check if kettle1 target volume has been reached
        if float(sensorValue1) >= float(self.volume1):
            self.set_target_temp(0, self.kettle2)
            self.stop_timer()
            self.start_timer(0)
            self.notify("Sparge Complete!", "Starting the next step.", timeout=None)
            self.next()