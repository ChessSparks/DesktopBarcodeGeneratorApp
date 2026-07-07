from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.db import delete_payer, get_connection, get_recipient_profile, list_payers
from app.models import build_slip, payer_from_row, recipient_from_row
from app.ui.payer_dialog import PayerDialog
from app.ui.recipient_dialog import RecipientDialog
from app.ui.slip_preview_dialog import SlipPreviewDialog

COLUMNS = [
    "ID", "Name", "Address", "Postcode & city", "Amount (EUR)",
    "Model", "Reference", "Purpose code", "Description",
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HUB3A Payment Slip Generator")
        self.resize(1100, 600)

        self.conn = get_connection()

        self._build_ui()
        self._refresh_table()
        QTimer.singleShot(0, self._maybe_prompt_recipient_setup)

    def _maybe_prompt_recipient_setup(self) -> None:
        row = get_recipient_profile(self.conn)
        if not row["name"].strip() or not row["iban"].strip():
            self._on_edit_recipient()

    def _build_ui(self) -> None:
        settings_menu = self.menuBar().addMenu("Settings")
        recipient_action = settings_menu.addAction("Recipient profile...")
        recipient_action.triggered.connect(self._on_edit_recipient)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._on_generate_slip)
        layout.addWidget(self.table)

        button_row = QHBoxLayout()
        add_btn = QPushButton("Add payer")
        add_btn.clicked.connect(self._on_add_payer)
        edit_btn = QPushButton("Edit payer")
        edit_btn.clicked.connect(self._on_edit_payer)
        delete_btn = QPushButton("Delete payer")
        delete_btn.clicked.connect(self._on_delete_payer)
        generate_btn = QPushButton("Generate slip")
        generate_btn.clicked.connect(self._on_generate_slip)

        button_row.addWidget(add_btn)
        button_row.addWidget(edit_btn)
        button_row.addWidget(delete_btn)
        button_row.addStretch(1)
        button_row.addWidget(generate_btn)
        layout.addLayout(button_row)

    def _refresh_table(self) -> None:
        rows = list_payers(self.conn)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                str(row["id"]),
                row["name"],
                row["address"],
                row["place"],
                f"{row['amount']:.2f}",
                row["model"],
                row["reference"],
                row["purpose_code"],
                row["description"],
            ]
            for col_index, value in enumerate(values):
                self.table.setItem(row_index, col_index, QTableWidgetItem(value))
        self._rows = rows

    def _selected_payer_id(self) -> int | None:
        selected = self.table.currentRow()
        if selected < 0 or selected >= len(self._rows):
            return None
        return self._rows[selected]["id"]

    def _on_edit_recipient(self) -> None:
        dialog = RecipientDialog(self.conn, self)
        dialog.exec()

    def _on_add_payer(self) -> None:
        dialog = PayerDialog(self.conn, parent=self)
        if dialog.exec():
            self._refresh_table()

    def _on_edit_payer(self) -> None:
        payer_id = self._selected_payer_id()
        if payer_id is None:
            QMessageBox.information(self, "No selection", "Select a payer to edit.")
            return
        dialog = PayerDialog(self.conn, payer_id=payer_id, parent=self)
        if dialog.exec():
            self._refresh_table()

    def _on_delete_payer(self) -> None:
        payer_id = self._selected_payer_id()
        if payer_id is None:
            QMessageBox.information(self, "No selection", "Select a payer to delete.")
            return
        confirm = QMessageBox.question(self, "Delete payer", "Delete the selected payer?")
        if confirm == QMessageBox.Yes:
            delete_payer(self.conn, payer_id)
            self._refresh_table()

    def _on_generate_slip(self) -> None:
        payer_id = self._selected_payer_id()
        if payer_id is None:
            QMessageBox.information(self, "No selection", "Select a payer to generate a slip for.")
            return

        recipient_row = get_recipient_profile(self.conn)
        recipient = recipient_from_row(recipient_row)
        if not recipient.name.strip() or not recipient.iban.strip():
            QMessageBox.warning(
                self, "Recipient not configured",
                "Set up your recipient profile first (Settings > Recipient profile...)."
            )
            return

        payer_row = next(row for row in self._rows if row["id"] == payer_id)
        payer = payer_from_row(payer_row)

        try:
            slip = build_slip(recipient, payer)
            slip.validate()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid data", str(exc))
            return

        dialog = SlipPreviewDialog(slip, parent=self)
        dialog.exec()
