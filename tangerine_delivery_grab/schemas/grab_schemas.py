from pydantic import BaseModel, HttpUrl
from ..settings.constants import settings


class TokenRequest(BaseModel):
    client_id: str
    client_secret: str
    grant_type: str
    scope: str


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str


class Dimensions(BaseModel):
    height: int
    width: int
    depth: int
    weight: int


class Coordinates(BaseModel):
    latitude: float | None = None
    longitude: float | None = None


class Package(BaseModel):
    name: str
    description: str
    quantity: int
    price: int | None = 0
    dimensions: Dimensions


class Quote(BaseModel):
    amount: int


class Location(BaseModel):
    address: str
    coordinates: Coordinates | None | dict = {}


class Recipient(BaseModel):
    firstName: str
    email: str | bool | None = None
    phone: str
    smsEnabled: bool = False


class Sender(BaseModel):
    firstName: str
    email: str | bool | None = None
    phone: str
    smsEnabled: bool = False


class Schedule(BaseModel):
    pickupTimeFrom: str
    pickupTimeTo: str


class CashOnDelivery(BaseModel):
    amount: float


class DestinationMultiStop(Location):
    packages: list[Package]


class DestinationMultiStopResponse(DestinationMultiStop):
    amount: float


class QuoteMultiStop(BaseModel):
    destination: list[DestinationMultiStopResponse]


class Driver(BaseModel):
    name: str
    phone: str
    licensePlate: str
    photoURL: str
    currentLat: float
    currentLng: float


class DeliveryQuotesRequest(BaseModel):
    serviceType: str | None = None
    vehicleType: str | None = None
    packages: list[Package]
    origin: Location
    destination: Location


class DeliveryQuotesResponse(BaseModel):
    quotes: list[Quote]


class CreateDeliveryRequest(BaseModel):
    merchantOrderID: str
    serviceType: str
    vehicleType: str | None = None
    codType: str | None = None
    paymentMethod: str | None = None
    payer: str | None = None
    highValue: bool
    promoCode: str | None = None
    cashOnDelivery: CashOnDelivery | None = None
    packages: list[Package]
    origin: Location
    destination: Location
    recipient: Recipient
    sender: Sender
    schedule: Schedule | None = None


class CreateDeliveryResponse(BaseModel):
    deliveryID: str
    quote: Quote
    trackingURL: str | HttpUrl | None = None


class TrackingWebhookRequest(BaseModel):
    deliveryID: str
    merchantOrderID: str
    status: str
    trackURL: str | HttpUrl | None = None
    failedReason: str | None = None
    driver: Driver | None = None


class MultiStopDeliveryQuotesRequest(BaseModel):
    serviceType: str = 'MULTI_STOP'
    vehicleType: str = settings.default_vehicle_type
    codType: str = settings.default_cod_type
    origin: list[Location]
    destination: list[DestinationMultiStop]
    routeOptimized: bool = True


class MultiStopDeliveryQuotesResponse(BaseModel):
    quotes: list[QuoteMultiStop]
