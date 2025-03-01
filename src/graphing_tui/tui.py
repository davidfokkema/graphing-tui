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
    @dataclass
    class Changed(Message):
        parameter: str
        value: float

    value: reactive[float] = reactive(1.0, init=False)

    def compose(self) -> ComposeResult:
        yield Label(self.name)
        yield Input(str(self.value), validate_on=["changed"], validators=[Number()])

    @on(Input.Changed)
    def update_value(self, event: Input.Changed) -> None:
        event.stop()
        if event.validation_result.is_valid:
            self.value = float(event.value)

    def watch_value(self, value: float) -> None:
        self.post_message(self.Changed(parameter=self.name, value=value))


class GraphingApp(App[None]):
    CSS_PATH = "tui.tcss"
    AUTO_FOCUS = "#expression"

    _expression: str | None = None
    _parameters: set = set()

    def compose(self) -> ComposeResult:
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
        plot = self.query_one(PlotWidget)
        plot.set_xlimits(-10, 10)
        plot.set_ylimits(-10, 10)

    @on(Input.Changed)
    def parse_expression(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            self._expression = event.value
            undefined = self.get_undefined_variables(self._expression) - {"x"}
            new = undefined - self._parameters
            outdated = self._parameters - undefined
            self._parameters = undefined
            if new:
                for parameter in new:
                    self.add_parameter(parameter)
            if outdated:
                for parameter in outdated:
                    self.remove_parameter(parameter)
        else:
            self._expression = None
        self.update_plot()

    def add_parameter(self, parameter: str) -> None:
        parameters = self.query_one("#parameters", VerticalScroll)
        parameters.mount(Parameter(name=parameter, id=parameter))

    def remove_parameter(self, parameter: str) -> None:
        parameters = self.query_one("#parameters", VerticalScroll)
        widget = parameters.query_children("#" + parameter).first()
        widget.remove()

    @on(PlotWidget.ScaleChanged)
    @on(Parameter.Changed)
    def update_plot(self) -> None:
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
        """
        Get a set of undefined variables in the given expression.

        This method uses libcst to parse the expression and collect all symbols.
        It then filters out any symbols that are predefined in the asteval symbol table.

        Args:
            expression (str): The mathematical expression to evaluate.

        Returns:
            set: A set of undefined variable names found in the expression.
        """

        class SymbolCollector(cst.CSTVisitor):
            def __init__(self):
                self.symbols = set()

            def visit_Name(self, node: cst.Name) -> None:
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
    def validate(self, value: str) -> ValidationResult:
        try:
            cst.parse_expression(value)
        except cst.ParserSyntaxError:
            return self.failure()
        else:
            return self.success()


# for textual run
app = GraphingApp


def main():
    GraphingApp().run()


if __name__ == "__main__":
    main()
