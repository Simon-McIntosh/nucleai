# Vision-First Multi-Modal Fusion Data Analysis Strategy

**Status**: Active Development  
**Last Updated**: 2025-11-27  
**Authors**: System Architecture Team

## Executive Summary

This document outlines a **vision-first, numerically-assisted** approach to fusion data analysis that leverages state-of-the-art vision models for rich semantic understanding while maintaining numerical precision through selective data queries.

### Key Insight

Modern vision models (GPT-4V, Claude 3.5 Sonnet, Gemini 2.0 Flash) can:
1. **Describe visual patterns** better than hand-crafted algorithms
2. **Write Python code** to extract numerical data on-demand
3. **Integrate multi-modal context** (plots + metadata + code results)
4. **Generate rich embeddings** for semantic search

This enables a **data scientist workflow**: Look at the plot → Write code to extract details → Execute in sandbox → Generate comprehensive description.

## Architecture Overview

```
IMAS Data → Plot Generation → Vision Model Analysis
                                       ↓
                                Write Python Code
                                       ↓
                                Execute in Sandbox (IMAS access)
                                       ↓
                                Numerical Results
                                       ↓
                          Rich Multi-Modal Description
                                       ↓
                          Text + Vision Embeddings
                                       ↓
                            Vector Store (ChromaDB)
                                       ↓
                          Hybrid Search (text + image + filters)
```

### Core Principle: Vision-First with Numerical Augmentation

**Traditional Approach** (Our Initial Plan):
```
Data → Numerical Features → Text Description → Embedding
```

**Codegen-First Approach** (Vision Model as Data Scientist):
```
Data → Plot → Vision Model → Write Code → Execute Sandbox → Results
                                                    ↓
                                          Rich Description → Embedding
```

## State-of-the-Art Vision Models (November 2025)

### Recommended Models (via OpenRouter)

Based on current OpenRouter rankings, Artificial Analysis leaderboard, and vision capabilities:

| Model | Input Modalities | Context | Cost ($/M tokens) | Quality Score | Best For |
|-------|------------------|---------|-------------------|---------------|----------|
| **Gemini 3 Pro Preview** | Text + Image | 1M | $2 input / $12 output | 73 (Frontier) | Cutting-edge quality, experimental preview |
| **Claude Opus 4.5** | Text + Image | 200K | $5 input / $25 output | 70 (Frontier) | Frontier reasoning, highest reliability |
| **Claude Sonnet 4.5** | Text + Image | 1M | $3 input / $15 output | 63 | Technical analysis, detailed reasoning, tool use |
| **Gemini 2.5 Pro** | Text + Image | 1M | $1.25 input / $10 output | 60 | Advanced reasoning, balanced cost/quality |
| **Gemini 2.5 Flash** | Text + Image | 1M | $0.30 input / $2.50 output | ~55 | Cost-effective, high throughput (485 t/s) |
| **GPT-4.1** | Text + Image | 1M | $2 input / $8 output | ~58 | Strong multi-modal understanding |
| **Gemini 2.0 Flash** | Text + Image | 1M | $0.10 input / $0.40 output | ~50 | Ultra cost-effective for batch processing |

**Quality Score**: Intelligence rating from Artificial Analysis leaderboard (higher is better). Frontier models (≥70) represent cutting edge.

### Why These Models Excel for Fusion Data

1. **Pattern Recognition**:
   - "This profile shows a well-formed pedestal at ρ~0.9"
   - "The ramp-up exhibits three distinct phases"
   - "Visible oscillations suggest MHD activity"

2. **Contextual Understanding**:
   - Reads axis labels, legends, annotations
   - Understands multi-panel layouts
   - Relates plots to physical phenomena

3. **Code Generation** (Critical for Codegen-First):
   - Writes Python code to query data: `imas.util.to_xarray(eq, 'time_slice/global_quantities/ip')`
   - Performs analysis: `np.gradient()`, `np.where()`, custom algorithms
   - Iterates: Generate code → Execute → Review results → Refine

## Pragmatic Atomic Operations Library

### Design Philosophy

Rather than restricting LLMs to overly specific tools, we provide a **reasonable core library of atomic operations** that can be chained together. This balances flexibility with discoverability.

### Core Capabilities

