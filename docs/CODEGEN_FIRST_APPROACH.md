# Codegen-First Vision Analysis Architecture

**Created**: 2025-01-27  
**Status**: Active Design

## Overview

This document explains the **codegen-first** architecture for vision-assisted fusion data analysis, where vision models write and execute Python code rather than calling predefined tools.

## Core Principle

**Vision Model = Data Scientist**

Instead of limiting vision models to predefined tool functions, we give them:
1. **Code generation capability**: Write arbitrary Python for analysis
2. **Sandbox execution environment**: Run code with IMAS access
3. **Iterative refinement**: Revise code based on results/errors
4. **Result integration**: Use numerical outputs in final descriptions

## Architecture Comparison

### Tool-Based Approach (Discarded)

```
Vision Model → Calls predefined functions
                 ├── get_exact_value(quantity, time)
                 ├── get_phase_metrics(phase)
                 ├── get_stability_analysis()
                 └── get_gradient(quantity, location)
                       ↓
                 Limited to anticipated queries
```

**Limitations**:
- Must anticipate all possible analyses
- Rigid API maintenance burden
- Can't adapt to unexpected data structures
- No flexibility for novel analysis approaches

### Codegen-First Approach (Current)

```
Vision Model → Generates Python code
                 ↓
            Execute in sandbox (imas, numpy, pandas, xarray, scipy)
                 ↓
            Return JSON results
                 ↓
            Vision integrates into description
```

**Advantages**:
- Unlimited analysis flexibility
- Vision model invents new analyses as needed
- Self-documenting (code shows methodology)
- Reproducible (store code with results)
- Iterative (refine based on execution results)
- No API to maintain

## Example Workflow

### 1. Vision Model Sees Plot

```python
# System provides plot and context
await vision_analyze(
    image=plasma_current_plot,
    imas_uri="imas://uda.iter.org/...",
    prompt="Analyze this plasma current waveform"
)
```

### 2. Vision Model Writes Code

```python
# Vision model generates:
"""
import imas
import imas.util
import numpy as np

# Load equilibrium data
entry = imas.DBEntry(imas_uri, 'r')
eq = entry.get('equilibrium')
ip_ds = imas.util.to_xarray(eq, 'time_slice/global_quantities/ip')

# Extract arrays
ip = ip_ds['time_slice.global_quantities.ip'].values / 1e6  # MA
time = ip_ds.coords['time'].values

# Detect phases via gradient
dip_dt = np.gradient(ip, time)
rampup = (dip_dt > 0.01) & (abs(ip) < 14)
flattop = (abs(dip_dt) < 0.005) & (abs(ip) > 14)
rampdown = dip_dt < -0.01

# Calculate metrics
return {
    'peak_ip_MA': float(abs(ip).max()),
    'peak_time_s': float(time[abs(ip).argmax()]),
    'rampup_duration_s': float((time[rampup][-1] - time[rampup][0]) if rampup.any() else 0),
    'flattop_duration_s': float((time[flattop][-1] - time[flattop][0]) if flattop.any() else 0),
    'flattop_stability_MA': float(abs(ip[flattop]).std() if flattop.any() else 0),
    'rampdown_duration_s': float((time[rampdown][-1] - time[rampdown][0]) if rampdown.any() else 0),
}
"""
```

### 3. Code Executes in Sandbox

```python
# Sandbox validates and executes
result = await execute_code(
    code=generated_code,
    context={'imas_uri': uri, 'simulation_uuid': uuid},
    timeout=30,
    memory_limit=2_000_000_000
)

# Returns:
{
    'success': True,
    'output': {
        'peak_ip_MA': 15.02,
        'peak_time_s': 580.9,
        'rampup_duration_s': 78.7,
        'flattop_duration_s': 655.0,
        'flattop_stability_MA': 0.03,
        'rampdown_duration_s': 63.1
    },
    'execution_time': 2.3
}
```

### 4. Vision Model Generates Description

```python
# Vision model combines visual observations with code results:
"""
This waveform demonstrates exceptional control of the ITER baseline scenario
over an extended 797s pulse with three well-defined phases:

**Ramp-up Phase (0-79s)**: Rapid current rise from near-zero to 15.02 MA over
79 seconds. The smooth ascent without visible oscillations indicates efficient
plasma formation and current drive.

**Flat-top Phase (79-734s)**: Outstanding stability maintained at 15.00 ± 0.03 MA
for 655 seconds. This represents 82% of the total pulse duration and demonstrates
the robustness of the DINA-JINTRAC integrated modeling. The extremely low
variance (σ = 0.03 MA, or 0.2%) indicates excellent poloidal field coil control.

**Ramp-down Phase (734-797s)**: Controlled termination over 63 seconds with
symmetric descent. The managed ramp-down suggests careful plasma shape evolution.

This scenario achieves Q = 9.55 fusion performance with 515 MW fusion power.
"""
```

## Sandbox Architecture

### Security Boundaries

