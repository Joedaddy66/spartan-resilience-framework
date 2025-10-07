"""
Resource monitor for telemetry and unit economics tracking.
Calibrated with real-world cloud provider rates.
"""
import time
import os
from datetime import datetime
from typing import Dict, Optional


class ResourceMonitor:
    """Monitor resource usage and calculate unit economics."""
    
    def __init__(self):
        # Calibrated cost models from environment or defaults
        # Default: GPT-3.5-turbo pricing as baseline ($0.001/1K input tokens)
        self.cost_per_1k_input_tokens = float(
            os.getenv("COST_PER_1K_INPUT_TOKENS", "0.001")
        )
        self.cost_per_1k_output_tokens = float(
            os.getenv("COST_PER_1K_OUTPUT_TOKENS", "0.002")
        )
        
        # Energy consumption (example values - should be calibrated)
        # Average ML inference: ~0.5 Wh per 1000 tokens
        self.energy_wh_per_1k_tokens = float(
            os.getenv("ENERGY_WH_PER_1K_TOKENS", "0.5")
        )
        
        # Carbon intensity varies by region (g CO2 per kWh)
        # Default: US grid average ~400 g/kWh
        self.carbon_intensity_g_per_kwh = float(
            os.getenv("CARBON_INTENSITY_G_PER_KWH", "400")
        )
        
        # Compute cost per hour (e.g., GPU instance cost)
        self.compute_cost_per_hour = float(
            os.getenv("COMPUTE_COST_PER_HOUR", "1.00")
        )
        
        self.metrics = []
    
    def _cost(self, token_count: int, token_type: str = "input") -> float:
        """
        Calculate cost for tokens based on calibrated rates.
        
        Args:
            token_count: Number of tokens processed
            token_type: 'input' or 'output' tokens
            
        Returns:
            Cost in USD
        """
        if token_type == "output":
            rate = self.cost_per_1k_output_tokens
        else:
            rate = self.cost_per_1k_input_tokens
            
        return round((rate / 1000) * token_count, 5)
    
    def _energy_joules(self, token_count: int) -> float:
        """
        Calculate energy consumption in joules.
        
        Args:
            token_count: Number of tokens processed
            
        Returns:
            Energy in joules
        """
        # Convert Wh to joules: 1 Wh = 3600 J
        wh = (self.energy_wh_per_1k_tokens / 1000) * token_count
        return round(wh * 3600, 2)
    
    def _carbon_kg(self, energy_joules: float) -> float:
        """
        Calculate carbon emissions in kg CO2.
        
        Args:
            energy_joules: Energy consumed in joules
            
        Returns:
            Carbon emissions in kg CO2
        """
        # Convert joules to kWh: 1 kWh = 3.6e6 J
        kwh = energy_joules / 3.6e6
        # Calculate emissions based on grid carbon intensity
        carbon_g = kwh * self.carbon_intensity_g_per_kwh
        return round(carbon_g / 1000, 6)  # Convert to kg
    
    def log_inference(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Log inference metrics with unit economics calculation.
        
        Args:
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Inference duration in milliseconds
            metadata: Additional metadata
            
        Returns:
            Metrics dictionary
        """
        total_tokens = input_tokens + output_tokens
        
        # Calculate costs
        input_cost = self._cost(input_tokens, "input")
        output_cost = self._cost(output_tokens, "output")
        total_cost = input_cost + output_cost
        
        # Calculate energy and carbon
        energy_joules = self._energy_joules(total_tokens)
        carbon_kg = self._carbon_kg(energy_joules)
        
        # Calculate compute cost (time-based)
        compute_hours = duration_ms / (1000 * 3600)
        compute_cost = self.compute_cost_per_hour * compute_hours
        
        # Total unit cost
        unit_cost_usd = total_cost + compute_cost
        
        metrics = {
            "timestamp": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "duration_ms": duration_ms,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "compute_cost_usd": round(compute_cost, 5),
            "unit_cost_usd": round(unit_cost_usd, 5),
            "energy_joules": energy_joules,
            "carbon_kg": carbon_kg,
            "carbon_intensity_g_per_kwh": self.carbon_intensity_g_per_kwh,
        }
        
        if metadata:
            metrics["metadata"] = metadata
        
        self.metrics.append(metrics)
        return metrics
    
    def log_training(
        self,
        model: str,
        duration_hours: float,
        gpu_count: int = 1,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Log training job metrics with unit economics.
        
        Args:
            model: Model identifier
            duration_hours: Training duration in hours
            gpu_count: Number of GPUs used
            metadata: Additional metadata
            
        Returns:
            Metrics dictionary
        """
        # Training is more compute-intensive
        compute_cost = self.compute_cost_per_hour * duration_hours * gpu_count
        
        # Estimate energy (training is ~10x more intensive than inference per hour)
        # Typical GPU: ~250W, for duration_hours
        energy_kwh = 0.250 * duration_hours * gpu_count
        energy_joules = energy_kwh * 3.6e6
        
        carbon_kg = self._carbon_kg(energy_joules)
        
        metrics = {
            "timestamp": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
            "type": "training",
            "model": model,
            "duration_hours": duration_hours,
            "gpu_count": gpu_count,
            "compute_cost_usd": round(compute_cost, 2),
            "energy_joules": round(energy_joules, 2),
            "carbon_kg": carbon_kg,
            "carbon_intensity_g_per_kwh": self.carbon_intensity_g_per_kwh,
        }
        
        if metadata:
            metrics["metadata"] = metadata
        
        self.metrics.append(metrics)
        return metrics
    
    def get_metrics(self) -> list:
        """Get all collected metrics."""
        return self.metrics
    
    def reset_metrics(self):
        """Clear collected metrics."""
        self.metrics = []
