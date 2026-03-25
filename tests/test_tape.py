from tmviz.domain.tape import Tape


def test_tape_reads_blank_and_erases_when_writing_blank() -> None:
    tape = Tape.from_symbols(["1", "_", "0"], blank_symbol="_")

    assert tape.read(0) == "1"
    assert tape.read(1) == "_"
    assert tape.read(5) == "_"

    tape.write(0, "_")
    assert tape.read(0) == "_"
    assert 0 not in tape.cells


def test_tape_snapshot_includes_sparse_cells() -> None:
    tape = Tape(blank_symbol="_", cells={-2: "1", 3: "0"})

    assert tape.snapshot(-2, 3) == [
        (-2, "1"),
        (-1, "_"),
        (0, "_"),
        (1, "_"),
        (2, "_"),
        (3, "0"),
    ]

