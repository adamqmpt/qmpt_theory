"""Configuration for QMPT pattern transfer test suite v1."""

N_RUNS = 10000

RUN_SEEDS = [42, 1337, 2025, 9001, 123456, 777, 888, 999, 1111, 2222]

ENV_CONFIG = {
    "size": 10,
    "max_steps": 50,
}

AGENT_CONFIG = {
    "internal_dim": 16,
    "self_model_dim": 8,
    "seed": None,  # set per run
}

COPY_HORIZON = 30
TRANSFER_HORIZON = 30
