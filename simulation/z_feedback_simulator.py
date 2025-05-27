# simulation/z_feedback_simulator.py

class ZFeedbackSimulator:
    """
    Simulates Z-feedback control loop behavior using a PID-like response.
    Adjusts Z-position to maintain setpoint relative to virtual tip height.
    """

    def __init__(self, kp=1.2, ki=0.05, kd=0.01, setpoint=0.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint

        self.z_position = 0.0
        self.last_error = 0.0
        self.integral = 0.0

    def reset(self):
        """
        Reset feedback loop state.
        """
        self.z_position = 0.0
        self.last_error = 0.0
        self.integral = 0.0

    def update(self, measured_value):
        """
        Perform one feedback loop iteration. Return new z_position.
        """
        error = self.setpoint - measured_value
        self.integral += error
        derivative = error - self.last_error

        correction = (
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )

        self.z_position += correction
        self.last_error = error

        return self.z_position

    def set_pid(self, kp=None, ki=None, kd=None):
        """
        Update PID parameters dynamically.
        """
        if kp is not None:
            self.kp = kp
        if ki is not None:
            self.ki = ki
        if kd is not None:
            self.kd = kd

    def set_setpoint(self, value):
        """
        Update the target setpoint value.
        """
        self.setpoint = value