**1. Data Access Operations** (`nucleai.imas.*`)
- Load IDS by type and time range
- Extract specific paths using IMAS path notation
- Convert to xarray/pandas for manipulation
- Access metadata and coordinate systems

**2. Plotting Operations** (`nucleai.plot.*`)

Comprehensive library for fusion diagnostics:

**Waveform Plots**:
- `plot_ip_waveform()` - Plasma current evolution
- `plot_wmhd_waveform()` - Stored energy evolution  
- `plot_pfus_waveform()` - Fusion power evolution
- `plot_density_waveform()` - Line-averaged density
- `plot_beta_waveform()` - Beta evolution (normalized, poloidal, toroidal)
- `plot_custom_waveform(path)` - Generic time-series from any IDS path

**Profile Plots**:
- `plot_te_profile(time)` - Electron temperature vs rho
- `plot_ti_profile(time)` - Ion temperature vs rho
- `plot_ne_profile(time)` - Electron density vs rho
- `plot_q_profile(time)` - Safety factor vs rho
- `plot_pressure_profile(time)` - Pressure profile
- `plot_rotation_profile(time)` - Rotation frequency
- `plot_custom_profile(path, time)` - Generic 1D profile

**Equilibrium Plots**:
- `plot_flux_surfaces(time)` - Poloidal flux contours
- `plot_psi_contours(time)` - Detailed flux topology
- `plot_separatrix(time)` - Last closed flux surface
- `plot_xpoints(time)` - X-point locations
- `plot_boundary_shape(time)` - Plasma boundary evolution

**Spectrograms & 2D Plots**:
- `plot_time_rho_spectrogram(quantity)` - 2D evolution (time vs rho)
- `plot_rz_quantity(quantity, time)` - R-Z plane distribution
- `plot_flux_surface_quantity(quantity, time)` - Quantity on flux surfaces

**Multi-Panel Layouts**:
- `plot_scenario_overview(time)` - Standard diagnostic grid
- `plot_confinement_suite(time)` - Energy confinement analysis
- `plot_transport_analysis(time)` - Transport coefficients
- `plot_mhd_diagnostics(time)` - Stability analysis

**3. Analysis Operations** (`nucleai.features.*`)
- Peak detection and characterization
- Phase segmentation (ramp-up, flat-top, ramp-down)
- Gradient calculations and pedestal detection
- Stability metrics (std, oscillation frequency)
- Event detection (disruptions, ELMs, sawtooth)
- Time-averaging and smoothing

**4. Numerical Operations** (via sandbox: numpy, scipy, xarray)
- All standard scientific Python capabilities
- Signal processing (scipy.signal)
- Interpolation and fitting (scipy.interpolate)
- Statistical analysis (scipy.stats)
- Array manipulation (numpy)
- Data wrangling (pandas, xarray)

### Composability

LLMs chain atomic operations:

```python
# Example: LLM-generated analysis workflow
# 1. Load data
ip_data = load_ids_quantity(imas_uri, 'equilibrium', 'time_slice/global_quantities/ip')

# 2. Plot for visualization
fig = plot_ip_waveform(imas_uri)

# 3. Analyze with atomic operations
phases = detect_phases(ip_data.time, ip_data.values)
stability = calculate_stability_metrics(ip_data.values[phases['flattop']])

# 4. Return structured results
return {
    'peak_ip': float(np.abs(ip_data.values).max()),
    'flattop_duration': float(phases['flattop_duration']),
    'flattop_stability': stability
}
```

### Atomic Operations: Advantages

1. **Discoverability**: Limited set of well-documented functions
2. **Flexibility**: Combine in arbitrary ways
3. **Maintainability**: Fewer functions than all possible combinations
4. **Introspection**: Each function has rich docstring with examples
5. **Testability**: Each atomic operation independently tested
6. **Evolution**: Add new atomics as needs emerge

### Not Too Specific, Not Too General

**Too Specific** (Avoid):
- `get_iter_baseline_scenario_flattop_ip_mean()` ❌
- `detect_elm_events_in_divertor_dα()` ❌

**Too General** (Also Avoid):
- `analyze_everything()` ❌  
- `query_data(arbitrary_string)` ❌

