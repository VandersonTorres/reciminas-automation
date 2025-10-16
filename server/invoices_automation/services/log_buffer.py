import logging

current_logs = []


class InMemoryLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        current_logs.append(log_entry)

    def clear(self):
        current_logs.clear()
