class PricingService:
    def __init__(self, base_rate: float = 1.0):
        self.base_rate = base_rate

    def calculate_cost(self, minutes: int) -> float:
        # FIX: Ensure minutes are not negative using max()
        safe_minutes = max(0, minutes) 
        
        return round(safe_minutes * self.base_rate, 2)