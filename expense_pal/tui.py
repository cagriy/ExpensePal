from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, Select


class ReviewApp(App):
    """TUI for reviewing and editing extracted receipt data before saving."""

    CSS = """
    Screen {
        align: center middle;
    }

    #form {
        width: 70;
        height: auto;
        border: round $primary;
        padding: 1 2;
    }

    .field-row {
        height: auto;
        margin-bottom: 1;
    }

    Label {
        width: 20;
        padding-top: 1;
    }

    Input {
        width: 1fr;
    }

    Select {
        width: 1fr;
    }

    #buttons {
        margin-top: 1;
        height: auto;
        align: right middle;
    }

    Button {
        margin-left: 1;
    }
    """

    def __init__(self, extracted_data: dict, categories: list[dict]):
        super().__init__()
        self.extracted_data = extracted_data
        self.categories = categories
        self.result: dict | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)

        llm_category = self.extracted_data.get("category", "")
        select_options = [(cat["description"], cat["description"]) for cat in self.categories]
        initial_value = llm_category if any(v == llm_category for _, v in select_options) else Select.BLANK

        with Container(id="form"):
            yield Label("Review Extracted Receipt Data", id="title")
            with Horizontal(classes="field-row"):
                yield Label("Date:")
                yield Input(value=self.extracted_data.get("date", ""), id="date", placeholder="YYYY-MM-DD")
            with Horizontal(classes="field-row"):
                yield Label("Total Amount:")
                yield Input(value=self.extracted_data.get("total_amount", ""), id="total_amount", placeholder="0.00")
            with Horizontal(classes="field-row"):
                yield Label("VAT Amount:")
                yield Input(value=self.extracted_data.get("vat_amount", "0.00"), id="vat_amount", placeholder="0.00")
            with Horizontal(classes="field-row"):
                yield Label("Description:")
                yield Input(value="Sample Expense", id="description", placeholder="Enter description...")
            with Horizontal(classes="field-row"):
                yield Label("Category:")
                yield Select(select_options, value=initial_value, id="category")
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="default", id="cancel")
                yield Button("Confirm", variant="primary", id="confirm")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            category_widget = self.query_one("#category", Select)
            selected_category = category_widget.value
            if selected_category is Select.BLANK:
                selected_category = ""

            self.result = {
                "date": self.query_one("#date", Input).value.strip(),
                "total_amount": self.query_one("#total_amount", Input).value.strip(),
                "vat_amount": self.query_one("#vat_amount", Input).value.strip(),
                "description": self.query_one("#description", Input).value.strip(),
                "category": selected_category,
            }
            self.exit(self.result)
        elif event.button.id == "cancel":
            self.exit(None)
