"""Unit tests for the Autonomous SPM Agent."""

from __future__ import annotations

import pytest
from core.ai.autonomous_spm_agent import AutonomousSPMAgent, SampleSpecification


def test_extract_sample_height():
    agent = AutonomousSPMAgent()
    
    # Test natural language patterns
    assert agent._extract_sample_height("I have a sample on the surface the height is 2.5mm") == 2.5
    assert agent._extract_sample_height("sample height is 1.8mm") == 1.8
    assert agent._extract_sample_height("The sample thickness is 0.75 mm") == 0.75
    assert agent._extract_sample_height("height 3.2 mm") == 3.2
    assert agent._extract_sample_height("sample 5mm height") == 5.0
    assert agent._extract_sample_height("random text without height") is None


def test_sample_specification_calibrations():
    spec = SampleSpecification(height_mm=2.0, width_mm=10.0, length_mm=10.0)
    assert spec.height_mm == 2.0
    assert spec.target_z == 2.15
    assert spec.safe_approach_z == 3.5
    assert spec.safe_z_floor == 1.8
    assert spec.clearance_setpoint == 0.5


def test_interpret_sample_command_generates_workflow_plan():
    agent = AutonomousSPMAgent()
    resp = agent.interpret_user_command("I have a sample on the surface the height is 1.5mm and scan 10x10mm")
    
    assert resp.intent == "configure_sample"
    assert resp.sample_spec is not None
    assert resp.sample_spec.height_mm == 1.5
    assert resp.sample_spec.width_mm == 10.0
    assert resp.sample_spec.length_mm == 10.0
    assert len(resp.plan) == 6
    assert resp.plan[0].action_type == "connect"
    assert resp.plan[1].action_type == "configure_params"
    assert resp.plan[2].action_type == "authorize"
    assert resp.plan[3].action_type == "approach"
    assert resp.plan[4].action_type == "scan"
    assert resp.plan[5].action_type == "analyze"
    assert "target_z_mm" in resp.applied_settings


def test_interpret_auto_connect_command():
    agent = AutonomousSPMAgent()
    resp = agent.interpret_user_command("find the right port and connect to device")
    assert resp.intent == "auto_connect"
    assert "Port" in resp.natural_response


def test_interpret_self_correction_command():
    agent = AutonomousSPMAgent()
    resp = agent.interpret_user_command("self correct the connection error and troubleshoot")
    assert resp.intent == "self_correct"
    assert resp.self_correction_applied is True
    assert "Self-Correction" in resp.natural_response


def test_interpret_surface_analysis_command():
    agent = AutonomousSPMAgent()
    resp = agent.interpret_user_command("analyze the image and calculate ISO 25178 surface roughness")
    assert resp.intent == "surface_analysis"
    assert resp.metrology_results is not None
    assert "Sa_um" in resp.metrology_results
    assert "Sq_um" in resp.metrology_results
    assert "Sz_um" in resp.metrology_results


def test_execute_plan_step_offline():
    agent = AutonomousSPMAgent(workstation=None)
    resp = agent.interpret_user_command("sample height 2.0mm")
    step = resp.plan[0]
    success = agent.execute_plan_step(step)
    assert success is True
    assert step.status == "completed"
