import time

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

    def init(self):
        '''
        Initialize Step. This method is called once at the beginning of the step
        :return: 
        '''
        # set target tep
        #self.set_target_temp(self.temp, self.kettle)

    def finish(self):
        self.set_target_temp(0, self.kettle)

    def execute(self):
        '''
        This method is execute in an interval
        :return: 
        '''
        sensorValue1 = float(cbpi.get_sensor_value(int(self.sensor1)))
        sensorValue2 = float(cbpi.get_sensor_value(int(self.sensor2)))
        volumeChange = sensorValue2 - float(self.volumeStart)
        volumeFlow = sensorValue1 - float(volumeChange)
        
        for key, value in cbpi.cache["actors"].iteritems():
            if key == int(self.actor1):
                actorState1 = value.state
            if key == int(self.actor2):
                actorState2 = value.state
                
        # Check if kettle2 volume limit reached
        if float(sensorValue2) <= float(self.volume2):
            self.set_target_temp(0, self.kettle2)
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
            if volumeFlow >= 0:
                if volumeFlow < float(self.volumeDiff):
                    self.actor_on(int(self.actor1))
                    self.actor_on(int(self.actor2))
                else:
                    self.actor_off(int(self.actor1))
            else:
                if abs(volumeFlow) >= float(self.volumeDiff):
                    self.actor_off(int(self.actor2))
        
        # Check if kettle1 target volume has been reached
        if sensorValue1 >= float(self.volume1):
            self.set_target_temp(0, self.kettle2)
            self.notify("Sparge Complete!", "Starting the next step.", timeout=None)
            self.next()