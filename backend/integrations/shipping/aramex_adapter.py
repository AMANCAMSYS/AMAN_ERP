"""
Aramex carrier adapter.

Uses the Aramex Shipping Services REST API (JSON). Endpoint reference:
  https://ws.aramex.net/ShippingAPI.V2/Shipping/Service_1_0.svc/json/CreateShipments
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

import requests

from .base import ShipmentRequest, ShipmentResult, ShippingCarrier, TrackingEvent

logger = logging.getLogger(__name__)


class AramexCarrier(ShippingCarrier):
    carrier = "aramex"

    def __init__(self, username: str, password: str, account_number: str,
                 account_pin: str, account_entity: str = "RUH",
                 account_country_code: str = "SA",
                 api_base: str = "https://ws.aramex.net",
                 timeout: int = 30):
        self.username = username
        self.password = password
        self.account_number = account_number
        self.account_pin = account_pin
        self.account_entity = account_entity
        self.account_country_code = account_country_code
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def _client_info(self) -> Dict[str, Any]:
        return {
            "UserName": self.username,
            "Password": self.password,
            "Version": "v1.0",
            "AccountNumber": self.account_number,
            "AccountPin": self.account_pin,
            "AccountEntity": self.account_entity,
            "AccountCountryCode": self.account_country_code,
            "Source": 24,
        }

    def _address(self, a: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "Line1": a.get("line1", ""),
            "Line2": a.get("line2", ""),
            "Line3": a.get("line3", ""),
            "City": a.get("city", ""),
            "StateOrProvinceCode": a.get("state", ""),
            "PostCode": a.get("postal", ""),
            "CountryCode": a.get("country", "SA"),
        }

    def _contact(self, a: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "PersonName": a.get("name", ""),
            "CompanyName": a.get("company", a.get("name", "")),
            "PhoneNumber1": a.get("phone", ""),
            "CellPhone": a.get("mobile", a.get("phone", "")),
            "EmailAddress": a.get("email", ""),
        }

    def create_shipment(self, request: ShipmentRequest) -> ShipmentResult:
        weight = float(Decimal(str(request.weight_kg)))
        shipment = {
            "Reference1": request.reference,
            "Shipper": {
                "Reference1": request.reference,
                "AccountNumber": self.account_number,
                "PartyAddress": self._address(request.origin),
                "Contact": self._contact(request.origin),
            },
            "Consignee": {
                "Reference1": request.reference,
                "PartyAddress": self._address(request.destination),
                "Contact": self._contact(request.destination),
            },
            "ShippingDateTime": f"/Date({int(datetime.utcnow().timestamp()*1000)})/",
            "Details": {
                "ActualWeight": {"Value": weight, "Unit": "Kg"},
                "ProductGroup": "DOM" if request.destination.get("country") == self.account_country_code else "EXP",
                "ProductType": request.service_code or "OND",
                "PaymentType": "P",
                "PaymentOptions": "",
                "Services": "",
                "NumberOfPieces": 1,
                "DescriptionOfGoods": request.description or "Goods",
                "GoodsOriginCountry": request.origin.get("country", "SA"),
            },
        }
        if request.cod_amount:
            shipment["Details"]["CashOnDeliveryAmount"] = {
                "Value": float(Decimal(request.cod_amount)),
                "CurrencyCode": request.currency,
            }
            shipment["Details"]["Services"] = "CODS"
        payload = {
            "Shipments": [shipment],
            "LabelInfo": {"ReportID": 9201, "ReportType": "URL"},
            "ClientInfo": self._client_info(),
        }
        try:
            r = requests.post(
                f"{self.api_base}/ShippingAPI.V2/Shipping/Service_1_0.svc/json/CreateShipments",
                json=payload, timeout=self.timeout,
            )
            body = r.json()
        except requests.RequestException as e:
            return ShipmentResult(status="failed", error_message=str(e))
        if body.get("HasErrors"):
            notif = (body.get("Notifications") or [{}])[0]
            return ShipmentResult(status="failed", gateway_response=body,
                                  error_message=notif.get("Message"))
        ship = ((body.get("Shipments") or [{}])[0]) or {}
        label = ship.get("ShipmentLabel") or {}
        return ShipmentResult(
            status="created",
            tracking_number=ship.get("ID"),
            label_url=label.get("LabelURL"),
            carrier_reference=ship.get("Reference1"),
            gateway_response=body,
        )

    def track(self, tracking_number: str) -> List[TrackingEvent]:
        payload = {
            "Shipments": [tracking_number],
            "ClientInfo": self._client_info(),
            "GetLastTrackingUpdateOnly": False,
        }
        try:
            r = requests.post(
                f"{self.api_base}/ShippingAPI.V2/Tracking/Service_1_0.svc/json/TrackShipments",
                json=payload, timeout=self.timeout,
            )
            body = r.json()
        except requests.RequestException:
            return []
        events: List[TrackingEvent] = []
        for result in body.get("TrackingResults") or []:
            val = result.get("Value") or {}
            for update in val.get("TrackingResult") or []:
                events.append(TrackingEvent(
                    code=update.get("UpdateCode", ""),
                    description=update.get("UpdateDescription", ""),
                    location=update.get("UpdateLocation"),
                ))
        return events
