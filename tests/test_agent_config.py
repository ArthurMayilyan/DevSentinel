import pytest

from agent_config import AgentConfig


def test_agent_config_has_default_max_steps():
    config = AgentConfig()

    assert config.max_steps == 8


def test_agent_config_accepts_custom_max_steps():
    config = AgentConfig(max_steps=20)

    assert config.max_steps == 20


def test_agent_config_rejects_zero_max_steps():
    with pytest.raises(ValueError):
        AgentConfig(max_steps=0)


def test_agent_config_rejects_negative_max_steps():
    with pytest.raises(ValueError):
        AgentConfig(max_steps=-1)