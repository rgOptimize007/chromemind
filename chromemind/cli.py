import asyncio
import click
from agents.orchestrator import OrchestratorAgent

@click.group()
def cli():
    """ChromeMind — Agentic Browser Knowledge Curator."""
    pass

@cli.command()
@click.option('--source', type=click.Choice(['bookmarks', 'history', 'tabs', 'all']), default=None, help='Source to scrape.')
@click.option('--limit', type=int, default=None, help='Max items per source.')
@click.option('--dry-run/--no-dry-run', default=None, help='Skip writing to Notion.')
@click.option('--enrich/--no-enrich', default=True, help='Enable/disable LLM enrichment.')
def run(source, limit, dry_run, enrich):
    """Run the ChromeMind pipeline."""
    mode = "enrich + write" if enrich else "scrape + write (no enrichment)"
    click.echo(f"Starting ChromeMind pipeline... [{mode}]")

    report = asyncio.run(OrchestratorAgent.run(
        source_override=source,
        limit_override=limit,
        dry_run_override=dry_run,
        enrich=enrich
    ))

    click.echo("\nRun Summary:")
    click.echo(f"  Created: {report.created}")
    click.echo(f"  Updated: {report.updated}")
    click.echo(f"  Skipped: {report.skipped}")

    if report.failed:
        click.echo(f"  Failed : {len(report.failed)}")
        for f in report.failed:
            reason = f.get('reason', 'Unknown').encode('ascii', 'replace').decode('ascii')
            click.echo(f"    - {f['id'][:12]}...: {reason[:120]}")

if __name__ == "__main__":
    cli()