**Allowed**:
- Read-only IMAS access (`DBEntry(uri, 'r')`)
- Numerical libraries: `numpy`, `scipy`, `pandas`, `xarray`
- Matplotlib (output serialization only)
- Temporary file writes for processing

**Forbidden**:
- File system writes (except temp)
- Network access
- Subprocess execution
- `eval()`, `exec()` outside sandbox
- Write-mode IMAS access

### Resource Limits

```python
SANDBOX_LIMITS = {
    'timeout': 30,  # seconds
    'memory': 2_000_000_000,  # 2GB
    'max_iterations': 3,  # Code refinement attempts
}
```

### Code Validation

Before execution:
1. **AST parsing**: Check syntax and forbidden operations
2. **Import whitelist**: Only allowed modules
3. **Return type check**: Must return JSON-compatible dict
4. **URI validation**: IMAS URIs pre-verified for read access

### Multi-Turn Iteration

```python
# Iteration 1: Initial attempt
code_v1 = vision_model.generate_code()
result_v1 = execute_code(code_v1)

if result_v1['error']:
    # Iteration 2: Vision sees error, corrects
    code_v2 = vision_model.refine_code(
        previous_code=code_v1,
        error=result_v1['error'],
        traceback=result_v1['traceback']
    )
    result_v2 = execute_code(code_v2)
    
    if result_v2['error'] and max_iterations > 2:
        # Iteration 3: Final attempt
        code_v3 = vision_model.refine_code(...)
        result_v3 = execute_code(code_v3)

# Use best successful result for description
```

## Benefits Over Tool-Based Approach

### 1. Unlimited Flexibility

**Tool-based**: "Sorry, I can only calculate these 12 metrics"  
**Codegen**: "Let me write code to calculate exactly what's needed"

### 2. Novel Analysis

**Tool-based**: Can't perform analyses not anticipated during API design  
**Codegen**: Vision model can invent new analysis methods on-the-fly

### 3. Adaptability

**Tool-based**: Breaks when data structure changes  
**Codegen**: Vision model adapts code to actual structure

### 4. Self-Documentation

**Tool-based**: Results without methodology  
**Codegen**: Code explicitly shows how results were derived

### 5. Reproducibility

**Tool-based**: Must trust tool implementation  
**Codegen**: Stored code can be re-executed for validation

### 6. No API Maintenance

**Tool-based**: Every new analysis needs new tool function  
**Codegen**: Just update prompt template guidance

## Implementation Status

### Completed
- [x] Strategy document created (`VISION_FIRST_STRATEGY.md`)
- [x] Implementation plan updated (`VISION_IMPLEMENTATION_PLAN.md`)
- [x] Codegen architecture defined (this document)
- [x] Removed tool-based stub files

### In Progress
- [ ] Sandbox implementation (`nucleai/vision/sandbox.py`)
- [ ] Vision analyzer with code generation (`nucleai/vision/analyzer.py`)
- [ ] Code generation prompts (`nucleai/vision/prompts.py`)

### Next Steps
1. Implement sandbox with AST validation and resource limits
2. Integrate OpenRouter vision API for code generation
3. Create prompt templates for different plot types
4. Test end-to-end with DINA-JINTRAC simulation
5. Validate code correctness and numerical accuracy

## Cost Analysis

**Per simulation** (one-time processing):
- Vision API (Gemini 2.0 Flash): ~$0.02
  - 1024×768 image input
  - ~500 token code generation
  - ~500 token description
- Code execution: $0.00 (local)

**Full corpus** (1300 simulations):
- Total: ~$26
- Processing time: ~2-3 hours (5 concurrent)

## Success Metrics

1. **Code Execution Success Rate**: >95% on first attempt
2. **Numerical Accuracy**: Code results match ground truth within 1%
3. **Description Quality**: Expert-validated technical accuracy
4. **Processing Cost**: <$0.05 per simulation
5. **Reproducibility**: Stored code re-executes successfully

## Risks and Mitigations

### Risk: Code Hallucination
**Impact**: Vision model generates syntactically correct but semantically wrong code  
**Mitigation**: 
- AST validation catches syntax errors
- Execution errors trigger iteration
- Store all code for human audit
- Compare results across similar simulations for outliers

### Risk: Sandbox Escape
**Impact**: Malicious or buggy code accesses unauthorized resources  
**Mitigation**:
- Comprehensive AST checking
- Read-only IMAS access
- No network access
- Resource limits prevent DoS
- Isolated execution namespace

### Risk: Performance
**Impact**: Code execution adds latency  
**Mitigation**:
- 30s timeout limits worst case
- Most analyses complete in <5s
- Parallel processing for batch jobs
- Cache numerical results in database

## Conclusion

The codegen-first approach treats vision models as **data scientists** rather than **image classifiers**. This architectural choice:

- Eliminates API maintenance burden
- Enables unlimited analysis flexibility
- Provides self-documenting, reproducible results
- Maintains security through sandbox constraints
- Scales to entire SimDB corpus at low cost (~$26)

By letting vision models write code, we unlock their full potential as analytical agents that can adapt to any fusion data analysis task.
