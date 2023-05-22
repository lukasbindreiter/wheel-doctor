"""Utility functions for working with and modifying zip wheels and tar.gz tarballs"""
import re
import shutil
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from zipfile import ZipFile

import tomli
import tomli_w

_DEPENDENCY_PATTERN = re.compile(
    r"(Requires-Dist: )(?P<package>[^ ]+) ?(?P<version>.*)"
)


def unpack(archive: Path, target_directory: Path) -> None:
    """Unpack the given wheel or tarball into the given directory

    Args:
        archive: Archive (.whl or .zip) or tarball (.tar.gz) to unpack
        target_directory: Directory to unpack it to
    """
    target_directory.mkdir(exist_ok=True, parents=True)
    shutil.unpack_archive(
        archive, target_directory, format="zip" if archive.suffix == ".whl" else None
    )


def pack(directory: Path, archive: Path) -> None:
    """Pack the given directory into a wheel or tarball

    Args:
        directory: The directory to pack into an archive
        archive: The archive file to create. The suffix of this file will determine
            the format. Supported are .zip and .whl for zip files, and .tar.gz for
            a gzipped tarball.
    """
    if archive.suffix == ".whl":
        created_archive = Path(
            shutil.make_archive(archive.with_suffix("").as_posix(), "zip", directory),
        )
    elif archive.suffixes[-2:] == [".tar", ".gz"]:
        basename = archive.with_suffix("").with_suffix("")
        created_archive = Path(
            shutil.make_archive(basename.as_posix(), "gztar", directory, basename.name)
        )
    else:
        raise ValueError("Refusing to pack into non-wheel or tarball format")

    if created_archive.resolve().absolute() != archive.resolve().absolute():
        created_archive.rename(archive)


def read_metadata(package: Path) -> str:
    """Read the METADATA file of a python package wheel (.whl) or tarball (.tar.gz)"""
    if package.suffix != ".whl" and package.suffixes[-2:] != [".tar", ".gz"]:
        raise ValueError(f"Invalid python package {package}. Expected .whl or .tar.gz")

    if package.suffix == ".whl":
        return _read_metadata_from_wheel(package)

    return _read_metadata_from_tarball(package)


def parse_dependencies(metadata: str) -> dict[str, str | None]:
    """Parse dependencies from a python package METADATA string

    Args:
        metadata: The contents of the METADATA file in a python package

    Returns:
        Mapping of dependency name to its version
    """
    dependencies = {}
    for line in metadata.splitlines():
        if match := _DEPENDENCY_PATTERN.match(line):
            dependencies[match.group("package")] = match.group("version") or None
    return dependencies


def update_dependencies(package: Path, dependencies: dict[str, str | None]) -> None:
    with TemporaryDirectory() as tmp_dir:
        extracted = Path(tmp_dir)
        unpack(package, extracted)

        # search for the metadata file, which is present in all cases
        metadata_files = list(extracted.glob("*.dist-info/METADATA")) + list(
            extracted.glob("*/PKG-INFO")
        )
        if len(metadata_files) != 1:
            raise ValueError(f"{package} is not a valid python wheel/tarball")
        update_dependencies_in_metadata_file(metadata_files[0], dependencies)

        pyproject_toml = list(extracted.glob("*/pyproject.toml"))
        if pyproject_toml:
            update_dependencies_in_pyproject_toml_file(pyproject_toml[0], dependencies)

        package.unlink()
        pack(extracted, package)


def update_dependencies_in_metadata_file(
    metadata: Path, dependencies: dict[str, str | None]
) -> None:
    metadata.write_text(
        update_dependencies_in_metadata(metadata.read_text(), dependencies)
    )


def update_dependencies_in_metadata(
    metadata: str, dependencies: dict[str, str | None]
) -> str:
    lines = metadata.splitlines()
    for i in range(len(lines)):
        if match := _DEPENDENCY_PATTERN.match(lines[i]):
            name = match.group("package")
            version = dependencies.get(name, match.group("version"))
            if version:
                lines[i] = f"Requires-Dist: {name} {version}"
            else:
                lines[i] = f"Requires-Dist: {name}"
    return "\n".join(lines)


def update_dependencies_in_pyproject_toml_file(
    pyproject_toml: Path, dependencies: dict[str, str | None]
) -> None:
    pyproject_toml.write_text(
        update_dependencies_in_pyproject_toml(pyproject_toml.read_text(), dependencies)
    )


def update_dependencies_in_pyproject_toml(
    toml: str, dependencies: dict[str, str | None]
) -> str:
    project = tomli.loads(toml)

    def _recurse(toml_node: dict[str, Any]) -> None:
        for key, value in toml_node.items():
            if key == "dependencies":
                for dependency in value:
                    if dependency in dependencies:
                        value[dependency] = dependencies[dependency] or "*"
            elif isinstance(value, dict):
                _recurse(value)

    _recurse(project)
    return tomli_w.dumps(project)


def _read_metadata_from_wheel(wheel: Path) -> str:
    zip_file = ZipFile(wheel)
    archive_contents = zip_file.namelist()
    metadata_files = [
        name for name in archive_contents if name.endswith(".dist-info/METADATA")
    ]
    if len(metadata_files) != 1:
        raise ValueError(f"{wheel} is not a valid python wheel/tarball")

    metadata_filename = metadata_files[0]
    return zip_file.read(metadata_filename).decode("utf-8")


def _read_metadata_from_tarball(tarball: Path) -> str:
    with tarfile.open(tarball, "r:gz") as tar_file:
        if tar_file is None:
            raise OSError(f"Failed to open tarball {tarball}")

        archive_contents = tar_file.getnames()
        metadata_files = [
            name for name in archive_contents if name.endswith("/PKG-INFO")
        ]
        if len(metadata_files) != 1:
            raise ValueError(f"{tarball} is not a valid python wheel/tarball")

        metadata_filename = metadata_files[0]
        extracted = tar_file.extractfile(metadata_filename)
        if extracted is None:
            raise OSError(
                f"Failed to read metadata {metadata_filename} from tarball {tarball}"
            )

        return extracted.read().decode("utf-8")