**Right Level** (Atomic & Composable):
- `plot_ip_waveform(imas_uri)` ✅
- `detect_phases(time, values)` ✅
- `calculate_gradient(data, coord)` ✅
- `find_peaks(signal, threshold)` ✅

## Implementation Strategy

### Phase 1: Vision-Assisted Feature Extraction (Weeks 1-4)

**Goal**: Vision model generates rich descriptions by writing and executing Python code.

**Components**:

1. **Plot Generation Pipeline** (`nucleai.plot`)
   - Standard diagnostic plots for each IDS type
   - Configurable styles (publication, diagnostic, analysis)
   - Multi-panel layouts with context

2. **Vision Analysis Service** (`nucleai.vision`)
   - Interface to OpenRouter vision models
   - Code execution sandbox with IMAS access
   - Prompt templates for code-based analysis

3. **Code Execution Sandbox** (`nucleai.execution`)
   - Safe Python execution environment
   - Pre-loaded modules: `imas`, `numpy`, `pandas`, `xarray`
   - Resource limits: memory, time, file access
   - Return serializable results to vision model

**Workflow Example** (Codegen-First):

```python
# 1. Generate plot
plot_bytes = await generate_ip_waveform_plot(imas_uri)

# 2. Vision model analyzes by writing Python code
analysis = await vision_analyze(
    image=plot_bytes,
    imas_uri=imas_uri,
    prompt="""
    Analyze this plasma current waveform. You have access to the IMAS data.
    
    Write Python code to extract the numerical details you need. Available:
    - imas, imas.util, numpy, pandas, xarray
    - Variable `imas_uri` contains the data location
    
    Your code should:
    1. Load the equilibrium IDS
    2. Extract plasma current vs time
    3. Calculate peak values, phase durations, stability metrics
    4. Return a dict with your findings
    
    Then provide a comprehensive technical description combining visual
    observations with the numerical results.
    """
)

# Vision model generates and executes this code:
generated_code = """
import imas
import imas.util
import numpy as np

# Load data
entry = imas.DBEntry(imas_uri, 'r')
eq = entry.get('equilibrium')
ip_ds = imas.util.to_xarray(eq, 'time_slice/global_quantities/ip')

# Extract arrays
ip = ip_ds['time_slice.global_quantities.ip'].values / 1e6  # MA
time = ip_ds.coords['time'].values
dip_dt = np.gradient(ip, time)

# Analyze phases
rampup_mask = dip_dt > 0.01
flattop_mask = (abs(dip_dt) < 0.005) & (abs(ip) > 14.0)
rampdown_mask = dip_dt < -0.01

# Calculate metrics
results = {
    'peak_ip_MA': float(abs(ip).max()),
    'peak_time_s': float(time[abs(ip).argmax()]),
    'rampup_duration_s': float((time[rampup_mask][-1] - time[rampup_mask][0]) 
                                if rampup_mask.any() else 0),
    'flattop_duration_s': float((time[flattop_mask][-1] - time[flattop_mask][0])
                                 if flattop_mask.any() else 0),
    'flattop_ip_mean_MA': float(abs(ip[flattop_mask]).mean() 
                                  if flattop_mask.any() else 0),
    'flattop_ip_std_MA': float(abs(ip[flattop_mask]).std() 
                                if flattop_mask.any() else 0),
    'rampdown_duration_s': float((time[rampdown_mask][-1] - time[rampdown_mask][0])
                                  if rampdown_mask.any() else 0),
}

entry.close()
"""

# Code executes in sandbox, returns:
code_results = {
    'peak_ip_MA': 15.02,
    'peak_time_s': 580.9,
    'rampup_duration_s': 78.7,
    'flattop_duration_s': 655.0,
    'flattop_ip_mean_MA': 15.00,
    'flattop_ip_std_MA': 0.03,
    'rampdown_duration_s': 63.1
}

# 3. Vision model generates rich description using code results
final_text = """
This waveform demonstrates exceptional control of the ITER baseline scenario
over an extended 797s pulse with three well-defined phases:

**Ramp-up Phase (0-79s)**: Rapid current rise from near-zero to 15 MA over
79 seconds. The smooth ascent without visible oscillations indicates efficient
plasma formation and current drive. Peak ramp rate occurs in the early phase,
consistent with aggressive breakdown and current penetration strategies.

**Flat-top Phase (79-734s)**: Outstanding stability maintained at 15.00 ± 0.03 MA
for 655 seconds. This represents 82% of the total pulse duration and demonstrates
the robustness of the DINA-JINTRAC integrated modeling. The extremely low
variance (σ = 0.03 MA, or 0.2%) indicates excellent poloidal field coil control
and equilibrium maintenance. No disruptions or significant MHD activity visible.

**Ramp-down Phase (734-797s)**: Controlled termination over 63 seconds with
symmetric descent to ~1.6 MA. The managed ramp-down suggests careful plasma
shape evolution and position control as current decreases.

**Physics Context**: This scenario achieves Q = 9.55 fusion performance with
515 MW fusion power in H-mode confinement. The extended flat-top duration is
significant for ITER's mission, providing substantial time for transport studies,
diagnostic validation, and control system testing.
"""

# 4. Generate embeddings
text_emb = await embed_text(final_text)
vision_emb = await embed_image(plot_bytes)

# 5. Store in vector DB
await store_features(
    simulation_uuid=uuid,
    text_description=final_text,
    text_embedding=text_emb,
    vision_embedding=vision_emb,
    plot_config=plot_config,
    numerical_cache=code_results,  # From code execution
    generated_code=generated_code  # Store for reproducibility
)
```

