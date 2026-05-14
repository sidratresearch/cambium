import typer

from cambium.tree import TreeSpan

app = typer.Typer()


@app.command()
def main():
    treespan = TreeSpan()
    treespan.transform()
    treespan.finalize()
