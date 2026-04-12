from storage.app_config import PotCalibration


class AdaptiveEMAFilter:
    def __init__(self, calibration: PotCalibration):
        """
        Adaptive EMA(Exponential Moving Average) filter that smooths potentiometer readings while allowing for quick response to fast movements.
        min_alpha: Alpha used when the knob is still (max stability).
        max_alpha: Alpha used during fast movements (max responsiveness).
        sensitivity: How quickly the filter 'wakes up' to movement.
        """
        self.calibration = calibration
        self.current_value = 0
        self.first_run = True

    def filter(self, raw_value):
        if self.first_run:
            self.current_value = raw_value
            self.first_run = False
            return raw_value

        # 1. Calculate the 'error' (how far did we move?)
        # We normalize this based on the expected range
        diff = abs(raw_value - self.current_value) / (self.calibration.max_value - self.calibration.min_value)

        # 2. Calculate a dynamic alpha based on movement speed
        # This creates a ramp: more movement = higher alpha
        dynamic_alpha = self.calibration.ema_filter_alpha_min + (diff * self.calibration.ema_filter_sensitivity * (self.calibration.ema_filter_alpha_max - self.calibration.ema_filter_alpha_min))

        # 3. Clamp alpha to our max limit
        alpha = min(dynamic_alpha, self.calibration.ema_filter_alpha_max)

        # 4. Standard EMA formula
        # y[n] = α * x[n] + (1 - α) * y[n-1]
        self.current_value = (alpha * raw_value) + (1 - alpha) * self.current_value

        return self.current_value