import typer

from cambium import config
from cambium.tree import TreeSpan

app = typer.Typer()


@app.command()
def main():

    config.initialize_configuration()

    treespan = TreeSpan()
    treespan.transform()
    treespan.finalize()
