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

def test_agent_config_has_default_max_rejected_final_answers():
    config = AgentConfig()

    assert config.max_rejected_final_answers == 3


def test_agent_config_accepts_custom_max_rejected_final_answers():
    config = AgentConfig(max_rejected_final_answers=5)

    assert config.max_rejected_final_answers == 5


def test_agent_config_rejects_zero_max_rejected_final_answers():
    with pytest.raises(ValueError):
        AgentConfig(max_rejected_final_answers=0)


def test_agent_config_rejects_negative_max_rejected_final_answers():
    with pytest.raises(ValueError):
        AgentConfig(max_rejected_final_answers=-1)        

def test_agent_config_has_default_max_rejected_tool_calls():
    config = AgentConfig()

    assert config.max_rejected_tool_calls == 5


def test_agent_config_accepts_custom_max_rejected_tool_calls():
    config = AgentConfig(max_rejected_tool_calls=2)

    assert config.max_rejected_tool_calls == 2


def test_agent_config_rejects_zero_max_rejected_tool_calls():
    with pytest.raises(ValueError):
        AgentConfig(max_rejected_tool_calls=0)


def test_agent_config_rejects_negative_max_rejected_tool_calls():
    with pytest.raises(ValueError):
        AgentConfig(max_rejected_tool_calls=-1)        

def test_agent_config_has_default_max_invalid_llm_outputs():
    config = AgentConfig()

    assert config.max_invalid_llm_outputs == 3


def test_agent_config_accepts_custom_max_invalid_llm_outputs():
    config = AgentConfig(max_invalid_llm_outputs=2)

    assert config.max_invalid_llm_outputs == 2


def test_agent_config_rejects_zero_max_invalid_llm_outputs():
    with pytest.raises(ValueError):
        AgentConfig(max_invalid_llm_outputs=0)


def test_agent_config_rejects_negative_max_invalid_llm_outputs():
    with pytest.raises(ValueError):
        AgentConfig(max_invalid_llm_outputs=-1)        

def test_agent_config_can_be_serialized_to_dict():
    config = AgentConfig(
        max_steps=20,
        max_rejected_final_answers=2,
        max_rejected_tool_calls=4,
        max_invalid_llm_outputs=3,
    )

    assert config.to_dict() == {
        "max_steps": 20,
        "max_rejected_final_answers": 2,
        "max_rejected_tool_calls": 4,
        "max_invalid_llm_outputs": 3,
    }


def test_agent_config_can_be_restored_from_dict():
    config = AgentConfig.from_dict({
        "max_steps": 20,
        "max_rejected_final_answers": 2,
        "max_rejected_tool_calls": 4,
        "max_invalid_llm_outputs": 3,
    })

    assert config == AgentConfig(
        max_steps=20,
        max_rejected_final_answers=2,
        max_rejected_tool_calls=4,
        max_invalid_llm_outputs=3,
    )


def test_agent_config_round_trip():
    original = AgentConfig(
        max_steps=20,
        max_rejected_final_answers=2,
        max_rejected_tool_calls=4,
        max_invalid_llm_outputs=3,
    )

    restored = AgentConfig.from_dict(original.to_dict())

    assert restored == original


def test_agent_config_from_dict_rejects_non_dict_input():
    with pytest.raises(ValueError):
        AgentConfig.from_dict("not a dict")


def test_agent_config_from_dict_rejects_unknown_fields():
    with pytest.raises(ValueError):
        AgentConfig.from_dict({
            "max_steps": 20,
            "max_rejected_final_answers": 2,
            "max_rejected_tool_calls": 4,
            "max_invalid_llm_outputs": 3,
            "unexpected": "value",
        })


def test_agent_config_from_dict_rejects_missing_max_steps():
    with pytest.raises(ValueError):
        AgentConfig.from_dict({
            "max_rejected_final_answers": 2,
            "max_rejected_tool_calls": 4,
            "max_invalid_llm_outputs": 3,
        })


def test_agent_config_from_dict_rejects_missing_max_rejected_final_answers():
    with pytest.raises(ValueError):
        AgentConfig.from_dict({
            "max_steps": 20,
            "max_rejected_tool_calls": 4,
            "max_invalid_llm_outputs": 3,
        })


def test_agent_config_rejects_non_integer_values():
    with pytest.raises(ValueError):
        AgentConfig(max_steps="20")


def test_agent_config_rejects_bool_values():
    with pytest.raises(ValueError):
        AgentConfig(max_steps=True)        