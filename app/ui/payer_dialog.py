from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox

from app.db import get_payer, insert_payer, update_payer


class PayerDialog(QDialog):
    def __init__(self, conn, payer_id: int | None = None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.payer_id = payer_id
        self.setWindowTitle("Edit payer" if payer_id else "Add payer")
        self.resize(420, 340)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.place_edit = QLineEdit()
        self.amount_edit = QLineEdit()
        self.model_edit = QLineEdit()
        self.reference_edit = QLineEdit()
        self.purpose_code_edit = QLineEdit()
        self.description_edit = QLineEdit()

        layout.addRow("Name", self.name_edit)
        layout.addRow("Address", self.address_edit)
        layout.addRow("Postcode && city", self.place_edit)
        layout.addRow("Amount (EUR)", self.amount_edit)
        layout.addRow("Model", self.model_edit)
        layout.addRow("Reference (poziv na broj)", self.reference_edit)
        layout.addRow("Purpose code (šifra namjene)", self.purpose_code_edit)
        layout.addRow("Description", self.description_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if payer_id is not None:
            self._load(payer_id)
        else:
            self.model_edit.setText("HR00")

    def _load(self, payer_id: int) -> None:
        row = get_payer(self.conn, payer_id)
        self.name_edit.setText(row["name"])
        self.address_edit.setText(row["address"])
        self.place_edit.setText(row["place"])
        self.amount_edit.setText(f"{row['amount']:.2f}")
        self.model_edit.setText(row["model"] or "HR00")
        self.reference_edit.setText(row["reference"])
        self.purpose_code_edit.setText(row["purpose_code"])
        self.description_edit.setText(row["description"])

    def _on_save(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Invalid data", "Name is required")
            return

        amount_text = self.amount_edit.text().strip().replace(",", ".")
        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid data", f"Invalid amount: {amount_text!r}")
            return
        if amount <= 0:
            QMessageBox.warning(self, "Invalid data", "Amount must be greater than 0")
            return

        args = (
            self.name_edit.text().strip(),
            self.address_edit.text().strip(),
            self.place_edit.text().strip(),
            amount,
            self.model_edit.text().strip() or "HR00",
            self.reference_edit.text().strip(),
            self.purpose_code_edit.text().strip(),
            self.description_edit.text().strip(),
        )
        if self.payer_id is None:
            insert_payer(self.conn, *args)
        else:
            update_payer(self.conn, self.payer_id, *args)
        self.accept()
