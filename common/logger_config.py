import os
import logging
from datetime import datetime
import sys

def setup_logger(name: str) -> logging.Logger:
    """
    Konfiguruje i zwraca logger z podaną nazwą.

    Args:
        name (str): Nazwa loggera

    Returns:
        logging.Logger: Skonfigurowany logger
    """
    # Utworzenie folderu logs jeśli nie istnieje
    os.makedirs('../logs', exist_ok=True)

    # Nazwa pliku logów z aktualną datą
    log_filename = f"logs/api_{datetime.now().strftime('%Y%m%d')}.log"

    # Konfiguracja formatowania logów
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Handler dla pliku
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Handler dla konsoli
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Konfiguracja loggera
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Usuwamy istniejące handlery (gdyby były)
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger