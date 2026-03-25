# Machine Spec Reference

[Back to README](../README.md) | [User Guide](user-guide.md) | [Architecture Guide](architecture.md) | [Contributing Guide](contributing.md)

## Overview

Machine specs are JSON files loaded by `MachineSpecFactory`, normalized by the
validator layer, and then converted into a runtime `TuringMachine`.

Bundled examples live under `specs/`.

## Required Fields

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | Human-readable machine name shown in the UI |
| `blank_symbol` | string | The symbol used for unpopulated tape cells |
| `states` | array of strings | All valid control states |
| `start_state` | string | Initial control state |
| `accept_states` | array of strings | States that immediately halt with `accept` |
| `alphabet` | array of strings | Full symbol set, including the blank symbol |
| `initial_tape` | array of strings | Initial finite tape contents |
| `initial_head` | integer | Starting tape index for the head |
| `rules` | array of 5-item arrays | Transition table rows |

## Optional Fields

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `reject_states` | array of strings | `[]` | States that immediately halt with `reject` |
| `missing_rule_policy` | string | `"halt"` | Behavior when no rule matches the current `(state, symbol)` pair |

## Rule Tuple Format

Each rule is a 5-item array:

```text
[current_state, read_symbol, next_state, write_symbol, move_direction]
```

Example:

```json
["scan", "_", "carry", "_", "L"]
```

This means:

- if the machine is in state `scan`
- and reads symbol `_`
- then it enters state `carry`
- writes `_`
- and moves left

## Valid Move Directions

| Value | Meaning |
| --- | --- |
| `L` | Move head left |
| `R` | Move head right |
| `S` | Stay on the current tape index |

Any other direction raises a validation error during spec normalization.

## `missing_rule_policy`

The runtime behavior when no rule exists for the current `(state, symbol)` pair:

| Value | Effect |
| --- | --- |
| `halt` | Halt immediately with reason `no_rule` |
| `reject` | Halt with reason `reject` and move to the first reject state if one exists |
| `error` | Raise `RuleNotFoundError` |

## Validator-Enforced Constraints

The current validator enforces the following rules:

- required fields must exist
- string fields must be non-empty
- `states` must be unique
- `alphabet` must be unique
- `blank_symbol` must appear in `alphabet`
- `start_state` must exist in `states`
- `accept_states` must be a subset of `states`
- `reject_states` must be a subset of `states`
- `initial_tape` symbols must all be in `alphabet`
- `initial_head` must be an integer
- `missing_rule_policy` must be one of `halt`, `reject`, or `error`
- `rules` must be a sequence of 5-item rows
- rule states must exist in `states`
- rule symbols must exist in `alphabet`
- each `(current_state, read_symbol)` pair must be unique

## Worked Example: Unary Increment

```json
{
  "name": "Unary Increment",
  "blank_symbol": "_",
  "states": ["q0", "halt"],
  "start_state": "q0",
  "accept_states": ["halt"],
  "reject_states": [],
  "alphabet": ["1", "_"],
  "initial_tape": ["1", "1", "1", "_"],
  "initial_head": 0,
  "rules": [
    ["q0", "1", "q0", "1", "R"],
    ["q0", "_", "halt", "1", "S"]
  ]
}
```

Behavior:

- scan right across the unary marks
- stop at the first blank
- write one more `1`
- halt in the accept state

## Worked Example: Binary Increment

```json
{
  "name": "Binary Increment",
  "blank_symbol": "_",
  "states": ["scan", "carry", "halt"],
  "start_state": "scan",
  "accept_states": ["halt"],
  "reject_states": [],
  "alphabet": ["0", "1", "_"],
  "initial_tape": ["1", "0", "1", "1", "_"],
  "initial_head": 0,
  "rules": [
    ["scan", "0", "scan", "0", "R"],
    ["scan", "1", "scan", "1", "R"],
    ["scan", "_", "carry", "_", "L"],
    ["carry", "1", "carry", "0", "L"],
    ["carry", "0", "halt", "1", "S"],
    ["carry", "_", "halt", "1", "S"]
  ]
}
```

Behavior:

- scan to the end of the binary number
- move left into carry mode
- flip trailing `1` values to `0`
- write a `1` when a `0` or blank is found
- halt

## Common Validation Failures

Typical invalid specs include:

- missing `blank_symbol`
- duplicate states or alphabet entries
- using a symbol in `initial_tape` that is not in `alphabet`
- referencing an unknown state in a rule
- duplicate rules for the same `(state, symbol)` pair
- using a direction other than `L`, `R`, or `S`

## Authoring Advice

- Keep symbol choices simple and explicit.
- Include the blank symbol in the alphabet from the start.
- Use short state names if you want compact rule displays in the UI.
- Start with a tiny machine and add rules incrementally.
- Run the test suite after adding new bundled specs.

## Related Docs

- Use the simulator interactively with the [User Guide](user-guide.md).
- See controller, rendering, and event flow details in the [Architecture Guide](architecture.md).
- For setup and contribution workflow, see [Contributing Guide](contributing.md).

