"""
Tests for telemetry resource monitor.
"""
import sys
import pathlib
import os

# Add packages to path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from packages.telemetry.resource_monitor import ResourceMonitor


def test_resource_monitor_initialization():
    """Test that ResourceMonitor initializes with defaults."""
    rm = ResourceMonitor()
    assert rm.cost_per_1k_input_tokens == 0.001
    assert rm.cost_per_1k_output_tokens == 0.002
    assert rm.energy_wh_per_1k_tokens == 0.5
    assert rm.carbon_intensity_g_per_kwh == 400
    assert rm.compute_cost_per_hour == 1.00


def test_resource_monitor_env_config():
    """Test that ResourceMonitor reads from environment."""
    os.environ["COST_PER_1K_INPUT_TOKENS"] = "0.003"
    os.environ["CARBON_INTENSITY_G_PER_KWH"] = "250"
    
    rm = ResourceMonitor()
    assert rm.cost_per_1k_input_tokens == 0.003
    assert rm.carbon_intensity_g_per_kwh == 250
    
    # Clean up
    del os.environ["COST_PER_1K_INPUT_TOKENS"]
    del os.environ["CARBON_INTENSITY_G_PER_KWH"]


def test_log_inference():
    """Test inference metrics logging."""
    rm = ResourceMonitor()
    metrics = rm.log_inference(
        model="gpt-3.5-turbo",
        input_tokens=100,
        output_tokens=50,
        duration_ms=250
    )
    
    assert metrics["model"] == "gpt-3.5-turbo"
    assert metrics["input_tokens"] == 100
    assert metrics["output_tokens"] == 50
    assert metrics["total_tokens"] == 150
    assert metrics["duration_ms"] == 250
    assert "timestamp" in metrics
    assert "unit_cost_usd" in metrics
    assert "energy_joules" in metrics
    assert "carbon_kg" in metrics
    assert metrics["unit_cost_usd"] > 0
    assert metrics["carbon_intensity_g_per_kwh"] == 400


def test_log_training():
    """Test training metrics logging."""
    rm = ResourceMonitor()
    metrics = rm.log_training(
        model="custom-model-v1",
        duration_hours=2.5,
        gpu_count=4
    )
    
    assert metrics["model"] == "custom-model-v1"
    assert metrics["type"] == "training"
    assert metrics["duration_hours"] == 2.5
    assert metrics["gpu_count"] == 4
    assert "compute_cost_usd" in metrics
    assert "energy_joules" in metrics
    assert "carbon_kg" in metrics
    assert metrics["compute_cost_usd"] > 0


def test_cost_calculation():
    """Test cost calculation accuracy."""
    rm = ResourceMonitor()
    
    # Test input tokens cost
    cost = rm._cost(1000, "input")
    assert cost == 0.001  # 1000 tokens at $0.001/1k
    
    # Test output tokens cost
    cost = rm._cost(1000, "output")
    assert cost == 0.002  # 1000 tokens at $0.002/1k


def test_energy_calculation():
    """Test energy calculation."""
    rm = ResourceMonitor()
    
    # Test energy for 1000 tokens
    energy_j = rm._energy_joules(1000)
    # 1000 tokens * 0.5 Wh/1000 = 0.5 Wh = 1800 J
    assert energy_j == 1800


def test_carbon_calculation():
    """Test carbon calculation."""
    rm = ResourceMonitor()
    
    # Test carbon for 1800 J (0.5 Wh)
    carbon = rm._carbon_kg(1800)
    # 0.5 Wh = 0.0005 kWh * 400 g/kWh = 0.2 g = 0.0002 kg
    assert carbon == 0.0002


def test_metrics_collection():
    """Test metrics collection and reset."""
    rm = ResourceMonitor()
    
    # Log some metrics
    rm.log_inference("model1", 100, 50, 250)
    rm.log_inference("model2", 200, 100, 500)
    
    metrics = rm.get_metrics()
    assert len(metrics) == 2
    assert metrics[0]["model"] == "model1"
    assert metrics[1]["model"] == "model2"
    
    # Reset
    rm.reset_metrics()
    assert len(rm.get_metrics()) == 0


def test_metadata_support():
    """Test that metadata is properly stored."""
    rm = ResourceMonitor()
    
    metadata = {"user_id": "123", "session": "abc"}
    metrics = rm.log_inference(
        model="test-model",
        input_tokens=100,
        output_tokens=50,
        duration_ms=250,
        metadata=metadata
    )
    
    assert "metadata" in metrics
    assert metrics["metadata"]["user_id"] == "123"
    assert metrics["metadata"]["session"] == "abc"
