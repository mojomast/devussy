"""HiveMind orchestration engine for swarm-based generation."""

import asyncio
import logging
from typing import List, Optional, Any, Dict

from ..llm_client import LLMClient
from ..templates import render_template

logger = logging.getLogger(__name__)

class HiveMindManager:
    """
    Manages swarm execution (parallel calls) and arbitration for generating
    high-quality development plans.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize the HiveMindManager.

        Args:
            llm_client: The LLM client to use for drone and arbiter calls.
        """
        self.llm_client = llm_client

    async def run_swarm(
        self,
        prompt: str,
        count: int = 3,
        temperature_jitter: bool = True,
        base_temperature: float = 0.7,
        drone_callbacks: Optional[List[Any]] = None,
        arbiter_callback: Optional[Any] = None,
        **llm_kwargs: Any
    ) -> str:
        """
        Execute a swarm of drone calls and then arbitrate the results.

        Args:
            prompt: The input prompt for the drones.
            count: Number of drone instances to run.
            temperature_jitter: Whether to vary temperature across drones.
            base_temperature: The base temperature to jitter around.
            **llm_kwargs: Additional arguments for the LLM calls.

        Returns:
            The synthesized response from the Arbiter.
        """
        logger.info(f"HiveMind: Releasing {count} drones (jitter={temperature_jitter})")

        # 1. Prepare and execute drones
        drone_responses = await self._execute_parallel(
            prompt, count, temperature_jitter, base_temperature,
            drone_callbacks=drone_callbacks,
            **llm_kwargs
        )

        # 2. Format for Arbiter
        arbiter_prompt = self._format_for_arbiter(prompt, drone_responses)

        # 3. Call Arbiter
        logger.info("HiveMind: Arbiter is deliberating...")
        final_response = await self._call_arbiter(
            arbiter_prompt,
            arbiter_callback=arbiter_callback,
            **llm_kwargs
        )

        return final_response

    async def _execute_parallel(
        self,
        prompt: str,
        count: int,
        temperature_jitter: bool,
        base_temperature: float,
        drone_callbacks: Optional[List[Any]] = None,
        **llm_kwargs: Any
    ) -> List[str]:
        """Run parallel drone requests."""
        
        async def execute_drone(i: int):
            """Execute a single drone with its specific configuration."""
            # Calculate temperature for this drone
            if temperature_jitter and count > 1:
                # Spread temperatures: e.g. 0.5, 0.7, 0.9 for count=3, base=0.7
                # Simple spread logic: +/- 0.2 range
                offset = (i / (count - 1) - 0.5) * 0.4 if count > 1 else 0
                temp = max(0.0, min(2.0, base_temperature + offset))
            else:
                temp = base_temperature

            # Create a copy of kwargs to avoid side effects
            drone_kwargs = llm_kwargs.copy()
            drone_kwargs["temperature"] = temp
            
            # Remove streaming handler for drones unless we have a callback
            if "streaming_handler" in drone_kwargs:
                del drone_kwargs["streaming_handler"]
            
            # Check if we have a callback for this drone
            callback = drone_callbacks[i] if drone_callbacks and i < len(drone_callbacks) else None
            
            if callback:
                # Stream this drone's response
                logger.debug(f"Drone {i+1}/{count} launching with temp={temp:.2f} (streaming)")
                response = await self.llm_client.generate_completion_streaming(
                    prompt,
                    callback=callback.on_token_async,
                    **drone_kwargs
                )
                # Notify completion
                await callback.on_completion_async(response)
                return response
            else:
                # No callback, just get full response
                logger.debug(f"Drone {i+1}/{count} launching with temp={temp:.2f}")
                response = await self.llm_client.generate_completion(prompt, **drone_kwargs)
                return response
        
        # Execute all drones concurrently using asyncio.gather
        logger.info(f"Launching {count} drones concurrently...")
        drone_responses = await asyncio.gather(*[execute_drone(i) for i in range(count)])
        logger.info(f"All {count} drones have completed")
        
        return drone_responses

    def _format_for_arbiter(self, original_prompt: str, drone_responses: List[str]) -> str:
        """Prepare the prompt for the Arbiter."""
        drone_outputs = []
        for i, response in enumerate(drone_responses):
            drone_outputs.append({
                "id": i + 1,
                "content": response
            })

        context = {
            "original_prompt": original_prompt,
            "drones": drone_outputs
        }
        
        return render_template("hivemind_arbiter.jinja", context)

    async def _call_arbiter(
        self,
        prompt: str,
        arbiter_callback: Optional[Any] = None,
        **llm_kwargs: Any
    ) -> str:
        """Call the Arbiter model."""
        # Arbiter should use a lower temperature for synthesis
        arbiter_kwargs = llm_kwargs.copy()
        arbiter_kwargs["temperature"] = 0.2 # Low temp for precise synthesis
        
        # Remove default streaming_handler if present
        if "streaming_handler" in arbiter_kwargs:
            del arbiter_kwargs["streaming_handler"]
        
        if arbiter_callback:
            # Stream arbiter response
            logger.debug("Arbiter: Streaming enabled")
            response = await self.llm_client.generate_completion_streaming(
                prompt,
                callback=arbiter_callback.on_token_async,
                **arbiter_kwargs
            )
            # Notify completion
            await arbiter_callback.on_completion_async(response)
            return response
        else:
            # No callback, just return full response
            logger.debug("Arbiter: No streaming")
            return await self.llm_client.generate_completion(prompt, **arbiter_kwargs)
