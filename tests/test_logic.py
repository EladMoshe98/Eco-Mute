from app.services.pricing import PricingService


def test_pricing_calculation():
    service = PricingService(base_rate=2.0)
    result = service.calculate_cost(10)
    assert result == 20.0


def test_pricing_negative_minutes():
    service = PricingService(base_rate=2.0)
    result = service.calculate_cost(-5)
    assert result == 0.0