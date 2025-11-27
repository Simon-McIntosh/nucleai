# Vision-First Implementation Plan (Codegen-First Architecture)

**Status**: Ready to Execute  
**Dependencies**: See `VISION_FIRST_STRATEGY.md` for full context  
**Timeline**: 12 weeks (3 months)  
**Architecture**: Vision models write and execute Python code rather than calling predefined tools

## Overview

This document provides actionable steps to implement the codegen-first vision-assisted fusion data analysis pipeline. Vision models act as data scientists that write Python code for analysis, which executes in a secure sandbox with IMAS access.

### Atomic Operations Philosophy

Rather than restricting LLMs to overly specific tools, we provide a **library of composable atomic operations**:

- **Data Access**: Load IDS, extract paths, convert to xarray/pandas
- **Plotting**: Comprehensive suite for waveforms, profiles, equilibrium, spectrograms, multi-panel layouts
- **Analysis**: Peak detection, phase segmentation, gradient calculation, stability metrics
- **Numerical**: Full scipy/numpy capabilities via sandbox

LLMs chain these atomics in arbitrary combinations to perform novel analyses. See `VISION_FIRST_STRATEGY.md` for detailed rationale.

## Phase 1: Foundation (Weeks 1-2)

### Week 1: Vision Model Integration

**Task 1.1**: Add vision model configuration to settings
- **File**: `nucleai/core/config.py`
- **Action**: Add fields to `Settings` class:
  ```python
  vision_model: str = "google/gemini-2.5-flash"  # Cost-effective default
  vision_premium_model: str = "anthropic/claude-sonnet-4.5"  # High-quality option
  vision_frontier_model: str = "google/gemini-3-pro-preview"  # Cutting-edge preview
  vision_max_tokens: int = 4000
  vision_temperature: float = 0.0
  ```
- **Test**: Verify settings load from `.env`
- **Note**: Preview models may have limited availability or change behavior

**Task 1.2**: Create vision analyzer module
- **File**: `nucleai/vision/analyzer.py`
- **Action**: Implement `VisionAnalyzer` class with:
  - `analyze_image(image_bytes, prompt, tools) -> VisionResult`
  - OpenRouter API client integration
  - Tool call parsing and execution
  - Error handling with recovery hints
- **Dependencies**: `httpx` for async HTTP, existing `openai_api_key`
- **Test**: Mock API call, verify tool schema generation

**Task 1.3**: Define vision result models
- **File**: `nucleai/vision/models.py`
- **Action**: Create Pydantic models:
  ```python
  class CodeExecution(BaseModel):
      code: str  # Generated Python code
      success: bool
      output: dict[str, Any] | None  # JSON results from code
      error: str | None
      execution_time: float
      iteration: int  # Which iteration (1-3)
  
  class VisionResult(BaseModel):
      text: str  # Rich description
      code_executions: list[CodeExecution]  # All attempts
      numerical_data: dict[str, float | int]  # Final extracted data
      tokens_used: int
      model: str
  ```
- **Test**: Schema validation

### Week 2: Code Execution Sandbox

**Task 1.4**: Create sandbox module structure
- **File**: `nucleai/vision/sandbox.py`
- **Action**: Implement secure code execution:
  ```python
  class CodeExecutionResult(BaseModel):
      success: bool
      output: dict[str, Any] | None  # JSON-compatible results
      error: str | None
      traceback: str | None
      execution_time: float
      memory_used: int
      
  async def execute_code(
      code: str,
      context: dict[str, Any],
      timeout: float = 30.0,
      memory_limit: int = 2_000_000_000
  ) -> CodeExecutionResult
  ```
- **Test**: Execute simple code with context variables

**Task 1.5**: Implement AST validation
- **File**: `nucleai/vision/sandbox.py`
- **Action**: 
  - Parse code with `ast.parse()`
  - Check for forbidden operations (exec, eval, open with 'w')
  - Validate import whitelist (imas, numpy, pandas, xarray, scipy, matplotlib)
  - Reject file system writes outside temp space
- **Test**: Verify rejection of malicious code patterns

**Task 1.6**: Add resource limits and timeout
- **File**: `nucleai/vision/sandbox.py`
- **Action**:
  - Use `asyncio.wait_for()` for timeout enforcement
  - Track memory with `tracemalloc`
  - Create isolated namespace with pre-imported modules
  - Handle exceptions and return structured errors
- **Test**: Verify timeout kills long-running code, memory limits enforced

