# Local GPU Acceleration for LightGBM and CUDA Fallbacks

## Overview
LightGBM supports OpenCL and CUDA device acceleration for histogram binning and tree building.
For large tabular datasets ($N > 100,000$ rows, $P > 100$ features), GPU acceleration achieves up to
4-8x faster training cycles compared to CPU-only execution.

## GPU Detection and Configuration

Athena's `train_model` tool dynamically inspects system hardware availability:

```python
def get_lgbm_device_params() -> dict:
    try:
        import torch
        if torch.cuda.is_available():
            return {"device_type": "cuda"}
    except ImportError:
        pass
    return {"device_type": "cpu"}
```

## Automatic Fallback Handling
If CUDA drivers are misconfigured or GPU out-of-memory errors occur, Athena catches `LightGBMError`
and falls back to CPU multi-threading (`n_jobs=4`) without terminating the user's analytical run.
The fallback is recorded as a warning in the tool result payload.
