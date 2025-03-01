# Graphing TUI

Graphing TUI is a terminal-based user interface application for graphing mathematical functions, written in Python using the excellent [Textual](https://www.textualize.io/) framework. It provides an intuitive and interactive way to visualize and manipulate function graphs directly from the command line. The app automatically determines the parameters in the expression, displays them prominently, and lets you easily change their values.

## Features

- Graph mathematical functions
- Automatically detect and display parameters
- Easily adjust parameter values
- Interactive user interface
- Mouse support for zooming and panning the plot

## Screenshots

![screenshot of a periodic function](docs/images/screenshot-periodic-function.png)

![video demo of graphing-tui](https://github.com/user-attachments/assets/1933bfcb-8647-489d-8b45-540ec3bb5f7d)

## Run without installation

To run Graphing TUI without installing it first, use `uvx` or `pipx`:

## Running the demo / installation

Using [uv](https://astral.sh/uv/):
```console
uvx graphing-tui
```

Using [pipx](https://pipx.pypa.io/):
```console
pipx run graphing-tui
```

Install the package with either
```console
uv tool install graphing-tui
```
or
```console
pipx install graphing-tui
```
Alternatively, install the package with `pip` (please, use virtual environments) and run the demo:
```console
pip install graphing-tui
```

## Usage

Run the application with:

```console
graphing-tui
```

Type an expression in the input box, change the values of any parameters and use your mousewheel to zoom the plot or click and drag for panning.

## License

This project is licensed under the MIT License.
