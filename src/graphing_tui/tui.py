import asteval
import libcst as cst
import numpy as np
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.validation import ValidationResult, Validator
from textual.widgets import Input, Label
from textual_plot import HiResMode, PlotWidget


class GraphingApp(App[None]):
    CSS_PATH = "tui.tcss"
    AUTO_FOCUS = "#expression"

    _expression: str | None = None
    _parameters: set = set()

    def compose(self) -> ComposeResult:
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

    @on(Input.Changed)
    def parse_expression(self, event: Input.Changed) -> None:
        if event.validation_result.is_valid:
            self._expression = event.value
            undefined = self.get_undefined_variables(self._expression) - {"x"}
            new = undefined - self._parameters
            outdated = self._parameters - undefined
            self._parameters = undefined
            if new:
                self.notify(f"New parameters found: {new}")
            if outdated:
                self.notify(f"Outdated parameters removed: {outdated}")
        else:
            self._expression = None
        self.update_plot()

    @on(PlotWidget.ScaleChanged)
    def update_plot(self) -> None:
        if self._expression is not None:
            plot = self.query_one(PlotWidget)
            plot.clear()
            x = np.linspace(plot._x_min, plot._x_max, 101)
            aeval = asteval.Interpreter(usersyms={"x": x})
            y = aeval(self._expression)
            # if not isinstance(y, np.ndarray):
            #     y = np.full_like(x, fill_value=y)
            # plot.plot(x, y, hires_mode=HiResMode.BRAILLE)

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


if __name__ == "__main__":
    GraphingApp().run()