**Task 1.7**: Integrate sandbox with vision analyzer
- **File**: `nucleai/vision/analyzer.py`
- **Action**:
  - Parse generated code from vision model response
  - Execute in sandbox with IMAS context
  - Return results to vision model for description generation
  - Support multi-turn iteration (up to 3 attempts)
- **Test**: End-to-end with mock vision responses containing Python code
- **Cost Targets**: 
  - Gemini 2.5 Flash: <$0.02/sim (production default)
  - Gemini 3 Pro Preview: <$0.04/sim (frontier quality)
  - Claude Sonnet 4.5: <$0.05/sim (premium reliability)

## Phase 2: Plot Generation + Vision Analysis (Weeks 3-4)

### Week 3: Standard Diagnostic Plots & Data Access Atomics

**Task 2.0**: Create data access module (atomic operations)
- **File**: `nucleai/imas/access.py`
- **Action**: Implement atomic data access operations for LLM use:
  ```python
  def load_ids(imas_uri: str, ids_name: str) -> Any:
      """Load entire IDS (equilibrium, core_profiles, etc.)."""
  
  def load_ids_quantity(
      imas_uri: str,
      ids_path: str,  # e.g., "equilibrium/time_slice/global_quantities/ip"
      as_xarray: bool = True
  ) -> xr.DataArray | Any:
      """Load specific quantity, optionally as xarray."""
  
  def get_time_range(imas_uri: str, ids_name: str) -> tuple[float, float]:
      """Get (min_time, max_time) for an IDS."""
  
  def get_time_slice_at(
      imas_uri: str,
      ids_name: str,
      time: float
  ) -> Any:
      """Get IDS data closest to specified time."""
  ```
- **Purpose**: Provide simple, documented data access for LLM-generated code
- **Test**: Load various IDS types and paths from DINA-JINTRAC

**Task 2.1**: Create waveform plotting module (atomic operations)
- **File**: `nucleai/plot/waveforms.py`
- **Action**: Implement standardized atomic waveform plots:
  ```python
  # Core waveforms
  def plot_ip_waveform(imas_uri: str, style: str = "diagnostic") -> bytes
  def plot_wmhd_waveform(imas_uri: str, style: str = "diagnostic") -> bytes
  def plot_pfus_waveform(imas_uri: str, style: str = "diagnostic") -> bytes
  def plot_density_waveform(imas_uri: str, style: str = "diagnostic") -> bytes
  
  # Beta diagnostics
  def plot_beta_waveform(imas_uri: str, beta_type: str = "all", style: str = "diagnostic") -> bytes
  # beta_type: "normalized" | "poloidal" | "toroidal" | "all"
  
  # Generic waveform (any IDS path)
  def plot_custom_waveform(
      imas_uri: str,
      ids_path: str,  # e.g., "equilibrium/time_slice/global_quantities/ip"
      style: str = "diagnostic"
  ) -> bytes
  ```
- **Features**: Consistent styling, axis labels, legends, annotations, multi-phase coloring
- **Returns**: PNG bytes suitable for vision model input
- **Test**: Generate plots for DINA-JINTRAC, verify visual quality
- **Priority**: Start with ip, wmhd, pfus; add others incrementally

**Task 2.2**: Create profile plotting module (atomic operations)
- **File**: `nucleai/plot/profiles.py`
- **Action**: Implement atomic profile plots:
  ```python
  # Temperature profiles
  def plot_te_profile(imas_uri: str, time: float, style: str = "diagnostic") -> bytes
  def plot_ti_profile(imas_uri: str, time: float, style: str = "diagnostic") -> bytes
  
  # Density profiles
  def plot_ne_profile(imas_uri: str, time: float, style: str = "diagnostic") -> bytes
  
  # MHD profiles
  def plot_q_profile(imas_uri: str, time: float, style: str = "diagnostic") -> bytes
  def plot_pressure_profile(imas_uri: str, time: float, style: str = "diagnostic") -> bytes
  
  # Rotation
  def plot_rotation_profile(imas_uri: str, time: float, style: str = "diagnostic") -> bytes
  
  # Generic profile (any 1D IDS path)
  def plot_custom_profile(
      imas_uri: str,
      ids_path: str,  # e.g., "core_profiles/profiles_1d/electrons/temperature"
      time: float,
      style: str = "diagnostic"
  ) -> bytes
  ```
- **Features**: Rho normalization, pedestal highlighting, gradient overlays
- **Test**: Generate for various time slices
- **Priority**: Start with Te, ne, q; add others incrementally