### Code Execution Sandbox Architecture

**Design Goal**: Enable vision models to write arbitrary Python code for data analysis while maintaining security boundaries.

**Allowed Modules**:
- **IMAS**: `imas`, `imas.util` (full read-only access)
- **Numerical**: `numpy`, `scipy` (signal, interpolate, stats)
- **Data**: `pandas`, `xarray` (manipulation and conversion)
- **Visualization**: `matplotlib` (output serialization only, no display)

**Security Boundaries**:
- Read-only IMAS access (DBEntry mode='r')
- No file system writes (except temporary scratch space)
- No network access (all IMAS URIs pre-validated)
- No subprocess execution or eval/exec outside sandbox
- Resource limits: 30s CPU time, 2GB memory per execution

**Execution Protocol**:

1. **Code Validation**:
   - AST parsing to detect forbidden operations
   - Import whitelist enforcement
   - Syntax error pre-check

2. **Sandboxed Execution**:
   - Isolated namespace with pre-imported modules
   - Context variables: `imas_uri`, `simulation_uuid`
   - Timeout enforcement via threading/asyncio
   - Memory tracking via tracemalloc

3. **Result Serialization**:
   - Code must return JSON-compatible dict
   - Auto-convert numpy types: `float(np.float64(x))`
   - Support nested structures: lists, dicts, primitives
   - Error messages returned as `{'error': str, 'traceback': str}`

4. **Multi-Turn Iteration**:
   - Vision model receives execution results
   - Can generate refined code based on errors or partial results
   - Maximum 3 iterations per analysis to prevent loops
   - Each iteration tracked for debugging

**Example Sandbox API**:

```python
from nucleai.vision.sandbox import execute_code

result = await execute_code(
    code=generated_code,
    context={'imas_uri': uri, 'simulation_uuid': uuid},
    timeout=30,  # seconds
    memory_limit=2_000_000_000  # bytes
)

if result['success']:
    data = result['output']  # JSON-compatible dict from code
else:
    error = result['error']
    traceback = result['traceback']
    # Vision model can retry with corrected code
```

**Advantages Over Tool Definitions**:
- Unlimited flexibility: vision model invents new analyses
- No API maintenance: code adapts to data structure changes
- Self-documenting: generated code shows exact methodology
- Reproducible: stored code can be re-run for validation
- Iterative: model refines approach based on results

### Phase 2: Multi-Modal Search (Weeks 5-8)

**Goal**: Enable search by text, image, or hybrid queries.

**Search Modes**:

1. **Text Search**: "Find stable 15 MA baseline scenarios"
   → Semantic similarity on text embeddings

2. **Image Search**: User uploads plot
   → Vision similarity on image embeddings

3. **Hybrid Search**: "Find scenarios like this image but with longer flat-top"
   → Vision similarity + numerical filter

4. **Numerical Filters**: "ip_peak > 10 AND flattop_duration > 400"
   → Direct where clause on cached numerical data

