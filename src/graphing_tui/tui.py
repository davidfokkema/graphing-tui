import asteval
import libcst as cst
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.validation import ValidationResult, Validator
from textual.widgets import Input, Label
from textual_plot import PlotWidget


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