**Task 2.3**: Define plot configuration schemas
- **File**: `nucleai/plot/models.py`
- **Action**: Create models to store plot "recipes":
  ```python
  class PlotConfig(BaseModel):
      plot_type: Literal["waveform", "profile", "equilibrium", "spectrogram", "multi_panel"]
      imas_uri: str
      time: float | None
      quantities: list[str]
      style: str
      
      def regenerate(self) -> bytes:
          """Regenerate plot from config."""
  ```
- **Purpose**: Store configs instead of images in DB
- **Test**: Roundtrip: config → plot → config → plot (same result)

**Task 2.3b**: Create multi-panel layout module
- **File**: `nucleai/plot/layouts.py`
- **Action**: Implement composite diagnostic layouts:
  ```python
  # Standard multi-panel views
  def plot_scenario_overview(
      imas_uri: str,
      time: float,
      style: str = "diagnostic"
  ) -> bytes:
      """Standard 2x3 grid: Ip, wmhd, pfus, Te, ne, q."""
  
  def plot_confinement_suite(
      imas_uri: str,
      time: float,
      style: str = "diagnostic"
  ) -> bytes:
      """Energy confinement: wmhd, Te, ne, P_input, tau_E."""
  
  def plot_transport_analysis(
      imas_uri: str,
      time: float,
      style: str = "diagnostic"
  ) -> bytes:
      """Transport: Te, ne, chi_e, chi_i, D."""
  
  def plot_mhd_diagnostics(
      imas_uri: str,
      time: float,
      style: str = "diagnostic"
  ) -> bytes:
      """MHD: q, pressure, j, flux surfaces."""
  ```
- **Features**: Consistent subplot layout, shared time axes where applicable
- **Test**: Generate overview for DINA-JINTRAC
- **Priority**: Implement after individual atomic plots work

**Task 2.3c**: Create analysis atomic operations module
- **File**: `nucleai/features/atomic.py`
- **Action**: Implement reusable analysis operations for LLM use:
  ```python
  # Phase detection
  def detect_phases(
      time: np.ndarray,
      values: np.ndarray,
      quantity_type: str = "ip"  # "ip", "wmhd", etc.
  ) -> dict[str, Any]:
      """Detect ramp-up, flat-top, ramp-down phases."""
      # Returns: {'rampup': slice, 'flattop': slice, 'rampdown': slice, 'durations': dict}
  
  # Stability analysis
  def calculate_stability_metrics(
      values: np.ndarray,
      time: np.ndarray | None = None
  ) -> dict[str, float]:
      """Calculate std, variance, oscillation frequency."""
  
  # Peak detection
  def find_peaks_with_context(
      values: np.ndarray,
      time: np.ndarray,
      threshold: float | None = None
  ) -> list[dict[str, float]]:
      """Find peaks with time, value, width, prominence."""
  
  # Gradient analysis
  def calculate_gradient(
      values: np.ndarray,
      coordinate: np.ndarray,
      smoothing: float | None = None
  ) -> np.ndarray:
      """Calculate gradient with optional smoothing."""
  
  # Pedestal detection
  def detect_pedestal(
      profile: np.ndarray,
      rho: np.ndarray,
      threshold: float = 0.8
  ) -> dict[str, float]:
      """Find pedestal location, width, height."""
  
  # Event detection
  def detect_events(
      time: np.ndarray,
      signal: np.ndarray,
      event_type: str = "disruption"  # "disruption", "elm", "sawtooth"
  ) -> list[dict[str, Any]]:
      """Detect specific event types in time series."""
  ```
- **Purpose**: Provide battle-tested analysis functions LLMs can compose
- **Test**: Each function on synthetic and real data
- **Documentation**: Rich docstrings with examples for LLM introspection

### Week 4: Code-Based Vision Analysis

**Task 2.4**: Create code generation prompts
- **File**: `nucleai/vision/prompts.py`
- **Action**: Define prompt templates for code generation:
  ```python
  WAVEFORM_CODE_ANALYSIS = """
  Analyze this plasma parameter waveform. You have IMAS data access.
  
  Write Python code to extract numerical details. Available modules:
  - imas, imas.util (data loading)
  - numpy, scipy (calculations, signal processing)
  - pandas, xarray (data manipulation)
  
  Context variables in your code:
  - imas_uri: str (IMAS data location)
  - simulation_uuid: str
  
  Your code should:
  1. Load the relevant IDS (equilibrium, core_profiles, etc.)
  2. Extract time-series or spatial data
  3. Calculate key metrics (peaks, phases, stability, gradients)
  4. Return a JSON-compatible dict with findings
  
  Then provide a comprehensive description combining visual observations
  with your numerical results. Address:
  - Overall temporal evolution and distinct phases
  - Stability characteristics and control quality  
  - Any anomalies, oscillations, or disruptions
  - Physical interpretation in fusion context
  """
  ```
