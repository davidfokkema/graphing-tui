import asteval
import libcst as cst
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.validation import ValidationResult, Validator
from textual.widgets import Input
from textual_plot import PlotWidget


class GraphingApp(App[None]):
    CSS_PATH = "tui.tcss"

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield PlotWidget()
            with Vertical():
                yield Input(
                    placeholder="Type function here",
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


GraphingApp().run()
