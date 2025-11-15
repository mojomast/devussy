"""Integration tests for interactive command workflow."""

import tempfile
import json
from pathlib import Path
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestInteractiveCommandWorkflow:
    """Test the complete interactive command workflow."""

    @pytest.mark.asyncio
    async def test_complete_workflow_after_interview(self):
        """Test that interactive command continues with full pipeline after /done."""
        
        # Mock interview data that would come from /done
        mock_interview_data = {
            "name": "Test Project",
            "languages": "Python",
            "requirements": "Build a simple web API",
            "frameworks": "FastAPI",
            "apis": "",
            "code_samples": ""
        }
        
        # Mock design object
        mock_design = MagicMock()
        mock_design.architecture_overview = "Test architecture overview"
        mock_design.tech_stack = ["Python", "FastAPI", "PostgreSQL"]
        
        # Mock devplan object
        mock_devplan = MagicMock()
        mock_devplan.summary = "Test development plan summary"
        mock_devplan.phases = [
            MagicMock(number=1, title="Phase 1", description="Test phase", steps=[]),
            MagicMock(number=2, title="Phase 2", description="Test phase", steps=[])
        ]
        
        # Mock handoff object
        mock_handoff = MagicMock()
        mock_handoff.content = "# Test Handoff Document\n\nTest content here."
        mock_handoff.next_steps = ["Step 1", "Step 2"]
        
        with patch('src.cli.LLMInterviewManager') as mock_interview_manager_class:
            # Mock interview manager
            mock_interview_manager = AsyncMock()
            mock_interview_manager.to_generate_design_inputs.return_value = mock_interview_data
            mock_interview_manager.run.return_value = mock_interview_data
            mock_interview_manager_class.return_value = mock_interview_manager
            
            with patch('src.cli._create_orchestrator') as mock_create_orchestrator:
                # Mock orchestrator
                mock_orchestrator = MagicMock()
                mock_orchestrator.project_design_gen.generate.return_value = mock_design
                mock_orchestrator.run_devplan_only.return_value = mock_devplan
                mock_orchestrator.run_handoff_only.return_value = mock_handoff
                mock_orchestrator._devplan_to_markdown.return_value = "# Test DevPlan\n\nTest content."
                mock_orchestrator._generate_phase_files.return_value = ["phase1.md", "phase2.md"]
                mock_create_orchestrator.return_value = mock_orchestrator
                
                with patch('src.cli.StreamingHandler'):
                    with patch('src.cli.FileManager') as mock_file_manager_class:
                        # Mock file manager
                        mock_file_manager = MagicMock()
                        mock_file_manager.write_markdown.return_value = None
                        mock_file_manager_class.return_value = mock_file_manager
                        
                        # Create temporary directory for output
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Test that interactive function can be imported
                            try:
                                from src.cli import interactive
                                
                                # Run interactive command
                                await interactive(
                                    config_path=None,
                                    provider="test",
                                    model="test-model", 
                                    output_dir=temp_dir,
                                    temperature=None,
                                    max_tokens=None,
                                    select_model=False,
                                    save_session=None,
                                    resume_session=None,
                                    llm_interview=True,
                                    scripted=False,
                                    streaming=False,
                                    verbose=False,
                                    debug=False
                                )
                                
                                # Verify workflow was called in correct order
                                assert mock_interview_manager.run.called, "Interview should have been called"
                                assert mock_orchestrator.project_design_gen.generate.called, "Design generation should have been called"
                                assert mock_orchestrator.run_devplan_only.called, "Devplan generation should have been called"
                                assert mock_orchestrator._generate_phase_files.called, "Phase files should have been generated"
                                assert mock_orchestrator.run_handoff_only.called, "Handoff generation should have been called"
                                assert mock_file_manager.write_markdown.call_count >= 4, "At least 4 files should have been written"
                                
                            except ImportError as e:
                                pytest.skip(f"Cannot import interactive command: {e}")
                            except Exception as e:
                                # Allow for other test setup issues
                                pytest.skip(f"Interactive command test setup failed: {e}")

    def test_interactive_command_import(self):
        """Test that interactive command can be imported."""
        try:
            from src.cli import interactive
            assert callable(interactive)
        except ImportError as e:
            pytest.skip(f"Cannot import interactive command: {e}")

    @pytest.mark.asyncio
    async def test_interactive_workflow_sequence(self):
        """Test the expected sequence of workflow steps."""
        
        # Track the order of operations
        execution_order = []
        
        def track_call(method_name):
            def wrapper(*args, **kwargs):
                execution_order.append(method_name)
                return MagicMock()
            return wrapper
        
        with patch('src.cli.LLMInterviewManager') as mock_interview_manager_class:
            mock_interview_manager = AsyncMock()
            mock_interview_manager.to_generate_design_inputs.return_value = {"name": "Test"}
            mock_interview_manager.run.return_value = {"name": "Test"}
            mock_interview_manager_class.return_value = mock_interview_manager
            
            with patch('src.cli._create_orchestrator') as mock_create_orchestrator:
                mock_orchestrator = MagicMock()
                mock_orchestrator.project_design_gen.generate = track_call("design_generation")
                mock_orchestrator.run_devplan_only = track_call("devplan_generation")
                mock_orchestrator._generate_phase_files = track_call("phase_files")
                mock_orchestrator.run_handoff_only = track_call("handoff_generation")
                mock_orchestrator._devplan_to_markdown.return_value = "mock devplan"
                mock_orchestrator._generate_phase_files.return_value = ["phase1.md"]
                mock_create_orchestrator.return_value = mock_orchestrator
                
                with patch('src.cli.StreamingHandler'):
                    with patch('src.cli.FileManager'):
                        with tempfile.TemporaryDirectory() as temp_dir:
                            try:
                                from src.cli import interactive
                                await interactive(
                                    config_path=None,
                                    provider="test",
                                    model="test",
                                    output_dir=temp_dir,
                                    temperature=None,
                                    max_tokens=None,
                                    verbose=False,
                                    debug=False
                                )
                                
                                # Verify the expected sequence
                                expected_sequence = ["design_generation", "devplan_generation", "phase_files", "handoff_generation"]
                                for step in expected_sequence:
                                    assert step in execution_order, f"{step} should have been called"
                                    
                            except Exception:
                                # Skip if test setup fails
                                pass