- **Include templates for**: profiles, equilibrium, multi-panel plots
- **Test**: Verify prompts produce executable code

**Task 2.5**: End-to-end vision workflow with code execution
- **File**: `nucleai/vision/workflows.py`
- **Action**: Implement complete pipeline:
  ```python
  async def analyze_simulation(imas_uri: str) -> VisionResult:
      """Complete code-enabled vision analysis."""
      # 1. Generate standard plots
      # 2. Vision model writes code
      # 3. Execute code in sandbox
      # 4. Vision model generates description with results
      # 5. Return rich description + numerical cache + code
  ```
- **Test**: Process DINA-JINTRAC from start to finish
- **Validate**: Description quality, code correctness, numerical accuracy

**Task 2.6**: Multi-turn code iteration
- **File**: `nucleai/vision/workflows.py`
- **Action**: Handle code refinement:
  ```python
  async def iterative_analysis(
      imas_uri: str,
      max_iterations: int = 3
  ) -> VisionResult:
      """Allow vision model to refine code based on results."""
      # Iteration loop:
      # - Vision generates code
      # - Execute in sandbox
      # - If error, pass error back to vision for correction
      # - If success, vision generates final description
  ```
- **Test**: Trigger intentional errors, verify recovery

**Task 2.7**: Batch processing utility
- **File**: `nucleai/vision/batch.py`
- **Action**: Process multiple simulations efficiently:
  ```python
  async def process_simdb_batch(
      limit: int = 100,
      filters: dict | None = None,
      max_concurrent: int = 5
  ) -> list[VisionResult]:
      """Process SimDB simulations in parallel."""
  ```
- **Features**: Progress tracking, error handling, cost monitoring
- **Test**: Process 10 sims, verify throughput and cost

## Phase 3: Embeddings + Storage (Weeks 5-6)

### Week 5: Image Embeddings

**Task 3.1**: Add vision embedding module
- **File**: `nucleai/embeddings/vision.py`
- **Action**: Implement image embedding:
  ```python
  def embed_image(image_bytes: bytes, model: str = "openai/clip-vit-base-patch32") -> list[float]
  def embed_images_batch(images: list[bytes]) -> list[list[float]]
  ```
- **Use**: OpenCLIP via transformers or OpenRouter embedding endpoint
- **Test**: Embed sample plots, verify similarity calculations

**Task 3.2**: Multi-modal storage schema
- **File**: `nucleai/search/storage.py`
- **Action**: Extend ChromaDB schema:
  ```python
  class MultiModalDocument:
      simulation_uuid: str
      text_description: str
      text_embedding: list[float]
      vision_embedding: list[float]
      plot_config: PlotConfig
      numerical_cache: dict[str, float]
      metadata: dict
  ```
- **ChromaDB**: Use separate collections or multi-vector per document
- **Test**: Store and retrieve with different embedding types

**Task 3.3**: Ingestion pipeline
- **File**: `nucleai/data/ingest.py`
- **Action**: Complete ingestion workflow:
  ```python
  async def ingest_simulations(
      simulation_uuids: list[str],
      regenerate: bool = False
  ) -> IngestStats:
      """Ingest simulations into vector store."""
      # For each sim:
      #   1. Generate plots
      #   2. Vision analysis
      #   3. Generate embeddings
      #   4. Store in ChromaDB
  ```
- **Features**: Skip already-processed, cost tracking, error recovery
- **Test**: Ingest 20 sims, verify DB contents

### Week 6: Search Interface

**Task 3.4**: Text search implementation
- **File**: `nucleai/search/text.py`
- **Action**: Semantic text search:
  ```python
  async def search_by_text(
      query: str,
      limit: int = 10,
      filters: dict | None = None
  ) -> list[SearchResult]:
      """Search using text embedding similarity."""
  ```
- **Test**: Various queries, verify relevance

**Task 3.5**: Image search implementation
- **File**: `nucleai/search/image.py`
- **Action**: Visual similarity search:
  ```python
  async def search_by_image(
      image_bytes: bytes,
      limit: int = 10,
      filters: dict | None = None
  ) -> list[SearchResult]:
      """Find visually similar plots."""
  ```
