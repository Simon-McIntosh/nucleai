"""Main CLI entrypoint for nucleai.

Commands:
    build-db: Fetch simulations from SimDB and populate local DuckDB and ChromaDB.
"""

import asyncio

import typer
from rich.console import Console
from rich.progress import Progress

from nucleai.db.manager import init_db, upsert_simulations
from nucleai.embeddings.text import generate_text_embedding
from nucleai.search.vector_store import ChromaDBVectorStore
from nucleai.simdb import query

app = typer.Typer()
console = Console()


@app.command()
def build_db(
    limit: int = typer.Option(2000, help="Maximum number of simulations to fetch"),
    rebuild: bool = typer.Option(False, help="Rebuild database from scratch"),
) -> None:
    """Fetch simulations from SimDB and populate local database.

    Downloads simulation metadata from SimDB and:
    1. Stores structured data in local DuckDB (SQL)
    2. Generates embeddings and stores in ChromaDB (Semantic Search)
    """
    asyncio.run(_build_db_async(limit, rebuild))


async def _build_db_async(limit: int, rebuild: bool) -> None:
    """Async implementation of build-db."""
    console.print(f"[bold blue]Starting SimDB sync (limit={limit})...[/bold blue]")

    # 1. Initialize DB
    # 1. Initialize DB
    if rebuild:
        console.print("[yellow]Rebuilding database...[/yellow]")
        from nucleai.db.manager import DuckDBManager

        manager = DuckDBManager()
        conn = manager.get_connection()
        conn.execute("DROP TABLE IF EXISTS simulations")
        conn.close()

        # Also clear ChromaDB
        store = ChromaDBVectorStore()
        # ChromaDB doesn't have a clean drop method exposed easily via our wrapper,
        # but we can rely on upsert overwriting or implement delete_all later.
        # For now, just dropping SQL table is a good start.

    init_db()

    # 2. Fetch from SimDB
    with Progress() as progress:
        task = progress.add_task("[cyan]Fetching from SimDB...", total=None)
        sims = await query(limit=limit)
        progress.update(task, completed=len(sims), total=len(sims))
        console.print(f"[green]Fetched {len(sims)} simulations.[/green]")

    # 3. Upsert to DuckDB
    with Progress() as progress:
        task = progress.add_task("[cyan]Updating DuckDB...", total=len(sims))
        upsert_simulations(sims)
        progress.update(task, completed=len(sims))
        console.print("[green]DuckDB updated.[/green]")

    # 4. Update ChromaDB (Embeddings)
    console.print("[bold blue]Updating Semantic Search Index...[/bold blue]")
    store = ChromaDBVectorStore()

    with Progress() as progress:
        task = progress.add_task("[cyan]Generating embeddings...", total=len(sims))

        for sim in sims:
            # Construct text for embedding
            # Combine relevant fields for semantic search
            text_parts = [
                f"Machine: {sim.machine}",
                f"Code: {sim.code.name} {sim.code.version or ''}",
                f"Description: {sim.description}",
                f"Status: {sim.status}",
            ]
            if sim.metadata and sim.metadata.composition:
                comp = sim.metadata.composition
                text_parts.append(f"Composition: D={comp.deuterium}, T={comp.tritium}")

            text = ". ".join(text_parts)

            try:
                # Generate embedding
                embedding = await generate_text_embedding(text)

                # Store in ChromaDB
                metadata = {
                    "machine": sim.machine,
                    "code": sim.code.name,
                    "alias": sim.alias,
                    "uuid": sim.uuid,
                }
                await store.store(id=sim.uuid, embedding=embedding, metadata=metadata)

            except Exception as e:
                console.print(f"[red]Failed to embed {sim.alias}: {e}[/red]")

            progress.advance(task)

    console.print("[bold green]Sync Complete![/bold green]")


@app.command()
def status() -> None:
    """Check status of local database."""
    from nucleai.db.manager import DuckDBManager

    try:
        manager = DuckDBManager()
        conn = manager.get_connection()
        count = conn.execute("SELECT COUNT(*) FROM simulations").fetchone()[0]
        console.print(f"[green]Local database contains {count} simulations.[/green]")
        conn.close()
    except Exception as e:
        console.print(f"[red]Database error: {e}[/red]")
        console.print("[yellow]Try running 'nucleai build-db' first.[/yellow]")


if __name__ == "__main__":
    app()
