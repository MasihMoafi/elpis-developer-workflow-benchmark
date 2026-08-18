# Calculator fixture

`apply_discount(cents, percentage)` accepts integer cents, rejects percentages
outside 0..100 with ValueError, applies a discount rather than a surcharge,
and truncates fractional cents down. Run `python -m unittest discover -s tests -v`.

