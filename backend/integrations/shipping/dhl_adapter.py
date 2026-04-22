"""DHL Express MyDHL API adapter."""

from __future__ import annotations

import base64
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

import requests

from .base import ShipmentRequest, ShipmentResult, ShippingCarrier, TrackingEvent

logger = logging.getLogger(__name__)


class DHLCarrier(ShippingCarrier):
    carrier = "dhl"

    def __init__(self, username: str, password: str,
                 account_number: str,
                 api_base: str = "https://express.api.dhl.com/mydhlapi",
                 timeout: int = 30):
        self.username = username
        self.password = password
        self.account_number = account_number
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def _auth(self):
        return (self.username, self.password)

    def create_shipment(self, request: ShipmentRequest) -> ShipmentResult:
        today = datetime.utcnow().strftime("%Y-%m-%dT%H:00:00 GMT+00:00")
        payload: Dict[str, Any] = {
            "plannedShippingDateAndTime": today,
            "pickup": {"isRequested": False},
            "productCode": request.service_code or "P",
            "accounts": [{"typeCode": "shipper", "number": self.account_number}],
            "customerDetails": {
                "shipperDetails": {
                    "postalAddress": {
                        "postalCode": request.origin.get("postal", ""),
                        "cityName": request.origin.get("city", ""),
                        "countryCode": request.origin.get("country", "SA"),
                        "addressLine1": request.origin.get("line1", ""),
                    },
                    "contactInformation": {
                        "fullName": request.origin.get("name", ""),
                        "companyName": request.origin.get("company", request.origin.get("name", "")),
                        "phone": request.origin.get("phone", ""),
                        "email": request.origin.get("email", ""),
                    },
                },
                "receiverDetails": {
                    "postalAddress": {
                        "postalCode": request.destination.get("postal", ""),
                        "cityName": request.destination.get("city", ""),
                        "countryCode": request.destination.get("country", "AE"),
                        "addressLine1": request.destination.get("line1", ""),
                    },
                    "contactInformation": {
                        "fullName": request.destination.get("name", ""),
                        "companyName": request.destination.get("company", request.destination.get("name", "")),
                        "phone": request.destination.get("phone", ""),
                        "email": request.destination.get("email", ""),
                    },
                },
            },
            "content": {
                "packages": [{
                    "weight": float(Decimal(str(request.weight_kg))),
                    "dimensions": {"length": 10, "width": 10, "height": 10},
                    "customerReferences": [{"value": request.reference, "typeCode": "CU"}],
                }],
                "isCustomsDeclarable": False,
                "description": request.description or "Goods",
                "incoterm": "DAP",
                "unitOfMeasurement": "metric",
            },
        }
        try:
            r = requests.post(f"{self.api_base}/shipments", json=payload,
                              auth=self._auth(), timeout=self.timeout)
            body = r.json()
        except requests.RequestException as e:
            return ShipmentResult(status="failed", error_message=str(e))
        if r.status_code >= 400:
            return ShipmentResult(status="failed", gateway_response=body,
                                  error_message=body.get("detail") or body.get("title"))
        docs = body.get("documents") or []
        label_bytes = None
        for d in docs:
            if d.get("typeCode") == "label":
                try:
                    label_bytes = base64.b64decode(d.get("content") or "")
                except Exception:
                    label_bytes = None
                break
        return ShipmentResult(
            status="created",
            tracking_number=body.get("shipmentTrackingNumber"),
            awb_label=label_bytes,
            gateway_response=body,
        )

    def track(self, tracking_number: str) -> List[TrackingEvent]:
        try:
            r = requests.get(f"{self.api_base}/tracking?shipmentTrackingNumber={tracking_number}",
                             auth=self._auth(), timeout=self.timeout)
            body = r.json()
        except requests.RequestException:
            return []
        events: List[TrackingEvent] = []
        for shipment in body.get("shipments") or []:
            for e in shipment.get("events") or []:
                ts = None
                try:
                    ts = datetime.fromisoformat(f"{e.get('date')}T{e.get('time', '00:00:00')}")
                except Exception:
                    pass
                events.append(TrackingEvent(
                    code=e.get("typeCode", ""),
                    description=e.get("description", ""),
                    location=e.get("location", {}).get("address", {}).get("addressLocality"),
                    timestamp=ts,
                ))
        return events
