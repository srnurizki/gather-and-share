# <<<./ Import Libraries
from pydantic import BaseModel, Field, model_validator

# <<<./ Item-level Receipt
class ReceiptItem(BaseModel):
    model_config = {'str_strip_whitespace': True}

    name: str = Field(description='Item name as printed on the receipt')
    quantity: float = Field(gt=0, description='Number of items purchased')
    unit_price: float = Field(ge=0, description='Price per item in IDR')
    total_price: float = Field(ge=0, description='Total price for this item in IDR')

# <<<./ Additional Charges due to Tax, Services, etc.
class AdditionalCharges(BaseModel):
    model_config = {'str_strip_whitespace': True}

    label: str = Field(description='Charges label as printed on the receipt (e.g. PPN 10%, Service, PB1')
    amount: float = Field(ge=0, description='Amount charged in IDR')

# <<<./ Receipt Components
class Receipt(BaseModel):
    model_config = {'str_strip_whitespace': True}

    items: list[ReceiptItem] = Field(description='Every items on the receipt')
    subtotal: float = Field(ge=0, description='Subtotal of items before additional charges')
    additional_charges: list[AdditionalCharges] = Field(default_factory=list, description='All additional charges (tax, service, etc.)')
    total: float = Field(ge=0, description="Grand total as printed on the receipt")

    # <<<./ Manually Computed Subtotal
    @property
    def computed_subtotal(self):
        return round(sum(item.total_price for item in self.items), 2)

    # <<<./ Total Add. Charges
    @property
    def total_additional_charges(self):
        return round(sum(charge.amount for charge in self.additional_charges), 2)

    # <<<./ Check Equivalency of Subtotal
    @property
    def is_subtotal_consistent(self):
        return abs(self.subtotal - self.computed_subtotal) <= 1.0

    # <<<./ Check Equivalency of Total
    @property
    def is_total_consistent(self):
        expected = round(self.computed_subtotal + self.total_additional_charges, 2)
        return abs(self.total - expected) <= 1.0

# <<<./ Items to be Assigned
class ItemAssignment(BaseModel):
    item_index: int = Field(ge=0, description='Index into ReceiptItem or Receipt.items')
    assigned_to: list[str] = Field(min_length=1, description='Participant name sharing this item')

# <<<./ Bill Splitting Result
class SplitResult(BaseModel):
    member: str
    assigned_items: list[ReceiptItem]
    item_subtotal: float = Field(ge=0, description="Subtotal of this member's item bill shares")
    charge_share: float = Field(ge=0, description='Proportional share of additional charges')
    total_owed: float = Field(ge=0, description='Total amount owed by this member')

    # <<<./ Validate Total Bill
    @model_validator(mode='after')
    def check_total_consistency(self):
        expected = round(self.item_subtotal + self.charge_share, 2)
        if abs(expected - self.total_owed) > 1.0:
            raise ValueError(
                f"Total owed {self.total_owed} does not match expected item subtotal: {self.item_subtotal} + charge_share: {self.charge_share} for member: {self.member}")
        return self

# <<<./ Complete Split Bill Result for All Members
class BillResult(BaseModel):

    receipt: Receipt
    members: list[str]
    assignments: list[ItemAssignment]
    results: list[SplitResult]

    # Total Owed by Member
    @property
    def total_collected(self):
        return round(sum(r.total_owed for r in self.results), 2)

    # Check Equivalency of Total Bill to Sum of Shared Bill
    @property
    def is_split_balanced(self):
        return abs(self.total_collected - self.receipt.total) <= 1.0