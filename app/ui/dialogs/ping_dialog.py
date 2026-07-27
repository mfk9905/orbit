"""
Orbit Ping Tool - Continuous Real-Time Network Monitor Dialog (ping -a -t).
Enables active host monitoring with live stdout stream, latency statistics, and PySide6 QProcess integration.
"""

import sys
import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QPlainTextEdit, QFrame, QGroupBox, QApplication
)
from PySide6.QtCore import Qt, QProcess, Slot
from PySide6.QtGui import QFont, QTextCursor
from app.ui.theme.design_system import OrbitTheme
from app.core.logging.logger import get_logger

logger = get_logger("orbit.ui.ping_dialog")


class PingDialog(QDialog):
    """Modern dark-themed PySide6 window for continuous ping -a -t host monitoring."""

    def __init__(self, parent=None, initial_host: str = "8.8.8.8") -> None:
        super().__init__(parent)
        self.setWindowTitle("Orbit Ping - Canlı Ağ Monitörü (ping -a -t)")
        self.resize(720, 540)
        self.setStyleSheet(OrbitTheme.MAIN_STYLESHEET)

        self.process: QProcess = None
        self.packet_count: int = 0
        self.last_latency: str = "-"
        self.resolved_target: str = "-"

        self._init_ui(initial_host)

    def _init_ui(self, initial_host: str) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header Title & Subtitle
        header_layout = QVBoxLayout()
        header_title = QLabel("🌐 Canlı Ağ ve IP Ping Monitörü")
        header_title.setFont(OrbitTheme.get_font(14, bold=True))
        header_title.setStyleSheet("color: #2ED573;")

        header_desc = QLabel("Hedef IP veya alan adını girerek 'ping -a -t' komutu ile sürekli yanıt ve ad çözümleme istatistiklerini takip edin.")
        header_desc.setFont(OrbitTheme.get_font(9))
        header_desc.setStyleSheet("color: #94A3B8;")
        header_desc.setWordWrap(True)

        header_layout.addWidget(header_title)
        header_layout.addWidget(header_desc)
        main_layout.addLayout(header_layout)

        # Controls Group (IP Input & Actions)
        ctrl_card = QFrame()
        ctrl_card.setStyleSheet("""
            QFrame {
                background-color: #141923;
                border: 1px solid #232D3F;
                border-radius: 10px;
                padding: 8px;
            }
        """)
        ctrl_layout = QHBoxLayout(ctrl_card)
        ctrl_layout.setSpacing(10)

        input_lbl = QLabel("Hedef IP / Host:")
        input_lbl.setFont(OrbitTheme.get_font(10, bold=True))

        self.txt_target = QLineEdit(initial_host)
        self.txt_target.setPlaceholderText("Örn: 8.8.8.8 veya google.com")
        self.txt_target.setFont(OrbitTheme.get_font(10))
        self.txt_target.setMinimumHeight(36)
        self.txt_target.returnPressed.connect(self.start_ping)

        self.btn_start = QPushButton("▶ Ping Başlat")
        self.btn_start.setFont(OrbitTheme.get_font(10, bold=True))
        self.btn_start.setMinimumHeight(36)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ED573, stop:1 #10B981);
                color: #042F1A;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #34E77F;
            }
            QPushButton:disabled {
                background: #1C2433;
                color: #64748B;
            }
        """)
        self.btn_start.clicked.connect(self.start_ping)

        self.btn_stop = QPushButton("⏹ Durdur")
        self.btn_stop.setFont(OrbitTheme.get_font(10, bold=True))
        self.btn_stop.setMinimumHeight(36)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #FF4757;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B81;
            }
            QPushButton:disabled {
                background-color: #1C2433;
                color: #64748B;
            }
        """)
        self.btn_stop.clicked.connect(self.stop_ping)

        self.btn_clear = QPushButton("🗑 Temizle")
        self.btn_clear.setFont(OrbitTheme.get_font(9))
        self.btn_clear.setMinimumHeight(36)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #1C2433;
                color: #94A3B8;
                border: 1px solid #2A364F;
                border-radius: 6px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #253247;
                color: #F1F5F9;
            }
        """)
        self.btn_clear.clicked.connect(self.clear_output)

        ctrl_layout.addWidget(input_lbl)
        ctrl_layout.addWidget(self.txt_target, stretch=1)
        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addWidget(self.btn_clear)
        main_layout.addWidget(ctrl_card)

        # Statistics Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        self.card_status = self._create_stat_card("Durum", "Hazır", "#94A3B8")
        self.card_packets = self._create_stat_card("Paket Sayısı", "0", "#2ED573")
        self.card_latency = self._create_stat_card("Son Gecikme", "- ms", "#00F2FE")
        self.card_target = self._create_stat_card("Aktif Hedef", "-", "#FFA502")

        stats_layout.addWidget(self.card_status["frame"])
        stats_layout.addWidget(self.card_packets["frame"])
        stats_layout.addWidget(self.card_latency["frame"])
        stats_layout.addWidget(self.card_target["frame"])
        main_layout.addLayout(stats_layout)

        # Terminal Output Console
        console_group = QGroupBox("Canlı Ping Çıktısı (ping -a -t)")
        console_group.setFont(OrbitTheme.get_font(10, bold=True))
        console_layout = QVBoxLayout(console_group)
        console_layout.setContentsMargins(8, 16, 8, 8)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(5000)
        self.console.setFont(QFont("Consolas", 10))
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0B0E14;
                color: #38BDF8;
                border: 1px solid #1C2433;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #253247;
            }
        """)

        console_layout.addWidget(self.console)
        main_layout.addWidget(console_group, stretch=1)

    def _create_stat_card(self, title: str, default_val: str, color_hex: str) -> dict:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #141923;
                border: 1px solid #232D3F;
                border-radius: 8px;
                padding: 6px 10px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        lbl_title = QLabel(title.upper())
        lbl_title.setFont(QFont("Segoe UI", 8, QFont.Bold))
        lbl_title.setStyleSheet("color: #64748B;")

        lbl_val = QLabel(default_val)
        lbl_val.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_val.setStyleSheet(f"color: {color_hex};")
        lbl_val.setAlignment(Qt.AlignLeft)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)

        return {"frame": frame, "title_label": lbl_title, "val_label": lbl_val}

    def start_ping(self) -> None:
        target = self.txt_target.text().strip()
        if not target:
            self.console.appendPlainText("⚠️ [HATA] Lütfen geçerli bir IP adresi veya alan adı girin.")
            return

        if self.process and self.process.state() != QProcess.NotRunning:
            self.stop_ping()

        self.packet_count = 0
        self.last_latency = "-"
        self.resolved_target = target
        self.card_packets["val_label"].setText("0")
        self.card_latency["val_label"].setText("- ms")
        self.card_target["val_label"].setText(target)
        self.card_status["val_label"].setText("Ping Atılıyor...")
        self.card_status["val_label"].setStyleSheet("color: #2ED573;")

        self.console.appendPlainText(f"\n🚀 === PING BAŞLATILDI: ping -a -t {target} ===\n")

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._handle_finished)

        # Execute ping command with -a (resolve hostname) and -t (continuous ping)
        self.process.start("ping", ["-a", "-t", target])

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.txt_target.setEnabled(False)

    def stop_ping(self) -> None:
        if self.process and self.process.state() != QProcess.NotRunning:
            logger.info("Stopping ping process...")
            self.process.terminate()
            if not self.process.waitForFinished(1000):
                self.process.kill()
        
        self.card_status["val_label"].setText("Durduruldu")
        self.card_status["val_label"].setStyleSheet("color: #FF4757;")
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.txt_target.setEnabled(True)
        self.console.appendPlainText("\n🛑 === PING DURDURULDU ===\n")

    def clear_output(self) -> None:
        self.console.clear()

    @Slot()
    def _handle_stdout(self) -> None:
        if not self.process:
            return
        
        data = self.process.readAllStandardOutput().data()
        try:
            # Decode using system default encoding (e.g. cp857, cp1254, or utf-8 on Windows)
            text = data.decode("cp857", errors="replace")
        except Exception:
            text = data.decode("utf-8", errors="replace")

        for line in text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            self.console.appendPlainText(line_str)
            self._parse_ping_line(line_str)

        self.console.moveCursor(QTextCursor.End)

    @Slot()
    def _handle_stderr(self) -> None:
        if not self.process:
            return
        
        data = self.process.readAllStandardError().data()
        text = data.decode("utf-8", errors="replace")
        if text.strip():
            self.console.appendPlainText(f"❌ [HATA]: {text.strip()}")
            self.console.moveCursor(QTextCursor.End)

    @Slot()
    def _handle_finished(self) -> None:
        if self.btn_stop.isEnabled():
            self.stop_ping()

    def _parse_ping_line(self, line: str) -> None:
        """Parses ping output lines to update live stats (packet count, latency, resolution)."""
        # Match latency patterns: süre=XXms or time=XXms or süre<1ms or time<1ms
        latency_match = re.search(r'(?:süre|time)[=<](\d+|<1)ms', line, re.IGNORECASE)
        if latency_match:
            self.packet_count += 1
            ms_val = latency_match.group(1)
            self.last_latency = f"{ms_val} ms"
            self.card_packets["val_label"].setText(str(self.packet_count))
            self.card_latency["val_label"].setText(self.last_latency)

        # Match hostname resolution pattern: Pinging host [IP] ... or host [IP] ile ...
        resolve_match = re.search(r'ping(?:ing)?\s+([^\s\[]+)\s*\[([^\]]+)\]', line, re.IGNORECASE)
        if resolve_match:
            host_name, ip_addr = resolve_match.group(1), resolve_match.group(2)
            self.resolved_target = f"{host_name} ({ip_addr})"
            self.card_target["val_label"].setText(self.resolved_target)

    def closeEvent(self, event) -> None:
        """Ensures background process is terminated cleanly when dialog is closed."""
        self.stop_ping()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = PingDialog(initial_host="8.8.8.8")
    dialog.show()
    sys.exit(app.exec())