### Phase 3: Interactive Refinement (Weeks 9-12)

**Goal**: Vision model guides user through exploration.

**Capabilities**:

1. **Query Expansion**: 
   - User: "Show me good H-mode scenarios"
   - Vision: "I'll look for profiles with clear pedestals and stable flat-tops"

2. **Result Explanation**:
   - Vision compares retrieved plots
   - Highlights similarities and differences
   - Suggests refinements

3. **Anomaly Detection**:
   - Vision spots unusual features across many plots
   - Flags for expert review

## Technical Implementation

### Directory Structure

```
nucleai/
├── vision/                  # NEW: Vision model integration
│   ├── __init__.py
│   ├── analyzer.py         # Vision model API with code execution
│   ├── sandbox.py          # Safe code execution environment
│   └── prompts.py          # Prompt templates for code generation
├── imas/                    # NEW: Data access atomic operations
│   ├── __init__.py
│   ├── access.py           # Atomic data loading functions
│   ├── loader.py           # Existing DBEntry wrappers
│   └── exceptions.py       # IMAS-specific errors
├── features/                # NEW: Analysis atomic operations
│   ├── __init__.py
│   ├── atomic.py           # Composable analysis functions
│   ├── waveforms.py        # Waveform-specific analysis
│   └── profiles.py         # Profile-specific analysis
├── plot/                    # NEW: Plotting atomic operations
│   ├── __init__.py
│   ├── waveforms.py        # Time-series plots (ip, wmhd, pfus, etc.)
│   ├── profiles.py         # 1D profiles (Te, ne, q, etc.)
│   ├── equilibrium.py      # Flux surfaces, boundaries, R-Z plots
│   ├── spectrograms.py     # 2D evolution plots (time-rho, etc.)
│   └── layouts.py          # Multi-panel diagnostic layouts
├── embeddings/
│   ├── text.py             # Existing text embeddings
│   └── vision.py           # NEW: Image embeddings (CLIP/SigLIP)
└── search/
    ├── semantic.py         # Existing text search
    ├── image.py            # NEW: Image similarity search
    └── hybrid.py           # NEW: Multi-modal search

docs/
├── VISION_FIRST_STRATEGY.md      # This document
└── VISION_IMPLEMENTATION_PLAN.md # Detailed implementation tasks
```

### Key Technologies

1. **Vision Models**: OpenRouter API (Claude Sonnet 4.5, Gemini 2.5 Flash/Pro)
2. **Code Execution**: Restricted Python sandbox with IMAS access
3. **Atomic Operations**: Composable library for data access, plotting, analysis
4. **Image Embeddings**: OpenCLIP, SigLIP (via transformers)
5. **Plot Generation**: Matplotlib with consistent styling for all diagnostic types
6. **Vector Store**: ChromaDB (supports multi-vector per document)
7. **Security**: Resource-limited sandbox, read-only IMAS, no network access

## Development Timeline

### Weeks 1-2: Foundation
- [x] Create strategy document
- [ ] Implement `nucleai.vision.analyzer` with OpenRouter integration
- [ ] Create `nucleai.vision.sandbox` for safe code execution
- [ ] Define allowed modules and resource limits

### Weeks 3-4: Plot Generation + Code-Enabled Vision Analysis
- [ ] Implement atomic data access operations (`nucleai.imas.access`)
- [ ] Implement atomic analysis operations (`nucleai.features.atomic`)
- [ ] Implement comprehensive plotting library:
  - [ ] `nucleai.plot.waveforms` (ip, wmhd, pfus, density, beta)
  - [ ] `nucleai.plot.profiles` (Te, Ti, ne, q, pressure, rotation)
  - [ ] `nucleai.plot.equilibrium` (flux surfaces, separatrix, boundaries)
  - [ ] `nucleai.plot.spectrograms` (time-rho evolution)
  - [ ] `nucleai.plot.layouts` (multi-panel diagnostic grids)
- [ ] Create prompt templates for code generation
- [ ] Test vision model code generation on sample plots
- [ ] Validate sandbox security boundaries
- [ ] Test multi-turn code refinement workflow

