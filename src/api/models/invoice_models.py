# generated by datamodel-codegen:
#   filename:  iHM-BASE-ihm-base-invoice-fulfillment-1.03-merged-swagger.yaml
#   timestamp: 2021-04-08T14:07:40+00:00

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BillingScheduleType(str, Enum):
    broadcast_weekly = 'broadcast weekly'
    broadcast_monthly = 'broadcast monthly'
    calendar_monthly = 'calendar monthly'


class BillingPeriod(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    billingScheduleType: Optional[BillingScheduleType] = None


class PostingPeriod(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None


class SfdcOpportunity(BaseModel):
    id: Optional[str] = None
    billingBundle: Optional[str] = None


class Subsidiary(str, Enum):
    iheartmedia = 'iheartmedia'


class OrderType(str, Enum):
    mmp = 'mmp'
    inside_sales = 'inside sales'
    local = 'local'
    market_collaboration = 'market collaboration'
    national = 'national'


class SpecialDeal(BaseModel):
    id: Optional[str] = None
    dealType: Optional[str] = None
    deal_name: Optional[str] = Field(None, alias='deal-name')


class StrataIOAttributes(BaseModel):
    strataContractTypeCode: Optional[str] = None
    strataParentOrderID: Optional[str] = None
    strataDevDype: Optional[str] = None
    ediContract_no: Optional[str] = Field(None, alias='ediContract-no')
    devAe: Optional[str] = None
    customer: Optional[str] = None


class InvoiceLineType(str, Enum):
    digital = 'digital'
    spot = 'spot'
    miscellaneous = 'miscellaneous'


class RevenueType(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class Unit(str, Enum):
    impressions = 'impressions'
    days = 'days'
    months = 'months'
    spots = 'spots'
    grp = 'grp'
    n_a = 'n/a'


class RateType(str, Enum):
    cpm = 'cpm'
    cpp = 'cpp'
    flat_rate_ = 'flat rate’'
    cost_per_day = 'cost per day'
    cpd = 'cpd'
    flat_rate_impressions = 'flat rate impressions'


class Product(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    productCategory: Optional[str] = None
    productType: Optional[str] = None


class BookingType(str, Enum):
    remnant = 'remnant'
    guaranteed = 'guaranteed'


class InvoiceAmountBasis(str, Enum):
    primary_delivery = 'primary delivery'
    third_party_delivery = 'third party delivery'
    fixed = 'fixed'
    even_billing = 'even billing'
    ____ = '????'


class FulfillmentStatus(str, Enum):
    scheduled = 'scheduled'
    verified = 'verified'
    completed = 'completed'
    canceled = 'canceled'
    error = 'error'
    exception = 'exception'
    deleted = 'deleted'


class FulfillmentType(str, Enum):
    spot = 'spot'
    digital = 'digital'
    misc = 'misc'


class BillingDisposition(str, Enum):
    billable = 'billable'
    non_billable = 'non-billable'


class Success(BaseModel):
    requestTrackingID: str = Field(
        ...,
        description='API creates a UUID for each object submitted within a request, any logging will include this ID,.',
    )
    id: str = Field(
        ...,
        description="api's ID given to the invoice that was posted, put or deleted.",
    )
    message: str


class Scope(str, Enum):
    order = 'order'
    spot = 'spot'
    digital = 'digital'
    miscellaneous = 'miscellaneous'


class BillingSchedule(str, Enum):
    quarterly = 'quarterly'
    broadcast_monthly = 'broadcast monthly'
    broadcast_weekly = 'broadcast weekly'
    calendar_monthly = 'calendar monthly'


class DeliveryMethodEnum(str, Enum):
    edi = 'edi'
    email = 'email'
    print = 'print'


class BillingBundle(BaseModel):
    id: Optional[str] = None


class CoopType(str, Enum):
    consolidated = 'consolidated'
    individual = 'individual'


class SplitBy(str, Enum):
    station = 'station'
    market = 'market'
    isci = 'isci'
    week = 'week'
    product_line = 'product line'


class SpecialBillingRequest(str, Enum):
    ae_review_required = 'ae review required'
    contract_based_invoice = 'contract based invoice'
    special_handling_required = 'special handling required'


class TradeContract(BaseModel):
    id: Optional[str] = None
    contractPercentage: Optional[int] = None


class Market(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class Station(BaseModel):
    enterpriseID: Optional[str] = None
    name: Optional[str] = None
    fccID: Optional[str] = None
    callLetters: Optional[str] = None
    isSimulcast: Optional[bool] = None


class Type(str, Enum):
    agency = 'agency'
    advertiser = 'advertiser'


class Terms(str, Enum):
    cia = 'cia'
    net_0 = 'net 0'
    net_30 = 'net 30'
    net_45 = 'net 45'
    net_60 = 'net 60'
    net_90 = 'net 90'
    net_120 = 'net 120'


class BillingAddress(BaseModel):
    id: Optional[str] = None
    attentionTo: Optional[str] = None
    streetAddress: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[int] = None
    country: Optional[str] = None
    email: Optional[str] = None
    ediPartner_key: Optional[str] = Field(None, alias='ediPartner-key')


class CustomerAccount(BaseModel):
    friendlyID: Optional[str] = None
    sfdcID: Optional[str] = None
    type: Optional[Type] = None
    name: Optional[str] = None
    terms: Optional[Terms] = None
    billingAddress: Optional[BillingAddress] = None


class RecepientType(str, Enum):
    employee = 'employee'
    sales_team = 'sales team'
    market = 'market'


class CommissionInstruction(BaseModel):
    recepientType: Optional[RecepientType] = None
    id: Optional[int] = None
    commissionPercentage: Optional[float] = None
    commissionBu: Optional[int] = None


class OriginatingSystem(str, Enum):
    viero = 'viero'
    operative = 'operative'


class FulfillmentOrder(BaseModel):
    orderId: Optional[int] = None
    originatingSystem: Optional[OriginatingSystem] = None
    siteID: Optional[float] = None
    serverName: Optional[str] = None


class Error(BaseModel):
    requestTrackingID: Optional[str] = Field(
        None,
        description='API creates a UUID for each object submitted within a request, any logging will include this ID, if there is an error the error in Kibana will include this ID.',
    )
    code: str
    message: str


class InvoiceLine(BaseModel):
    invoiceLineID: Optional[str] = Field(
        None, description='line number in Netsuite, should be a sequential number'
    )
    invoiceLineType: Optional[InvoiceLineType] = None
    orderLineID: Optional[str] = None
    tradeContract_number: Optional[str] = Field(None, alias='tradeContract-number')
    isLocalTrade: Optional[bool] = None
    newBusiness: Optional[float] = None
    makeGood: Optional[bool] = None
    market: Optional[Market] = None
    station: Optional[Station] = None
    revenueType: Optional[RevenueType] = None
    businessUnitID: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    unit: Optional[Unit] = None
    quantityInvoiced: Optional[int] = None
    quantityOrdered: Optional[int] = None
    rateType: Optional[RateType] = None
    rate: Optional[float] = None
    product: Optional[Product] = None
    bindTo: Optional[str] = None
    breakType: Optional[str] = None
    days: Optional[str] = None
    length: Optional[str] = None
    billableThirdParty: Optional[str] = None
    thirdPartyDeliverySource: Optional[str] = None
    added_value: Optional[str] = Field(None, alias='added-value')
    bookingType: Optional[BookingType] = None
    demo: Optional[str] = None
    advertiserProduct_name: Optional[str] = Field(None, alias='advertiserProduct-name')
    invoiceAmountBasis: Optional[InvoiceAmountBasis] = None
    baseAmount: Optional[float] = None
    agencyCommissionAmount: Optional[float] = None
    discountAmount: Optional[float] = None
    arAdjustmentAmount: Optional[float] = None
    taxAmount: Optional[float] = None
    netAmount: Optional[float] = None
    discountPct: Optional[float] = None
    agencyCommissionPct: Optional[float] = None
    taxRate: Optional[float] = None


class Fulfillment(BaseModel):
    id: Optional[str] = None
    day: Optional[str] = Field(
        None,
        description='if fulfillment group to day, this is the day of the grouping',
        example='2020/06/15',
    )
    fulfillmentStatus: Optional[FulfillmentStatus] = Field(
        None, description='status of misc-fulfillment.'
    )
    fulfillmentType: Optional[FulfillmentType] = None
    billingDisposition: Optional[BillingDisposition] = None
    fulfilledDate: Optional[str] = None
    quantity: Optional[int] = None
    length: Optional[float] = None
    station: Optional[Station] = None
    businessUnit: Optional[str] = None
    isMakegood: Optional[bool] = None
    makegoodReasonID: Optional[str] = None
    makegoodOriginalOrderdate: Optional[str] = None
    makegoodDeletedSpotid: Optional[str] = None
    isci: Optional[str] = None
    linkedSpotID: Optional[str] = None
    originalOrderline: Optional[str] = None
    creative: Optional[str] = None
    isDeleted: Optional[bool] = Field(
        False, description='revenue type is actively used if false'
    )
    dateCreated: Optional[str] = Field(
        None, description='Date time revenue type map was created'
    )
    lastModifiedDate: Optional[str] = Field(
        None, description='Date time revenue type map was last updted'
    )


class BillingInstruction(BaseModel):
    scope: Optional[Scope] = None
    billingSchedule: Optional[BillingSchedule] = None
    preBillRequired: Optional[bool] = None
    invoiceRecipients: Optional[List[CustomerAccount]] = None
    deliveryMethod: Optional[List[DeliveryMethodEnum]] = None
    isBundled: Optional[bool] = None
    billingBundle: Optional[BillingBundle] = None
    isCoop: Optional[bool] = None
    coopType: Optional[CoopType] = None
    notarize: Optional[bool] = None
    isSummaryInvoice: Optional[bool] = None
    splitBy: Optional[SplitBy] = None
    suppressRate: Optional[bool] = None
    suppressMiscRate: Optional[bool] = None
    suppressDigitalRate: Optional[bool] = None
    numberOfCopies: Optional[float] = None
    combineSpotMiscDigitalOnInvoice: Optional[bool] = None
    toBeInvoicedAs: Optional[str] = None
    emailAddress: Optional[str] = None
    isBillAndRemit: Optional[bool] = None
    specialBillingRequest: Optional[SpecialBillingRequest] = None
    isSpecialBilling: Optional[bool] = None
    specialBillingInstructions: Optional[str] = None
    tradeContract: Optional[TradeContract] = None
    agencyCommision: Optional[int] = None
    discount: Optional[int] = None
    customerID: Optional[str] = None
    ediPartner: Optional[str] = None


class InvoiceHeader(BaseModel):
    id: Optional[str] = Field(
        None,
        description='Invoice document ID (same as printed on invoice), not to be confused with netsuite internal ID',
    )
    netsuiteInternalID: Optional[str] = Field(
        None, description='netsuite internal ID for invoice'
    )
    isAdjustmentInvoice: Optional[bool] = None
    invoicesAdjustedByThisInvoice: Optional[List[str]] = None
    isAdjusted: Optional[bool] = None
    adjustmentInvoicesAppliedToThisInvoice: Optional[List[str]] = Field(
        None,
        description='if this invoice has been adjusted, this is a list of all the invoices that have been created',
    )
    invoiceDate: Optional[str] = None
    grossAmount: Optional[float] = None
    netAmount: Optional[float] = None
    taxTotal: Optional[float] = None
    agencyDiscountPct: Optional[int] = None
    agencyDiscountAmount: Optional[float] = None
    homeMarket: Optional[Market] = None
    billingPeriod: Optional[BillingPeriod] = None
    postingPeriod: Optional[PostingPeriod] = None
    customerOrderID: Optional[str] = None
    adbuilderOrderID: Optional[str] = None
    sfdcOpportunity: Optional[SfdcOpportunity] = None
    subsidiary: Optional[Subsidiary] = None
    EST_IO_CPE: Optional[str] = Field(None, alias='EST/IO/CPE')
    note1: Optional[str] = None
    note2: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    toBeAiredAs: Optional[str] = None
    industryCode: Optional[str] = None
    subIndustryCode: Optional[str] = None
    productCode: Optional[str] = None
    campaign: Optional[str] = None
    salesOwner: Optional[str] = None
    isPolitical: Optional[bool] = None
    orderType: Optional[OrderType] = None
    dealType: Optional[str] = None
    specialDeal: Optional[SpecialDeal] = None
    customerAccounts: Optional[List[CustomerAccount]] = None
    billingInstructions: Optional[List[BillingInstruction]] = None
    salesTeam: Optional[List[CommissionInstruction]] = None
    fulfillmentOrders: Optional[List[FulfillmentOrder]] = None
    strataIOAttributes: Optional[StrataIOAttributes] = None
    isDeleted: Optional[bool] = Field(
        False, description='revenue type is actively used if false'
    )
    dateCreated: Optional[str] = Field(
        None, description='Date time revenue type map was created'
    )
    lastModifiedDate: Optional[str] = Field(
        None, description='Date time revenue type map was last updted'
    )


class InvoiceLineWithFulfillment(InvoiceLine):
    fulfillments: Optional[List[Fulfillment]] = None


class Invoice(InvoiceHeader):
    invoiceLines: Optional[List[InvoiceLine]] = None
    isDeleted: Optional[bool] = Field(
        False, description='revenue type is actively used if false'
    )
    dateCreated: Optional[str] = Field(
        None, description='Date time revenue type map was created'
    )
    lastModifiedDate: Optional[str] = Field(
        None, description='Date time revenue type map was last updted'
    )


class InvoiceDetailed(InvoiceHeader):
    invoiceLines: Optional[List[InvoiceLineWithFulfillment]] = None
    isDeleted: Optional[bool] = Field(
        False, description='revenue type is actively used if false'
    )
    dateCreated: Optional[str] = Field(
        None, description='Date time revenue type map was created'
    )
    lastModifiedDate: Optional[str] = Field(
        None, description='Date time revenue type map was last updted'
    )