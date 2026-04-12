class EMAFilter:
    def __init__(self, alpha, initial_value=0):
        """
        EMA(Exponential Moving Average) filter for smoothing potentiometer readings.
        alpha: Smoothing factor (0.0 to 1.0). 
               Higher = more responsive, less smooth.
               Lower = slower response, very smooth.
        """
        self.alpha = alpha
        self.current_value = initial_value

    def filter(self, raw_value):
        # The EMA formula: y[n] = α * x[n] + (1 - α) * y[n-1]
        self.current_value = (self.alpha * raw_value) + (1 - self.alpha) * self.current_value
        return self.current_value