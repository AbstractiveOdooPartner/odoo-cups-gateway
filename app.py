import cups
import time
import datetime
from loguru import logger
from odoorpc import ODOO

# ---------- #
# PARAMETERS #
# ---------- #

ODOO_HOST = ""
ODOO_PORT = "443"
ODOO_PROTOCOL = "jsonrpc+ssl"
ODOO_DB = ""
ODOO_USER = ""
ODOO_PASSWORD = ""
DEFAULT_PRINTER = ""

# ----------- #
# APPLICATION #
# ----------- #

if __name__ == "__main__":
    logger.add(f"/opt/odoo_cups_gw/logs/{datetime.date.today().isoformat()}.log", rotation="00:00")
    logger.info(f"Startup")
    odoo = ODOO(ODOO_HOST, ODOO_PROTOCOL, ODOO_PORT)
    odoo.login(ODOO_DB, ODOO_USER, ODOO_PASSWORD)
    connection = cups.Connection()
    jobs_waiting = odoo.env["printer.queue"].search([["printed_by", "in", [False, ""]]])
    logger.info(f"Jobs waiting: {jobs_waiting}")

    while True:
        job_ids = []
        if not jobs_waiting:
            # odoo.json("/longpolling/poll", {"channels": ["printer_queue"], "last": 0})
            time.sleep(5)
            job_ids = odoo.env["printer.queue"].search(
                [["printed_by", "in", [False, ""]]]
            )
        else:
            job_ids = jobs_waiting.copy()
        jobs_waiting = []

        # If no jobs are found: start polling again
        if not job_ids:
            continue

        logger.info(f"Job ID's received: {job_ids}")
        jobs = odoo.env["printer.queue"].browse(job_ids)
        for job in jobs:
            if job.raw_report:
                filename = f"/opt/odoo_cups_gw/labels/{job.id}.txt"
                with open(filename, mode="w") as file:
                    file.write(job.raw_report)
                connection.printFile(
                    DEFAULT_PRINTER, filename, filename, options={"raw": "1"}
                )
                logger.info(f"Printed Job: {job.id}")
            job.printed_by = DEFAULT_PRINTER
            job.printed_on = datetime.date.today()
            odoo.env.commit()
