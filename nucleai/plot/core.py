import altair as alt
import xarray as xr


def plot_timeseries(
    data: xr.DataArray,
    title: str,
    xlabel: str = "Time (s)",
    ylabel: str = "Value",
    color: str = "#1f77b4",
) -> alt.Chart:
    """Create a time series plot from an xarray DataArray.

    Args:
        data: xarray DataArray with a single dimension (time).
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        color: Line color.

    Returns:
        Altair Chart object.
    """
    if len(data.dims) != 1:
        raise ValueError("Data must be 1D for time series plot")

    time_dim = data.dims[0]
    data_df = data.to_dataframe(name="value").reset_index()
    data_df = data_df.rename(columns={time_dim: "time"})

    return (
        alt.Chart(data_df)
        .mark_line(color=color)
        .encode(
            x=alt.X("time", title=xlabel),
            y=alt.Y("value", title=ylabel),
            tooltip=["time", "value"],
        )
        .properties(width=600, height=400, title=title)
        .configure_view(strokeWidth=0)
    )


def serve_plot(chart: alt.Chart) -> None:
    """Serve the chart via a local HTTP server.

    Args:
        chart: Altair Chart to serve.
    """
    import http.server
    import socketserver
    import webbrowser
    from pathlib import Path

    filename = "plot.html"
    chart.save(filename)

    port = 8082
    handler = http.server.SimpleHTTPRequestHandler

    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"Serving at http://localhost:{port}/{filename}")
            webbrowser.open(f"http://localhost:{port}/{filename}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServer stopped.")
                Path(filename).unlink()
    except OSError:
        print(f"Port {port} is in use. Please try again later.")
