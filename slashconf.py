from logbook.compat import redirect_logging
import slash

slash.config.root.log.format = "{record.channel}: {record.message}"

redirect_logging()