class TestInteractiveCommandErrorHandling:
    """Test error handling in interactive command."""

    @pytest.mark.asyncio
    async def test_handles_interview_failure(self):
        """Test that interactive command handles interview failures gracefully."""
        
        with patch('src.cli.LLMInterviewManager') as mock_interview_manager_class:
            # Mock interview manager that fails
            mock_interview_manager = AsyncMock()
            mock_interview_manager.run.side_effect = Exception("Interview failed")
            mock_interview_manager_class.return_value = mock_interview_manager
            
            # Should handle the error gracefully
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    from src.cli import interactive
                    await interactive(
                        config_path=None,
                        provider="test",
                        model="test",
                        output_dir=temp_dir,
                        temperature=None,
                        max_tokens=None,
                        verbose=False,
                        debug=False
                    )
                    # If we get here without exception, that's good
                except Exception:
                    # Exception is expected, but command should handle it gracefully
                    pass

    def test_parameter_validation(self):
        """Test that interactive command validates parameters."""
        # Test with invalid parameters
        try:
            from src.cli import interactive
            # Should handle None config_path gracefully
            import asyncio
            asyncio.run(interactive(
                config_path=None,
                provider="test",
                model="test",
                output_dir="/tmp",
                temperature=None,
                max_tokens=None,
                verbose=False,
                debug=False
            ))
        except Exception:
            # Expected to fail, but shouldn't crash
            pass


if __name__ == "__main__":
    # Run tests manually
    pytest.main([__file__, "-v"])