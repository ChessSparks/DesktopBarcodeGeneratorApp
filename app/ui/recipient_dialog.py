from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox

from app.db import get_recipient_profile, save_recipient_profile


class RecipientDialog(QDialog):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle("Recipient settings")
        self.resize(420, 220)

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.place_edit = QLineEdit()
        self.iban_edit = QLineEdit()

        layout.addRow("Name", self.name_edit)
        layout.addRow("Address", self.address_edit)
        layout.addRow("Postcode && city", self.place_edit)
        layout.addRow("IBAN", self.iban_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self._load()

    def _load(self) -> None:
        row = get_recipient_profile(self.conn)
        self.name_edit.setText(row["name"])
        self.address_edit.setText(row["address"])
        self.place_edit.setText(row["place"])
        self.iban_edit.setText(row["iban"])

    def _on_save(self) -> None:
        iban = self.iban_edit.text().replace(" ", "")
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Invalid data", "Recipient name is required")
            return
        if not iban.upper().startswith("HR"):
            QMessageBox.warning(self, "Invalid data", "IBAN must be a Croatian IBAN starting with HR")
            return

        save_recipient_profile(
            self.conn,
            name=self.name_edit.text().strip(),
            address=self.address_edit.text().strip(),
            place=self.place_edit.text().strip(),
            iban=iban,
        )
        self.accept()
