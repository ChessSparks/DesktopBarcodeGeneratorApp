import io

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from app.hub3a import PaymentSlip
from app.slip_renderer import render_filled_slip


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    pixmap = QPixmap()
    pixmap.loadFromData(buffer.getvalue())
    return pixmap


class SlipPreviewDialog(QDialog):
    def __init__(self, slip: PaymentSlip, parent=None):
        super().__init__(parent)
        self.slip = slip
        self.setWindowTitle(f"Payment slip - {slip.payer_name}")
        self.resize(1050, 550)

        self.image = render_filled_slip(slip)
        self.pixmap = pil_to_qpixmap(self.image)

        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setPixmap(
            self.pixmap.scaled(1000, 900, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        scroll.setWidget(self.image_label)
        layout.addWidget(scroll)

        button_row = QHBoxLayout()
        print_btn = QPushButton("Print")
        print_btn.clicked.connect(self._on_print)
        export_btn = QPushButton("Export as PNG/PDF")
        export_btn.clicked.connect(self._on_export)
        button_row.addWidget(print_btn)
        button_row.addWidget(export_btn)
        button_row.addStretch(1)
        layout.addLayout(button_row)

    def _paint_to_printer(self, printer: QPrinter) -> None:
        painter = QPainter(printer)
        page_rect = printer.pageRect(QPrinter.DevicePixel)
        scaled = self.pixmap.scaled(
            int(page_rect.width()), int(page_rect.height()), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x = (page_rect.width() - scaled.width()) / 2
        y = (page_rect.height() - scaled.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled)
        painter.end()

    def _on_print(self) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOrientation(QPrinter.Landscape)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QDialog.Accepted:
            return
        self._paint_to_printer(printer)

    def _on_export(self) -> None:
        safe_name = "".join(c for c in self.slip.payer_name if c.isalnum() or c in " -_").strip() or "slip"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export payment slip", f"{safe_name}.png", "PNG image (*.png);;PDF document (*.pdf)"
        )
        if not path:
            return

        if path.lower().endswith(".pdf"):
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOrientation(QPrinter.Landscape)
            printer.setOutputFileName(path)
            self._paint_to_printer(printer)
        else:
            if not path.lower().endswith(".png"):
                path += ".png"
            self.image.save(path)

        QMessageBox.information(self, "Exported", f"Saved to {path}")
