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
            plot = self.query_one(PlotWidget)
            plot.clear()
            x = np.linspace(plot._x_min, plot._x_max, 101)
            aeval = asteval.Interpreter(usersyms={"x": x})
            y = aeval(event.value)
            if not isinstance(y, np.ndarray):
                y = np.full_like(x, fill_value=y)
            plot.plot(x, y, hires_mode=HiResMode.BRAILLE)


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
