# Plotting Style Guidelines

## Core Principles
1.  **Maximize Data-to-Ink Ratio**: Remove unnecessary grid lines, borders, and backgrounds. Every pixel should convey information.
2.  **Scientific Precision**: Use clear, descriptive titles and axis labels with units.
3.  **Consistent Styling**: Use a unified color palette and font hierarchy.
4.  **Serve, Don't Save**: Always serve plots via a local server (localhost) for immediate viewing. Do not save static files unless explicitly requested.

## Technical Rules
-   **Library**: Use `vega-altair` for all plotting.
-   **Input**: Plotting functions must accept `xarray.DataArray` or `xarray.Dataset` objects.
-   **Output**: Plotting functions must return `altair.Chart` objects.
-   **Serving**: Use `nucleai.plot.serve_plot` to display charts.

## Style Specs
-   **Background**: White (transparent if possible/appropriate).
-   **Grid**: Minimal or none. If used, light gray and dashed.
-   **Colors**: Use the `nucleai` corporate palette (to be defined in `nucleai.plot.style`).
-   **Fonts**: Sans-serif (e.g., Helvetica, Arial) for readability.
