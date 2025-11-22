import json
import os
from pathlib import Path
from datetime import datetime

# Mock data structures based on analysis
def generate_samples():
    output_dir = Path("DevDocs/JINJA_DATA_SAMPLES")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Project Design Context
    project_design = {
        "project_name": "SuperApp",
        "languages": ["Python", "TypeScript"],
        "frameworks": ["FastAPI", "React"],
        "apis": ["OpenAI", "Stripe"],
        "requirements": "Build a scalable web app.",
        "objectives": ["High performance", "User friendly"],
        "tech_stack": ["Python 3.11", "React 18", "PostgreSQL"],
        "architecture_overview": "Microservices architecture...",
        "dependencies": ["sqlalchemy", "pydantic"],
        "challenges": ["Concurrency", "Data consistency"],
        "mitigations": ["Use async/await", "Use transactions"],
        "complexity": "Medium",
        "estimated_phases": 5
    }
    
    with open(output_dir / "project_design.jinja.json", "w") as f:
        json.dump(project_design, f, indent=2)

    # 2. Basic DevPlan Context
    repo_context = {
        "project_type": "python",
        "structure": {
            "source_dirs": ["src"],
            "test_dirs": ["tests"],
            "config_dirs": ["config"],
            "has_ci": True
        },
        "dependencies": {
            "python": ["fastapi", "uvicorn"]
        },
        "metrics": {
            "total_files": 42,
            "total_lines": 1337
        },
        "patterns": {
            "test_frameworks": ["pytest"],
            "build_tools": ["poetry"]
        },
        "project_name": "ExistingApp",
        "description": "An existing app",
        "version": "1.0.0",
        "author": "Dev"
    }

    basic_devplan_context = {
        "repo_context": repo_context,
        "project_design": project_design,
        "code_samples": "def hello(): pass",
        "interactive_session": {"question_count": 5}
    }

    with open(output_dir / "basic_devplan.jinja.json", "w") as f:
        json.dump(basic_devplan_context, f, indent=2)

    # 3. Detailed DevPlan Context
    detailed_devplan_context = {
        "repo_context": repo_context,
        "phase_number": 1,
        "phase_title": "Setup",
        "phase_description": "Initialize the project.",
        "project_name": "SuperApp",
        "tech_stack": ["Python", "Git"],
        "code_samples": "print('hello')"
    }

    with open(output_dir / "detailed_devplan.jinja.json", "w") as f:
        json.dump(detailed_devplan_context, f, indent=2)

    # 4. Design Review Context
    design_review_context = {
        "project_design": project_design
    }

    with open(output_dir / "design_review.jinja.json", "w") as f:
        json.dump(design_review_context, f, indent=2)

    # 5. Handoff Prompt Context
    handoff_context = {
        "project_name": "SuperApp",
        "repo_context": repo_context,
        "current_phase_number": 2,
        "current_phase_name": "Core Logic",
        "next_task_id": "2.1",
        "next_task_description": "Implement auth",
        "blockers": "None"
    }

    with open(output_dir / "handoff_prompt.jinja.json", "w") as f:
        json.dump(handoff_context, f, indent=2)

    # 6. Hivemind Arbiter Context
    hivemind_context = {
        "original_prompt": "Design a system...",
        "drones": [
            {"id": "A", "content": "Proposal A..."},
            {"id": "B", "content": "Proposal B..."}
        ]
    }

    with open(output_dir / "hivemind_arbiter.jinja.json", "w") as f:
        json.dump(hivemind_context, f, indent=2)

    # 7. Interactive Session Report
    session_context = {
        "session": {
            "project_name": "SuperApp",
            "session_id": "sess_123",
            "created_at": "2023-01-01",
            "last_updated": "2023-01-01",
            "answers": {
                "project_name": "SuperApp",
                "project_type": "Web App",
                "primary_language": "Python",
                "requirements": "Fast"
            }
        }
    }

    with open(output_dir / "interactive_session_report.jinja.json", "w") as f:
        json.dump(session_context, f, indent=2)

    # 8. Docs DevPlan Report
    devplan_report_context = {
        "timestamp": "2023-01-01",
        "devplan": {
            "project_name": "SuperApp",
            "estimated_duration": "2 weeks",
            "project_summary": "A great app.",
            "phases": [
                {
                    "number": 1,
                    "name": "Setup",
                    "completed": True,
                    "description": "Setup phase",
                    "steps": [
                        {
                            "number": "1.1",
                            "title": "Init Git",
                            "completed": True,
                            "description": "Run git init",
                            "deliverables": [".git"],
                            "commit_message": "Initial commit"
                        }
                    ],
                    "completed_steps": 1
                }
            ],
            "current_phase": {"number": 2, "name": "Core"},
            "next_task": "Implement login",
            "milestones": [],
            "external_dependencies": [],
            "internal_dependencies": [],
            "success_criteria": ["It works"]
        }
    }

    with open(output_dir / "docs_devplan_report.jinja.json", "w") as f:
        json.dump(devplan_report_context, f, indent=2)

    print("Samples generated.")

if __name__ == "__main__":
    generate_samples()