- **Test**: Upload plot, find similar waveforms

**Task 3.6**: Hybrid search implementation
- **File**: `nucleai/search/hybrid.py`
- **Action**: Combined search:
  ```python
  async def hybrid_search(
      text_query: str | None = None,
      image_query: bytes | None = None,
      numerical_filters: dict | None = None,
      limit: int = 10
  ) -> list[SearchResult]:
      """Multi-modal search with numerical filtering."""
      # Combine: text similarity + vision similarity + where clauses
      # Configurable weighting: alpha * text + beta * vision
  ```
- **Test**: Complex queries with multiple modalities

## Phase 4: Interactive Features (Weeks 7-8)

### Week 7: Query Refinement

**Task 4.1**: Query expansion
- **File**: `nucleai/search/expansion.py`
- **Action**: LLM-assisted query expansion:
  ```python
  async def expand_query(user_query: str) -> ExpandedQuery:
      """Generate search strategy from natural language."""
      # Returns: text queries, numerical filters, search hints
  ```
- **Test**: Various user intents, verify expansions

**Task 4.2**: Result explanation
- **File**: `nucleai/search/explain.py`
- **Action**: Explain search results:
  ```python
  async def explain_results(
      query: str,
      results: list[SearchResult]
  ) -> str:
      """Explain why these results match the query."""
      # Compare result descriptions, highlight similarities
  ```
- **Test**: Generate explanations, verify quality

**Task 4.3**: Interactive refinement loop
- **File**: `nucleai/search/interactive.py`
- **Action**: Multi-turn refinement:
  ```python
  async def refine_search(
      initial_query: str,
      feedback: str,
      previous_results: list[SearchResult]
  ) -> list[SearchResult]:
      """Refine search based on user feedback."""
  ```
- **Test**: Simulated user interactions

### Week 8: Quality Assurance

**Task 4.4**: Validation suite
- **File**: `tests/integration/test_vision_pipeline.py`
- **Action**: End-to-end tests:
  - Known simulation → expected description quality
  - Search queries → expected relevance
  - Tool calling → numerical accuracy
- **Metrics**: Precision, recall, description richness

**Task 4.5**: Performance benchmarking
- **File**: `tests/benchmarks/vision_performance.py`
- **Action**: Measure:
  - Latency per simulation
  - Cost per simulation
  - Throughput (sims/hour)
  - Search latency
- **Compare against targets from strategy doc**

**Task 4.6**: Cost monitoring
- **File**: `nucleai/vision/cost.py`
- **Action**: Track API costs:
  ```python
  class CostTracker:
      def record_api_call(model: str, tokens_in: int, tokens_out: int)
      def get_total_cost() -> float
      def get_cost_by_simulation() -> dict[str, float]
  ```
- **Integrate**: Into all vision API calls
- **Test**: Verify cost calculations match actuals

## Phase 5: Production Readiness (Weeks 9-12)

### Week 9: CLI Tools

**Task 5.1**: Ingestion CLI
- **File**: `nucleai/cli/ingest.py`
- **Action**: Command-line tool for batch processing:
  ```bash
  nucleai ingest simdb --limit 100 --filters '{"machine": "ITER"}'
  nucleai ingest uuid --id abc123
  nucleai ingest status  # Show progress
  ```
- **Use**: Click framework, Rich for progress
- **Test**: Process sims from CLI

**Task 5.2**: Search CLI
- **File**: `nucleai/cli/search.py`
- **Action**: Interactive search tool:
  ```bash
  nucleai search text "baseline scenarios"
  nucleai search image plot.png
  nucleai search hybrid --text "..." --image plot.png --filter "ip_peak > 10"
  ```
- **Test**: All search modes from CLI

### Week 10: Documentation

**Task 5.3**: API reference
- **File**: `docs/API_REFERENCE.md`
- **Action**: Complete API documentation with examples for all public functions
- **Generate**: Using introspection + docstrings

**Task 5.4**: User guide
- **File**: `docs/USER_GUIDE.md`
- **Action**: Step-by-step guides:
  - Setup and configuration
  - Ingesting data
  - Searching with different modalities
  - Interpreting results
  - Cost management

**Task 5.5**: Developer guide
- **File**: `docs/DEVELOPER_GUIDE.md`
- **Action**: For contributors:
  - Architecture overview
  - Adding new plot types
  - Customizing prompts
  - Extending tool functions

### Week 11: Optimization

