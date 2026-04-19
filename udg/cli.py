import sys
import click
from pathlib import Path
from udg import __version__
from udg.auth.token import load_token, rotate_token, generate_token
from udg.config import settings

@click.group()
def cli():
    pass

@cli.command()
def version():
    click.echo(__version__)

@cli.command()
def start():
    click.echo("Starting udg server...")

@cli.command()
def token_show():
    token = load_token(settings.token_file)
    click.echo(f"Current token: {token[:8]}...")

@cli.command()
def token_rotate():
    new_token = rotate_token(settings.token_file)
    click.echo(f"New token: {new_token}")

@cli.command()
def device_list():
    click.echo("Devices: []")

if __name__ == "__main__":
    cli()