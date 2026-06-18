# <<<./ Import Libraries
from src.schemas import (BillResult, ItemAssignment, Receipt,
                         ReceiptItem, SplitResult)

# <<<./ Raise Calculation Error
class CalculationError(Exception):
    pass

# <<<./ Bill Calculator
class BillCalculator:
    def validate(self, receipt: Receipt, assignments: list[ItemAssignment], members: list[str]):
        if not members:
            raise CalculationError(f'Members list cannot be empty.')

        # <<<./ Validate Duplicates
        item_indices = [a.item_index for a in assignments]
        if len(item_indices) != len(set(item_indices)):
            raise CalculationError(f'Each item_index can only appear in one ItemAssignment.'
                                   'Duplicated item_index identified.')

        # <<<./ Validate Indices Range
        for assignment in assignments:
            if assignment.item_index >= len(receipt.items):
                raise CalculationError(
                    f'item_index {assignment.item_index} is out of range.'
                    'Receipt has {len(receipt.items)} items.'
                    'Valid range is 0-{len(receipt.items)-1}.')

        # <<<./ Validate Members List
        members_set = set(members)
        for assignment in assignments:
            for name in assignment.assigned_to:
                if name not in members_set:
                    raise CalculationError(
                        f'{name} appears in an ItemAssignment but not in the members list.')

        # <<<./ Validate Item Assignment
        assigned_indices = {a.item_index for a in assignments}
        for i, item in enumerate(receipt.items):
            if i not in assigned_indices:
                raise CalculationError(
                    f'Item {item.name} (index {i}) has no assignment.'
                    'Every item must be assigned to at least one member.')

    # <<<./ Calculate Item Subtotal
    def calculate_subtotals(self, receipt: Receipt, assignments: list[ItemAssignment], members: list[str]):
        subtotals: dict[str, float] = {m: 0.0 for m in members}

        for assignment in assignments:
            item = receipt.items[assignment.item_index]
            share = item.total_price / len(assignment.assigned_to)
            for name in assignment.assigned_to:
                subtotals[name] = round(subtotals[name] + share, 2)

        return subtotals

    # <<<./ Calculate Proportional Charges Share
    def calculate_charge_share(self, receipt: Receipt, item_subtotals: dict[str, float], members: list[str]):
        total_additional = receipt.total_additional_charges
        computed_subtotal = receipt.computed_subtotal

        if total_additional == 0  or computed_subtotal == 0:
            return {m: 0.0 for m in members}

        charge_shares: dict[str, float] = {}

        for member in members[:-1]:
            proportion = item_subtotals[member] / computed_subtotal
            charge_shares[member] = round(proportion * total_additional, 2)

        last = members[-1]
        charge_shares[last] = round(total_additional - sum(charge_shares.values()), 2)
        return charge_shares

    # <<<./ Recap Member Items Assignment
    def collect_member_items(self, receipt: Receipt, assignments: list[ItemAssignment], members: list[str]):
        item_indices: dict[str, set] = {m: set() for m in members}

        for assignment in assignments:
            for name in assignment.assigned_to:
                item_indices[name].add(assignment.item_index)

        return {m: [receipt.items[i] for i in sorted(indices)] for m, indices in item_indices.items()}

    # <<<./ Split to Members
    def split(self, receipt: Receipt, assignments: list[ItemAssignment], members: list[str]):
        self.validate(receipt, assignments, members)
        item_subtotals = self.calculate_subtotals(receipt, assignments, members)
        charge_shares = self.calculate_charge_share(receipt, item_subtotals, members)
        member_items = self.collect_member_items(receipt, assignments, members)

        results = [
            SplitResult(
                member=m,
                assigned_items=member_items[m],
                item_subtotal=item_subtotals[m],
                charge_share=charge_shares[m],
                total_owed=round(item_subtotals[m] + charge_shares[m], 2))
            for m in members]

        bill = BillResult(
            receipt=receipt,
            members=members,
            assignments=assignments,
            results=results)

        if not bill.is_split_balanced:
            raise CalculationError(
                f'Split is not balanced after calculation.'
                f'Collected: IDR {bill.total_collected:,.0f}.'
                f'Expected: IDR {receipt.total:,.0f}.'
                'This is a floating-point rounding issue. Report as bug')

        return bill