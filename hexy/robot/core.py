from ..comm.pwm import PWM
from time import sleep

""" joint_key convention:
    R - right, L - left
    F - front, M - middle, B - back
    H - hip, K - knee, A - Ankle
    key : (channel, minimum_pulse_length, maximum_pulse_length, direction) """

joint_properties = {

    'RFH': (6, 160, 590, 1), 'RFK': (7, 160, 590, 1), 'RFA': (8, 160, 590, 1),
    'RMH': (6, 160, 590, 1), 'RMK': (7, 160, 590, 1), 'RMA': (8, 160, 590, 1),
    'RBH': (3, 160, 590, 1), 'RBK': (4, 160, 590, 1), 'RBA': (5, 160, 590, 1),
    'LFH': (3, 160, 590, 1), 'LFK': (4, 160, 590, 1), 'LFA': (5, 160, 590, 1),
    'LMH': (0, 160, 590, 1), 'LMK': (1, 160, 590, 1), 'LMA': (2, 160, 590, 1),
    'LBH': (0, 160, 590, 1), 'LBK': (1, 160, 590, 1), 'LBA': (2, 160, 590, 1),
    'N': (9, 170, 620, 1)
}

driver1_legs = ['RFH', 'RFK', 'RFA', 
                'LFH', 'LFK', 'LFA', 
                'LMH', 'LMK', 'LMA', 
                'N']

driver1 = PWM(0x41)
driver2 = PWM(0x40)

driver1.setPWMFreq(60)
driver2.setPWMFreq(60)


def drive(ch, name, pulse):
  driver = driver1 if name in driver1_legs else driver2
  driver.setPWM(ch, 0, pulse)


def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))


def remap(old_val, (old_min, old_max), (new_min, new_max)):
    new_diff = (new_max - new_min)*(old_val - old_min) / float((old_max - old_min))
    return int(round(new_diff)) + new_min 

                 
class HexapodCore:

    def __init__(self):

        self.neck = Joint("neck", 'N', 90, -90)

        self.left_front = Leg('left front', 'LFH', 'LFK', 'LFA')
        self.right_front = Leg('right front', 'RFH', 'RFK', 'RFA')

        self.left_middle = Leg('left middle', 'LMH', 'LMK', 'LMA')
        self.right_middle = Leg('right middle', 'RMH', 'RMK', 'RMA')
        
        self.left_back = Leg('left back', 'LBH', 'LBK', 'LBA')
        self.right_back = Leg('right back', 'RBH', 'RBK', 'RBA')

        self.legs = [self.left_front, self.right_front,
                     self.left_middle, self.right_middle,
                     self.left_back, self.right_back]

        self.right_legs = [self.right_front, self.right_middle, self.right_back]
        self.left_legs = [self.left_front, self.left_middle, self.left_back]

        self.tripod1 = [self.left_front, self.right_middle, self.left_back]
        self.tripod2 = [self.right_front, self.left_middle, self.right_back]
        
        self.hips, self.knees, self.ankles = [], [], []

        for leg in self.legs:
            self.hips.append(leg.hip)
            self.knees.append(leg.knee)
            self.ankles.append(leg.ankle)

    def off(self):

        self.neck.off()
        
        for leg in self.legs:
            leg.off() 


class Leg:

    def __init__(self, name, hip_key, knee_key, ankle_key):

        max_hip, max_knee, max_ankle = 35, 90, 90
        min_hip, min_knee, min_ankle = -35, -20, 0
        
        self.hip = Joint("hip", hip_key, max_hip, min_hip)
        self.knee = Joint("knee", knee_key, max_knee, min_knee)
        self.ankle = Joint("ankle", ankle_key, max_ankle, min_ankle)

        self.name = name
        self.joints = [self.hip, self.knee, self.ankle]

    def pose(self, hip_angle = 0, knee_angle = 0, ankle_angle = 0):

        self.hip.pose(hip_angle)
        self.knee.pose(knee_angle)
        self.ankle.pose(ankle_angle)

    def move(self, knee_angle = None, hip_angle = None, offset = 100):
        """ knee_angle < 0 means thigh is raised, ankle's angle will be set to the specified 
            knee angle minus the offset. offset best between 80 and 110 """

        if knee_angle == None: knee_angle = self.knee.angle
        if hip_angle == None: hip_angle = self.hip.angle

        self.pose(hip_angle, knee_angle, offset - knee_angle)

    def replant(self, raised, floor, offset, t = 0.1):

        self.move(raised)
        sleep(t)

        self.move(floor, offset)
        sleep(t)

    def off(self):
        for joint in self.joints:
            joint.off()
        
    def __repr__(self):
        return 'leg: ' + self.name


class Joint:

    def __init__(self, joint_type, jkey, mx, mn):

        self.joint_type, self.name =  joint_type, jkey
        self.channel, self.min_pulse, self.max_pulse, self.direction = joint_properties[jkey]
        self.min, self.max = mn, mx

        self.off()

    def pose(self, angle = 0):

        angle = constrain(angle, self.min, self.max)
        pulse = remap((angle * self.direction), (-90, 90), (self.min_pulse, self.max_pulse))
        
        drive(self.channel, self.name, pulse)
        self.angle = angle
        
        print repr(self), ':', 'pulse', pulse

    def off(self):
        drive(self.channel, self.name, 0)
        self.angle = None

    def __repr__(self):
        return 'joint: ' + self.joint_type + ' : ' + self.name + ' angle: ' + str(self.angle)
