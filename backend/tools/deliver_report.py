"""Local operator workflow: issue a reviewed report, revoke it, or purge expired records.

From backend/: .venv/Scripts/python.exe tools/deliver_report.py --help
The operator must review the document before sending its bearer link to a recipient.
"""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import get_settings
from app.core.report_store import purge_deliveries, revoke_delivery, save_delivery
from app.engines.report_composer import compose_report
from app.schemas.bazi import BaziNatalRequest
from app.schemas.report import ReportRelationshipRequest, ReportTimeRequest

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("action", choices=["issue", "revoke", "purge"])
parser.add_argument("--product", choices=["r1", "r2", "r3"])
parser.add_argument(
    "--input", type=Path, help="JSON input file; never written into the delivery store"
)
parser.add_argument("--id", help="Delivery id to revoke")
parser.add_argument("--origin", default="http://localhost:5173")
args = parser.parse_args()
settings = get_settings()
if args.action == "issue":
    if not args.product or not args.input:
        parser.error("issue requires --product and --input")
    model = {"r1": ReportRelationshipRequest, "r2": BaziNatalRequest, "r3": ReportTimeRequest}[
        args.product
    ]
    request = model.model_validate(json.loads(args.input.read_text(encoding="utf-8-sig")))
    doc = save_delivery(
        settings.report_store_path, compose_report(args.product, request, request.reference_date)
    )
    print(
        f"{args.origin.rstrip('/')}/report/{args.product}#"
        + urlencode({"delivery": doc.order_id, "token": doc.token})
    )
elif args.action == "revoke":
    if not args.id:
        parser.error("revoke requires --id")
    print("revoked" if revoke_delivery(settings.report_store_path, args.id) else "not found")
else:
    print(f"purged {purge_deliveries(settings.report_store_path)} delivery records")