### Weeks 5-6: Embedding + Storage
- [ ] Add `nucleai.embeddings.vision` (OpenCLIP integration)
- [ ] Extend ChromaDB schema for multi-modal storage
- [ ] Store generated code for reproducibility
- [ ] Implement batch processing for SimDB data
- [ ] Create progress tracking for large-scale ingestion

### Weeks 7-8: Search Interface
- [ ] Implement text search (semantic similarity)
- [ ] Implement image search (vision similarity)
- [ ] Implement hybrid search (combined scoring)
- [ ] Add numerical filtering on cached results from code execution

### Weeks 9-12: Interactive Features
- [ ] Query expansion and refinement
- [ ] Result comparison and explanation (vision generates comparison code)
- [ ] Anomaly detection across corpus (vision writes detection algorithms)
- [ ] User feedback loop

## Cost Analysis (November 2025 Pricing)

### Per-Simulation Processing (One-Time)

| Component | Cost | Notes |
|-----------|------|-------|
| Plot generation | $0.00 | Local compute |
| Vision analysis (Gemini 2.0 Flash) | $0.01 | ~1 image + 2K tokens @ $0.10/$0.40 per M |
| Vision analysis (Gemini 2.5 Flash) | $0.015 | ~1 image + 2K tokens @ $0.30/$2.50 per M |
| Vision analysis (Gemini 3 Pro Preview) | $0.03 | ~1 image + 2K tokens @ $2/$12 per M (frontier) |
| Vision analysis (Claude Sonnet 4.5) | $0.04 | ~1 image + 2K tokens @ $3/$15 per M |
| Vision analysis (Claude Opus 4.5) | $0.06 | ~1 image + 2K tokens @ $5/$25 per M (frontier) |
| Code execution (3-5 per sim) | $0.00 | Local IMAS data access |
| Text embedding | $0.00 | Local Sentence-Transformers |
| Vision embedding | $0.00 | Local OpenCLIP |
| **Total per simulation (Gemini 2.0)** | **$0.01** | Budget option |
| **Total per simulation (Gemini 2.5)** | **$0.015** | Balanced option |
| **Total per simulation (Gemini 3)** | **$0.03** | Frontier preview |
| **Total per simulation (Claude Sonnet)** | **$0.04** | Premium quality |
| **Total per simulation (Claude Opus)** | **$0.06** | Highest quality |
| **Total for 1300 sims (Gemini 2.5)** | **$20** | Recommended for production |
| **Total for 1300 sims (Gemini 3)** | **$39** | Cutting-edge quality |

### Ongoing Query Costs

- Text search: $0.00 (local embedding + vector search)
- Image search: $0.00 (local embedding + vector search)
- Hybrid search: $0.00 (local)
- Vision-assisted refinement: $0.01-0.05 per interaction (optional)

## Success Metrics

### Quality Metrics
1. **Description Richness**: Average description length, technical depth
2. **Numerical Accuracy**: Agreement between code-extracted and ground-truth values
3. **Search Relevance**: User satisfaction with search results

### Performance Metrics
1. **Latency**: Plot generation + vision analysis < 5s per simulation
2. **Cost**: < $0.10 per simulation for vision analysis
3. **Throughput**: Process 1300 SimDB simulations in < 2 hours

## Risk Mitigation

### Risk: Vision model hallucination
**Mitigation**: Code execution forces numerical precision. Vision provides narrative, code provides facts. Generated code is stored for reproducibility and audit.

### Risk: API costs for large-scale processing
**Mitigation**: Use cost-effective models (Gemini 2.0 Flash: $0.075/$0.30 per M tokens). Batch processing. Cache results.

### Risk: Plot generation slowdown
**Mitigation**: Generate plots lazily (on-demand). Cache frequently accessed plots. Optimize matplotlib rendering.

### Risk: Search quality degradation
**Mitigation**: Hybrid scoring combines vision similarity + text semantic + numerical filters. User feedback loop.

## Conclusion

This codegen-first approach leverages the extraordinary capabilities of modern multimodal models while maintaining numerical precision through code execution. By letting vision models "look" at plots and "write code" to extract details, we create rich, searchable descriptions that capture both quantitative and qualitative aspects of fusion data. The vision model acts as a data scientist, not just an image classifier.

---

**Next Steps**: See implementation tasks in project tracking.