**Task 5.6**: Caching strategy
- **Action**: Add caching for:
  - Generated plots (LRU cache)
  - Vision API responses (Redis/disk)
  - Embeddings (in-memory + disk)
- **Test**: Measure cache hit rates, latency improvements

**Task 5.7**: Parallel processing
- **Action**: Optimize batch processing:
  - Concurrent plot generation
  - Parallel vision API calls (rate-limited)
  - Async embedding generation
- **Target**: 2x throughput improvement

**Task 5.8**: Model selection
- **Action**: Add cost/quality tradeoffs:
  - Gemini 2.0 Flash: Ultra cost-effective batch ($0.10/$0.40 per M, ~$13 for 1300 sims)
  - Gemini 2.5 Flash: Balanced cost/performance ($0.30/$2.50 per M, ~$20 for 1300 sims) - **Recommended default**
  - Gemini 3 Pro Preview: Frontier quality ($2/$12 per M, ~$39 for 1300 sims) - Cutting-edge but preview/experimental
  - Claude Sonnet 4.5: Premium technical quality ($3/$15 per M, ~$52 for 1300 sims)
  - Gemini 2.5 Pro: Advanced reasoning ($1.25/$10 per M, ~$30 for 1300 sims)
  - Claude Opus 4.5: Highest frontier quality ($5/$25 per M, ~$78 for 1300 sims)
- **Implement**: Model routing based on use case and quality requirements
- **Strategy**: 
  - Use Gemini 2.5 Flash for production ingestion (fast, reliable, cost-effective)
  - Use Gemini 3 Pro Preview for quality validation on sample (cutting-edge)
  - Use Claude Sonnet 4.5 for critical/published results (premium reliability)
- **Test**: Compare quality metrics across models on same dataset
- **Monitor**: Track preview model stability and API changes

### Week 12: Launch Preparation

**Task 5.9**: Production deployment
- **Action**: Prepare for production:
  - Environment configuration
  - Monitoring and logging
  - Error alerting
  - Backup strategies

**Task 5.10**: User feedback system
- **Action**: Implement feedback collection:
  - Search result ratings
  - Description quality feedback
  - Feature requests
- **Purpose**: Continuous improvement

**Task 5.11**: Demo and training
- **Action**: Prepare:
  - Live demo notebook
  - Video tutorials
  - Workshop materials
- **Audience**: ITER researchers

## Success Criteria

### Phase 1 Complete When:
- ✅ Vision model analyzes sample plot with tool calls
- ✅ Tools return accurate numerical data
- ✅ End-to-end test passes for one simulation

### Phase 2 Complete When:
- ✅ Standard atomic plots generated for all IDS types (waveforms, profiles, equilibrium, spectrograms)
- ✅ Multi-panel layouts provide comprehensive diagnostic views
- ✅ Vision descriptions are technically accurate
- ✅ Batch processing handles 100 sims successfully
- ✅ Cost per simulation:
  - <$0.02 (Gemini 2.5 Flash - production target)
  - <$0.04 (Gemini 3 Pro Preview - frontier option)
  - <$0.05 (Claude Sonnet 4.5 - premium quality)

### Phase 3 Complete When:
- ✅ Multi-modal search returns relevant results
- ✅ 1300 SimDB simulations ingested
- ✅ Text, image, and hybrid search all functional

### Phase 4 Complete When:
- ✅ Users can refine searches interactively
- ✅ Results include explanations
- ✅ Validation metrics meet targets (TBD in testing)

### Phase 5 Complete When:
- ✅ CLI tools deployed and documented
- ✅ User guide and API docs complete
- ✅ Performance targets met
- ✅ Ready for production use

## Risk Management

### High Risk Items
1. **Vision model hallucination**: Mitigated by tool calling for numerical precision
2. **API costs exceed budget**: Mitigated by caching, model selection, batch discounts
3. **Search relevance issues**: Mitigated by hybrid scoring, user feedback

### Dependencies
- OpenRouter API availability
- IMAS data access
- ChromaDB stability

### Rollback Plan
If vision-first doesn't meet quality targets:
- Fall back to numerical-first with vision as optional enhancement
- Use vision only for search, not primary descriptions
- Hybrid approach: vision + template-based descriptions

## Next Steps

1. **Review this plan** with team
2. **Set up project tracking** (GitHub Issues/Projects)
3. **Begin Week 1, Task 1.1**: Add vision config to settings
4. **Schedule weekly reviews** to assess progress

---

**Ready to start**: All prerequisites met, architecture defined, tasks scoped.
