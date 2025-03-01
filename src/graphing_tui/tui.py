"""The Textual User Interface (TUI) for a graphing application.

The application allows users to input mathematical expressions and dynamically
plot them. It includes functionality for handling parameters within the
expressions and updating the plot based on user input and changes in the plot
scale.
"""

from dataclasses import dataclass

import asteval
import libcst as cst
import numpy as np
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.validation import Number, ValidationResult, Validator
from textual.widgets import Footer, Header, Input, Label
from textual_plot import HiResMode, PlotWidget


class Parameter(Horizontal):
    """A class representing a parameter input widget.

    This class creates a horizontal container with a label and an input field.
    The input field validates the value as a number and updates the parameter
    value.
    """

    @dataclass
    class Changed(Message):
        """A message class representing a change in the parameter value.

        Attributes:
            parameter: The name of the parameter.
            value: The new value of the parameter.
        """

        parameter: str
        value: float

    value: reactive[float] = reactive(1.0, init=False)

    def compose(self) -> ComposeResult:
        """Compose the child widgets of the parameter.

        Yields:
            The label and input field for the parameter.
        """
        yield Label(self.name)
        yield Input(str(self.value), validate_on=["changed"], validators=[Number()])

    @on(Input.Changed)
    def update_value(self, event: Input.Changed) -> None:
        """Update the parameter value when the input value changes.

        Args:
            event: The input changed event.
        """
        event.stop()
        if event.validation_result.is_valid:
            self.value = float(event.value)

    def watch_value(self, value: float) -> None:
        """Post a message when the parameter value changes.

        Args:
            value: The new value of the parameter.
        """
        self.post_message(self.Changed(parameter=self.name, value=value))


class GraphingApp(App[None]):
    """The main application class for the graphing TUI.

    This class creates the user interface for plotting mathematical expressions.
    """

    CSS_PATH = "tui.tcss"
    AUTO_FOCUS = "#expression"

    _expression: str | None = None
    _parameters: set = set()

    def compose(self) -> ComposeResult:
        """Compose the child widgets of the application.

        Yields:
            The header, footer, plot widget, and input fields.
        """
        yield Header()
        yield Footer()
        with Horizontal():
            yield PlotWidget()
            with Vertical():
                yield Label("Expression:")
                yield Input(
                    placeholder="Type expression",
                    id="expression",
                    validate_on=["changed"],
                    validators=ExpressionValidator(),
                )
                yield VerticalScroll(id="parameters")

    def on_mount(self) -> None:
        """Set the initial plot limits when the application mounts."""
        plot = self.query_one(PlotWidget)
        plot.set_xlimits(-10, 10)
        plot.set_ylimits(-10, 10)

    @on(Input.Changed)
    def parse_expression(self, event: Input.Changed) -> None:
        """Parse the mathematical expression when the input value changes.

        Args:
            event: The input changed event.
        """
        if event.validation_result.is_valid:
            self._expression = event.value
            all_parameters = self.get_undefined_variables(self._expression) - {"x"}
            new = all_parameters - self._parameters
            outdated = self._parameters - all_parameters
            self._parameters = all_parameters
            for parameter in new:
                self.add_parameter(parameter)
            for parameter in outdated:
                self.remove_parameter(parameter)
        else:
            self._expression = None
        self.update_plot()

    def add_parameter(self, parameter: str) -> None:
        """Add a new parameter input field.

        Args:
            parameter: The name of the parameter.
        """
        parameters = self.query_one("#parameters", VerticalScroll)
        parameters.mount(Parameter(name=parameter, id=parameter))

    def remove_parameter(self, parameter: str) -> None:
        """Remove an existing parameter input field.

        Args:
            parameter: The name of the parameter.
        """
        parameters = self.query_one("#parameters", VerticalScroll)
        widget = parameters.query_children("#" + parameter).first()
        widget.remove()

    @on(PlotWidget.ScaleChanged)
    @on(Parameter.Changed)
    def update_plot(self) -> None:
        """Update the plot when the scale or parameter values change."""
        if self._expression is not None:
            plot = self.query_one(PlotWidget)
            plot.clear()
            x = np.linspace(plot._x_min, plot._x_max, 101)
            symbols = {"x": x}
            for parameter in self.query(Parameter):
                symbols[parameter.name] = parameter.value
            aeval = asteval.Interpreter(usersyms=symbols)
            y = aeval(self._expression)
            if np.isscalar(y):
                # if you don't include 'x', y will be a scalar
                y = np.full_like(x, fill_value=y)
            if not isinstance(y, np.ndarray):
                return
            if np.isfinite(y).any():
                # there are finite values to plot
                plot.plot(x, y, hires_mode=HiResMode.BRAILLE)

    def get_undefined_variables(self, expression: str) -> set:
        """Get a set of undefined variables in the given expression.

        This method uses libcst to parse the expression and collect all symbols.
        It then filters out any symbols that are predefined in the asteval symbol table.

        Args:
            expression: The mathematical expression to evaluate.

        Returns:
            A set of undefined variable names found in the expression.
        """

        class SymbolCollector(cst.CSTVisitor):
            """A visitor class for collecting symbols in a parsed expression."""

            def __init__(self):
                self.symbols = set()

            def visit_Name(self, node: cst.Name) -> None:
                """Collect the name of a symbol.

                Args:
                    node: The CST node representing a symbol name.
                """
                self.symbols.add(node.value)

        # Parse the expression and collect all symbols
        tree = cst.parse_expression(expression)
        collector = SymbolCollector()
        tree.visit(collector)

        # Predefined symbols in asteval
        predefined_symbols = set(asteval.Interpreter().symtable.keys())

        # Filter out predefined symbols
        undefined_symbols = collector.symbols - predefined_symbols

        return undefined_symbols


class ExpressionValidator(Validator):
    """A validator class for validating mathematical expressions.

    This class uses the `libcst` library to parse the expression and check for syntax errors.
    If the expression is valid, it returns a success result; otherwise, it returns a failure result.
    """

    def validate(self, value: str) -> ValidationResult:
        """Validate the given expression.

        Args:
            value: The mathematical expression to validate.

        Returns:
            The result of the validation, indicating success or failure.
        """
        try:
            cst.parse_expression(value)
        except cst.ParserSyntaxError:
            return self.failure()
        else:
            return self.success()


# for textual run
app = GraphingApp


def main():
    """The main entry point for running the GraphingApp.

    This function initializes and runs the GraphingApp using the Textual framework.
    """
    GraphingApp().run()


if __name__ == "__main__":
    main()
