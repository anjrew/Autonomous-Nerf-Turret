"""A self-contained PID controller for turret aiming.

The controller uses derivative-on-measurement (so a setpoint change does
not produce a derivative kick) and clamps the integral term to prevent
windup while the actuator is saturated.
"""

from typing import Optional, Tuple


class PIDController:
    """PID controller: output = Kp*e + Ki*integral(e) + Kd*de/dt.

    Args:
        kp: Proportional gain.
        ki: Integral gain.
        kd: Derivative gain.
        output_limits: Inclusive (min, max) the output is clamped to.
        integral_limit: Absolute bound on the accumulated integral term.
            Defaults to half the output span when output_limits is set.
    """

    def __init__(
        self,
        kp: float,
        ki: float = 0.0,
        kd: float = 0.0,
        output_limits: Optional[Tuple[float, float]] = None,
        integral_limit: Optional[float] = None,
    ) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limits = output_limits
        if integral_limit is None and output_limits is not None:
            lo, hi = output_limits
            integral_limit = abs(hi - lo) / 2
        self.integral_limit = integral_limit

        self._integral = 0.0
        self._previous_measurement: Optional[float] = None
        self._last_output: float = 0.0

    def reset(self) -> None:
        """Clear all controller state (call when switching targets)."""
        self._integral = 0.0
        self._previous_measurement = None
        self._last_output = 0.0

    def update(self, error: float, measurement: float, dt: float) -> float:
        """Advance the controller one step.

        Args:
            error: setpoint - measurement, in the same units as the
                measurement itself.
            measurement: the current measured value. Used (not the error)
                for the derivative term, so a setpoint change cannot kick
                the output.
            dt: seconds since the previous update. Must be > 0.

        Returns:
            The clamped controller output.
        """
        proportional = self.kp * error

        self._integral += error * dt
        if self.integral_limit is not None:
            self._integral = max(
                -self.integral_limit, min(self.integral_limit, self._integral)
            )
        integral = self.ki * self._integral

        derivative = 0.0
        if self._previous_measurement is not None and dt > 0:
            derivative = -self.kd * (measurement - self._previous_measurement) / dt
        self._previous_measurement = measurement

        output = proportional + integral + derivative
        if self.output_limits is not None:
            lo, hi = self.output_limits
            output = max(lo, min(hi, output))
        self._last_output = output
        return output

    @property
    def last_output(self) -> float:
        return self._last_output
