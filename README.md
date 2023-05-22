# wheel-doctor

Easily manipulate METADATA in python wheels and tarballs

## Intended purpose

The main goal of this tool is to remove references to other packages specified as path dependencies, which will be present in some cases (e.g. building packages in monorepos). Partially inspired by: https://gitlab.com/gerbenoostra/poetry-monorepo

## Usage

Show a table of dependencies specified in a package:

```
> wheel-doctor show-dependencies dist/package-1.0.0-py3-none-any.whl

┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dependency  ┃ Version                                                           ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ numpy       │ <none>                                                            │
│ loguru      │ <none>                                                            │
│ xarray      │ <none>                                                            │
│ my-package  │ @ file:///home/user/my-package                                    │
└─────────────┴───────────────────────────────────────────────────────────────────┘
```

Overwrite a specific dependency

```
> wheel-doctor replace-dependency-version dist/package-1.0.0-py3-none-any.whl my-package "" --verbose

dist/package-1.0.0-py3-none-any.whl
Updating dependency my-package: Replacing version '@ file:///home/user/my-package'
with version '<none>'
Updated dependencies:
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dependency  ┃ Version                                                           ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ numpy       │ <none>                                                            │
│ loguru      │ <none>                                                            │
│ xarray      │ <none>                                                            │
│ my-package  │ <none>                                                            │
└─────────────┴───────────────────────────────────────────────────────────────────┘
```

Removing all path dependencies

```
> wheel-doctor remove-path-dependencies dist/package-1.0.0-py3-none-any.whl my-package --verbose

dist/package-1.0.0-py3-none-any.whl
my-package: Removing path dependency '@ file:///home/user/my-package'
Updated dependencies:
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Dependency  ┃ Version                                                           ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ numpy       │ <none>                                                            │
│ loguru      │ <none>                                                            │
│ xarray      │ <none>                                                            │
│ my-package  │ <none>                                                            │
└─────────────┴───────────────────────────────────────────────────────────────────┘
```
