import os
from venv import logger

from dotenv import load_dotenv
import psutil
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

EXPORTER_HOST = os.environ.get("EXPORTER_HOST", "0.0.0.0")
EXPORTER_PORT = int(os.environ.get("EXPORTER_PORT", "8081"))


# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Логи выводятся в консоль
        # Если нужно писать в файл, добавьте FileHandler:
        # logging.FileHandler("exporter.log"),
    ],
)

logger = logging.getLogger(__name__)


def generate_metrics():
    """
    Генерирует системные метрики в формате Prometheus.

    Возвращает:
        str: Строка, содержащая системные метрики, отформатированные по стандарту Prometheus.

    Метрики:
        - cpu_usage: Использование процессора в процентах.
        - memory_total: Общий объем оперативной памяти в байтах.
        - memory_used: Используемая оперативная память в байтах.
        - disk_total: Общий объем дискового пространства в байтах.
        - disk_used: Используемое дисковое пространство в байтах.
    """
    cpu_usage = psutil.cpu_percent()

    mem_info = psutil.virtual_memory()
    memory_total = mem_info.total
    memory_used = memory_total - mem_info.available

    disk_info = psutil.disk_usage("/")
    disk_total = disk_info.total
    disk_used = disk_info.used

    metrics = [
        "# HELP cpu_usage CPU usage percentage",
        "# TYPE cpu_usage gauge",
        f"cpu_usage {cpu_usage}",
        "# HELP memory_total Total system memory in bytes",
        "# TYPE memory_total gauge",
        f"memory_total {memory_total}",
        "# HELP memory_used Used system memory in bytes",
        "# TYPE memory_used gauge",
        f"memory_used {memory_used}",
        "# HELP disk_total Total disk space in bytes",
        "# TYPE disk_total gauge",
        f"disk_total {disk_total}",
        "# HELP disk_used Used disk space in bytes",
        "# TYPE disk_used gauge",
        f"disk_used {disk_used}",
    ]

    return "\n".join(metrics)


class MetricsHandler(BaseHTTPRequestHandler):
    """
    HTTP-обработчик для предоставления метрик Prometheus.

    Этот обработчик отвечает на GET-запросы:
    - Для пути "/": возвращает системные метрики в формате Prometheus.
    - Для любых других путей: возвращает ошибку 404 Not Found.
    """

    def do_GET(self):
        """
        Обработка GET-запросов.

        - Путь "/": Возвращает метрики.
        - Любой другой путь: Возвращает ошибку 404 (Not Found).
        """
        if self.path == "/":
            logger.info("Received GET request for metrics.")
            metrics = generate_metrics()

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(metrics.encode("utf-8"))
        else:
            logger.warning(f"Received GET request for unknown path: {self.path}")
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    """
    Точка входа для экспорта метрик Prometheus.

    Скрипт инициализирует и запускает HTTP-сервер для предоставления системных метрик
    в формате Prometheus. Сервер слушает хост и порт, заданные в переменных окружения,
    или по умолчанию 0.0.0.0:8081.
    """
    logger.info(f"Starting exporter on {EXPORTER_HOST}:{EXPORTER_PORT}")
    try:
        server = HTTPServer((EXPORTER_HOST, EXPORTER_PORT), MetricsHandler)
        logger.info(f"Exporter running on http://{EXPORTER_HOST}:{EXPORTER_PORT}/")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down the exporter.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")