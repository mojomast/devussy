"""Project design generator pipeline stage."""

from __future__ import annotations

from typing import Any, List, Optional
import asyncio

from ..llm_client import LLMClient
from ..logger import get_logger
from ..models import ProjectDesign
from ..templates import render_template

logger = get_logger(__name__)


class ProjectDesignGenerator:
    """Generate a structured project design document using an LLM."""

    def __init__(self, llm_client: LLMClient):
        """Initialize the generator with an LLM client.

        Args:
            llm_client: The LLM client instance to use for generation.
        """
        self.llm_client = llm_client

    async def generate(
        self,
        project_name: str,
        languages: List[str],
        requirements: str,
        frameworks: Optional[List[str]] = None,
        apis: Optional[List[str]] = None,
        **llm_kwargs: Any,
    ) -> ProjectDesign:
        """Generate a project design from user inputs.

        Args:
            project_name: Name of the project
            languages: List of programming languages to use
            requirements: Additional project requirements and description
            frameworks: Optional list of frameworks to use
            apis: Optional list of external APIs/services
            **llm_kwargs: Additional kwargs to pass to the LLM client

        Returns:
            Structured ProjectDesign model
        """
        logger.info(f"Generating project design for: {project_name}")

        # Prepare template context
        context = {
            "project_name": project_name,
            "languages": languages,
            "frameworks": frameworks or [],
            "apis": apis or [],
            "requirements": requirements,
        }

        # Render the prompt template
        prompt = render_template("project_design.jinja", context)
        logger.debug(f"Rendered prompt: {prompt[:200]}...")
        logger.info(f"Full prompt length: {len(prompt)} characters")
        logger.debug(f"Full prompt:\n{prompt}")

        # Optional streaming handler for console output
        streaming_handler = llm_kwargs.pop("streaming_handler", None)

        # Call the LLM
        streaming_enabled = hasattr(self.llm_client, "streaming_enabled") and getattr(
            self.llm_client, "streaming_enabled", False
        )
        print(f"DEBUG: Generator streaming_enabled={streaming_enabled}, handler_present={streaming_handler is not None}")

        if streaming_enabled and streaming_handler is not None:
            print("DEBUG: Entering streaming block")
            # Use streaming with console/token handler
            async with streaming_handler:
                response_chunks: list[str] = []

                async def token_callback(token: str) -> None:
                    """Async callback invoked by LLM client for each streamed chunk."""
                    # print(f"DEBUG: Token received: {token[:10]}...") 
                    response_chunks.append(token)
                    # Await the handler to ensure backpressure and completion
                    await streaming_handler.on_token_async(token)

                full_response = await self.llm_client.generate_completion_streaming(
                    prompt,
                    callback=token_callback,
                    **llm_kwargs,
                )

                await streaming_handler.on_completion_async(full_response)

            response = full_response

        elif streaming_enabled:
            # Use streaming without external handler
            response = ""

            def token_callback(token: str) -> None:
                nonlocal response
                response += token

            response = await self.llm_client.generate_completion_streaming(
                prompt, callback=token_callback, **llm_kwargs
            )
        else:
            # Use non-streaming for backwards compatibility
            response = await self.llm_client.generate_completion(prompt, **llm_kwargs)
            
        logger.info(f"Received LLM response ({len(response)} chars)")
        
        # DEBUG: Log response preview
        if response:
            logger.debug(f"Response preview: {response[:500]}...")
        else:
            logger.error("CRITICAL: LLM returned empty response!")
            logger.error(f"Prompt was: {prompt[:200]}...")

        # Parse the response into a ProjectDesign model
        design = self._parse_response(response, project_name)
        
        # Store the raw LLM response for full documentation
        design.raw_llm_response = response
        
        logger.info("Successfully parsed project design")

        return design

    def _parse_response(self, response: str, project_name: str) -> ProjectDesign:
        """Parse the LLM response into a structured ProjectDesign.

        Args:
            response: The raw markdown response from the LLM
            project_name: The project name

        Returns:
            Parsed ProjectDesign model
        """
        # Initialize lists
        objectives = []
        tech_stack = []
        dependencies = []
        challenges = []
        mitigations = []
        architecture_overview = None

        # Split response into lines for parsing
        lines = response.split("\n")
        current_section = None

        for line in lines:
            stripped = line.strip()

            # Detect section headers
            if "objective" in stripped.lower() and stripped.startswith("#"):
                current_section = "objectives"
                continue
            elif "technology stack" in stripped.lower() and stripped.startswith("#"):
                current_section = "tech_stack"
                continue
            elif "architecture" in stripped.lower() and stripped.startswith("#"):
                current_section = "architecture"
                architecture_lines = []
                continue
            elif "dependencies" in stripped.lower() and stripped.startswith("#"):
                current_section = "dependencies"
                continue
            elif "challenge" in stripped.lower() and stripped.startswith("#"):
                current_section = "challenges"
                continue
            elif "complexity" in stripped.lower() and stripped.startswith("#"):
                current_section = "complexity"
                continue
            elif stripped.startswith("#"):
                # Unknown section, skip
                current_section = None
                continue

            # Extract bullet points based on current section
            if current_section and stripped.startswith("-"):
                content = stripped[1:].strip()
                if content:
                    if current_section == "objectives":
                        objectives.append(content)
                    elif current_section == "tech_stack":
                        tech_stack.append(content)
                    elif current_section == "dependencies":
                        dependencies.append(content)
                    elif current_section == "challenges":
                        # Try to differentiate challenges from mitigations
                        if any(
                            kw in content.lower()
                            for kw in ["mitigation", "solution", "address"]
                        ):
                            mitigations.append(content)
                        else:
                            challenges.append(content)
                    elif current_section == "complexity":
                        # Parse complexity fields
                        lower_content = content.lower()
                        if "complexity rating" in lower_content:
                            parts = content.split(":", 1)
                            if len(parts) > 1:
                                complexity = parts[1].strip()
                        elif "estimated phases" in lower_content:
                            parts = content.split(":", 1)
                            if len(parts) > 1:
                                # Extract number from string like "4-6" or "5"
                                val_str = parts[1].strip()
                                # Try to find the first number
                                import re
                                num_match = re.search(r'\d+', val_str)
                                if num_match:
                                    estimated_phases = int(num_match.group(0))

            elif current_section == "architecture" and stripped:
                if not stripped.startswith("#"):
                    architecture_lines.append(stripped)

        # Join architecture lines
        if "architecture_lines" in locals():
            architecture_overview = "\n".join(architecture_lines)

        # If we got a response but failed to parse sections, use the full response
        if not architecture_overview and response:
            logger.warning("Failed to parse structured sections, using full response as architecture overview")
            architecture_overview = response
        elif not response:
            logger.error("CRITICAL: Empty response from LLM, cannot generate project design")
            architecture_overview = """ERROR: LLM returned empty response. Please check:
1. API key configuration
2. Network connectivity
3. Model availability
4. API endpoint status"""
        
        return ProjectDesign(
            project_name=project_name,
            objectives=objectives if objectives else ["No objectives parsed"],
            tech_stack=tech_stack if tech_stack else ["No tech stack parsed"],
            architecture_overview=architecture_overview,
            dependencies=dependencies if dependencies else [],
            challenges=challenges if challenges else [],
            mitigations=mitigations if mitigations else [],
            complexity=locals().get("complexity"),
            estimated_phases=locals().get("estimated_phases"),
        )
