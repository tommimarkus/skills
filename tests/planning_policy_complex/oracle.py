"""Immutable, requirement-derived oracle; execute outside the worker write set."""
import copy
import importlib
import sys
from pathlib import Path


def check(trial):
    sys.path.insert(0, str(Path(trial).resolve()))
    catalog, summary, render, export = [importlib.import_module(name) for name in ('catalog', 'summary', 'render', 'export')]
    records = [
        {'id': ' Zebra ', 'label': ' Two\t words ', 'amount': 2},
        {'id': 'APPLE', 'label': ' Red ', 'amount': 3},
        {'id': 'apricot', 'label': '', 'amount': 0},
        {'id': 'Straße', 'label': 'Unicode', 'amount': 5},
    ]
    snapshot = copy.deepcopy(records)
    expected = [
        {'id': 'zebra', 'label': 'Two words', 'amount': 2},
        {'id': 'apple', 'label': 'Red', 'amount': 3},
        {'id': 'apricot', 'label': '', 'amount': 0},
        {'id': 'strasse', 'label': 'Unicode', 'amount': 5},
    ]
    normalized = catalog.normalize(records)
    assert normalized == expected
    assert normalized is not records
    assert all(item is not original for item, original in zip(normalized, records))
    assert list(summary.totals(records).items()) == [('a', 3), ('s', 5), ('z', 2)]
    expected_rows = ['apple|Red|3', 'apricot||0', 'strasse|Unicode|5', 'zebra|Two words|2']
    assert render.rows(records) == expected_rows
    assert export.build(records) == {'totals': {'a': 3, 's': 5, 'z': 2}, 'rows': expected_rows}
    assert records == snapshot
    assert export.build([]) == {'totals': {}, 'rows': []}
    assert catalog.normalize([]) == []
    for function in (catalog.normalize, summary.totals, render.rows, export.build):
        for invalid, message in (
            ([{'id': ' ', 'label': '', 'amount': False}], 'empty id'),
            ([{'id': 'x', 'label': '', 'amount': True}], 'invalid amount'),
            ([{'id': 'x', 'label': '', 'amount': -1}], 'invalid amount'),
            ([{'id': 'x', 'label': '', 'amount': 1.0}], 'invalid amount'),
            ([{'id': 'Straße', 'label': '', 'amount': 1}, {'id': ' STRASSE ', 'label': '', 'amount': 2}], 'duplicate id'),
            ([{'id': 'x', 'label': '', 'amount': 1}, {'id': 'X', 'label': '', 'amount': False}], 'invalid amount'),
        ):
            before = copy.deepcopy(invalid)
            try:
                function(invalid)
            except ValueError as error:
                assert str(error) == message
            else:
                raise AssertionError('expected validation failure')
            assert invalid == before


if __name__ == '__main__':
    check(sys.argv[1])
