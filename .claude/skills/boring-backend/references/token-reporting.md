# Token Reporting

When telemetry exists, report `total_tokens`, `input_tokens`, `cached_input_tokens`, `cache_write_tokens` when available, `noncached_input_tokens = input - cached`, `output_tokens`, and `reasoning_output_tokens`.

Cache writes are already input; do not add them to totals.
