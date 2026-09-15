import math

from pid_controller import PIDController


def test_p_only_moves_toward_setpoint():
    pid = PIDController(kp=0.5, output_limits=(-10, 10))
    measurement = 100.0
    for _ in range(300):
        error = 0.0 - measurement
        output = pid.update(error, measurement, dt=0.1)
        measurement += output * 0.1  # plant: position changes by output*dt
    assert abs(measurement) < 1.0


def test_ki_eliminates_steady_state_error():
    # plant with a constant disturbance that pure P cannot fully reject
    pid = PIDController(kp=0.2, ki=0.5, output_limits=(-50, 50))
    measurement = 0.0
    disturbance = 2.0
    for _ in range(500):
        error = 10.0 - measurement
        output = pid.update(error, measurement, dt=0.1)
        measurement += output * 0.1 + disturbance * 0.1
    assert abs(10.0 - measurement) < 0.5


def test_output_clamped_to_limits():
    pid = PIDController(kp=100.0, output_limits=(-5, 5))
    out = pid.update(error=1000.0, measurement=0.0, dt=0.1)
    assert out == 5.0
    out = pid.update(error=-1000.0, measurement=0.0, dt=0.1)
    assert out == -5.0


def test_integral_windup_clamped():
    pid = PIDController(kp=0.0, ki=1.0, output_limits=(-10, 10), integral_limit=3.0)
    for _ in range(1000):
        pid.update(error=1000.0, measurement=0.0, dt=0.1)
    assert pid._integral == 3.0  # bounded, not 100 * 1000


def test_derivative_on_measurement_no_setpoint_kick():
    # change the setpoint; derivative-on-measurement must not spike
    pid = PIDController(kp=0.0, ki=0.0, kd=1.0, output_limits=(-100, 100))
    pid.update(error=0.0, measurement=10.0, dt=0.1)
    out = pid.update(error=50.0, measurement=10.0, dt=0.1)  # setpoint jump only
    assert abs(out) < 1e-9


def test_derivative_responds_to_measured_change():
    pid = PIDController(kp=0.0, ki=0.0, kd=1.0, output_limits=(-100, 100))
    pid.update(error=0.0, measurement=10.0, dt=0.1)
    out = pid.update(error=0.0, measurement=12.0, dt=0.1)
    assert math.isclose(out, -20.0)  # -kd * d(measurement)/dt


def test_reset_clears_state():
    pid = PIDController(kp=1.0, ki=1.0, kd=1.0)
    pid.update(error=100.0, measurement=0.0, dt=0.1)
    pid.reset()
    assert pid._integral == 0.0
    assert pid._previous_measurement is None
    assert pid.last_output == 0.0
