from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from wheel_doctor.wheel import parse_dependencies, read_metadata, update_dependencies

_app = typer.Typer(help="Manipulate METADATA in python wheels and tarballs")
console = Console()


_NONE_VERSION = "<none>"


@_app.command()
def show_dependencies(wheels: list[Path]) -> None:
    """Display dependency METADATA in a wheel/tarball"""
    for file in wheels:
        console.print(f"{file}", style="bold")

        metadata = read_metadata(file)
        dependencies = parse_dependencies(metadata)
        _print_dependencies(dependencies)


@_app.command()
def replace_dependency_version(
    wheels: list[Path],
    dependency_name: str,
    version: str,
    verbose: Annotated[bool, typer.Option("--verbose")] = False,
) -> None:
    """Replace a specific version pin of a dependency in wheel/tarball METADATA"""
    for file in wheels:
        metadata = read_metadata(file)
        dependencies = parse_dependencies(metadata)
        if dependency_name not in dependencies:
            raise ValueError(f"Dependency {dependency_name} not found in wheel {file}!")

        new_version = None if not version or version == _NONE_VERSION else version
        if verbose:
            console.print(f"{file}", style="bold")
            console.print(
                f"Updating dependency {dependency_name}: "
                f"Replacing version '{dependencies[dependency_name] or _NONE_VERSION}' "
                f"with version '{new_version or _NONE_VERSION}'"
            )

        dependencies[dependency_name] = new_version

        update_dependencies(file, dependencies)

        if verbose:
            console.print("Updated dependencies:", style="bold")
            _print_dependencies(parse_dependencies(read_metadata(file)))


@_app.command()
def remove_path_dependencies(
    wheels: list[Path],
    verbose: Annotated[bool, typer.Option("--verbose")] = False,
) -> None:
    """Replace a specific version pin of a dependency in wheel/tarball METADATA"""
    for file in wheels:
        metadata = read_metadata(file)
        dependencies = parse_dependencies(metadata)

        if verbose:
            console.print(f"{file}", style="bold")

        for dependency, version in dependencies.items():
            if version is not None and "@" in version:
                dependencies[dependency] = None
                if verbose:
                    console.print(f"{dependency}: Removing path dependency '{version}'")

        update_dependencies(file, dependencies)

        if verbose:
            console.print("Updated dependencies:", style="bold")
            _print_dependencies(parse_dependencies(read_metadata(file)))


def _print_dependencies(dependencies: dict[str, str | None]) -> None:
    table = Table("Dependency", "Version")
    for dependency, version in dependencies.items():
        table.add_row(dependency, version or Text(_NONE_VERSION, style="#777777"))
    console.print(table)


if __name__ == "__main__":
    _app()
