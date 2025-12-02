# Get a patient's plan within a time range and return plan for frontend display
from pagelogic.repo import drug_repo, plan_repo
from datetime import datetime, date, time as dt_time, timedelta

def get_raw_plan(user_id: int):
    """
    For doctor editing: get raw plan + items + rules without expanding schedule,
    and fill in drug_name.
    """
    plan = plan_repo.get_plan_by_user_id(user_id)
    if not plan:
        return None

    items = plan_repo.get_all_plan_items_by_plan_id(plan.id)
    rules_map = plan_repo.get_plan_item_rules_by_plan_id(plan.id)

    # Fill in drug_name
    drug_ids = [it.drug_id for it in items]
    drugs = drug_repo.get_drugs_by_ids_locally(drug_ids)
    drug_map = {d.id: d.generic_name for d in drugs}

    for it in items:
        # Bind first rule if exists
        item_rules = rules_map.get(it.id, [])
        if isinstance(item_rules, (list, tuple)) and item_rules:
            it.plan_item_rule = item_rules[0]
        else:
            it.plan_item_rule = None

        it.drug_name = drug_map.get(it.drug_id)

    plan.plan_items = items
    return plan


def get_user_plan(
            id,
            from_when,
            to_when,
                ):
    """
    Fetches a user's medication plan, expands plan items by their repeat rules
    into actual date/time entries, attaches drug info, and returns a sorted plan
    for frontend display.

    Params:
        id: user_id to get plan for
        from_when: start date/datetime (or None for date.min)
        to_when: end date/datetime (or None for date.max)

    Example:
        plan = get_user_plan(
            id=2,
            from_when=date(2025, 11, 1),
            to_when=date(2025, 12, 31)
        )
    """
    plan = plan_repo.get_plan_by_user_id(id)
    plan_items = plan_repo.get_all_plan_items_by_plan_id(plan.id)
    item_ids_to_rules = plan_repo.get_plan_item_rules_by_plan_id(plan.id)
    
    drug_ids = [item.drug_id for item in plan_items]
    drugs = drug_repo.get_drugs_by_ids_locally(drug_ids)
    drug_id_to_names = {drug.id: drug.generic_name for drug in drugs}

    # Fill in drug names
    for i in range(len(plan_items)):
        plan_items[i].drug_name = drug_id_to_names[plan_items[i].drug_id]

    # Expand plan items with dates/times based on rules
    plan_items = fill_date_and_time(plan_items, item_ids_to_rules, from_when, to_when)
    plan.plan_items = plan_items
    
    return plan


def fill_date_and_time(plan_items, item_ids_to_rules, from_when, to_when):
    """
    Expand plan items based on plan_item_rules within [from_when, to_when],
    returning new plan_items list with specific date, time, and plan_item_rule.
    """

    # Normalize from_when / to_when to date
    if isinstance(from_when, datetime):
        start_date = from_when.date()
    elif isinstance(from_when, date):
        start_date = from_when
    elif from_when is None:
        start_date = date.min
    else:
        start_date = datetime.fromisoformat(from_when).date()

    if isinstance(to_when, datetime):
        end_date = to_when.date()
    elif isinstance(to_when, date):
        end_date = to_when
    elif to_when is None:
        end_date = date.max
    else:
        end_date = datetime.fromisoformat(to_when).date()

    result_items = []

    for item in plan_items:
        rules = item_ids_to_rules.get(item.id)
        if not rules:
            continue

        if not isinstance(rules, (list, tuple)):
            rules = [rules]

        for rule in rules:
            rule_start = rule.start_date
            rule_end = rule.end_date or end_date

            # Actual time range = intersection of rule range and query range
            cur_start = max(rule_start, start_date)
            cur_end = min(rule_end, end_date)

            if cur_start > cur_end:
                continue

            times = rule.times or []  # List of times per day (time or str)

            # ONCE: execute only once
            if rule.repeat_type == 'ONCE':
                if start_date <= rule.start_date <= end_date:
                    if times:
                        for t in times:
                            result_items.append(
                                plan_repo.plan_item(
                                    id=item.id,
                                    plan_id=item.plan_id,
                                    drug_id=item.drug_id,
                                    drug_name=item.drug_name,
                                    dosage=item.dosage,
                                    unit=item.unit,
                                    amount_literal=item.amount_literal,
                                    note=item.note,
                                    date=rule.start_date,
                                    time=t,
                                    plan_item_rule=rule
                                )
                            )
                    else:
                        result_items.append(
                            plan_repo.plan_item(
                                id=item.id,
                                plan_id=item.plan_id,
                                drug_id=item.drug_id,
                                drug_name=item.drug_name,
                                dosage=item.dosage,
                                unit=item.unit,
                                amount_literal=item.amount_literal,
                                note=item.note,
                                date=rule.start_date,
                                time=None,
                                plan_item_rule=rule
                            )
                        )

            # DAILY: repeat daily with interval_value
            elif rule.repeat_type == 'DAILY':
                interval = rule.interval_value or 1  # 1 = daily, 2 = every other day
                d = cur_start
                while d <= cur_end:
                    if times:
                        for t in times:
                            result_items.append(
                                plan_repo.plan_item(
                                    id=item.id,
                                    plan_id=item.plan_id,
                                    drug_id=item.drug_id,
                                    drug_name=item.drug_name,
                                    dosage=item.dosage,
                                    unit=item.unit,
                                    amount_literal=item.amount_literal,
                                    note=item.note,
                                    date=d,
                                    time=t,
                                    plan_item_rule=rule
                                )
                            )
                    else:
                        result_items.append(
                            plan_repo.plan_item(
                                id=item.id,
                                plan_id=item.plan_id,
                                drug_id=item.drug_id,
                                drug_name=item.drug_name,
                                dosage=item.dosage,
                                unit=item.unit,
                                amount_literal=item.amount_literal,
                                note=item.note,
                                date=d,
                                time=None,
                                plan_item_rule=rule
                            )
                        )
                    d += timedelta(days=interval)

            # WEEKLY: repeat weekly with weekday flags
            elif rule.repeat_type == 'WEEKLY':
                d = cur_start
                while d <= cur_end:
                    wd = d.weekday()  # 0=Mon, 6=Sun

                    should_take = (
                        (wd == 0 and rule.mon) or
                        (wd == 1 and rule.tue) or
                        (wd == 2 and rule.wed) or
                        (wd == 3 and rule.thu) or
                        (wd == 4 and rule.fri) or
                        (wd == 5 and rule.sat) or
                        (wd == 6 and rule.sun)
                    )

                    if should_take:
                        if times:
                            for t in times:
                                result_items.append(
                                    plan_repo.plan_item(
                                        id=item.id,
                                        plan_id=item.plan_id,
                                        drug_id=item.drug_id,
                                        drug_name=item.drug_name,
                                        dosage=item.dosage,
                                        unit=item.unit,
                                        amount_literal=item.amount_literal,
                                        note=item.note,
                                        date=d,
                                        time=t,
                                        plan_item_rule=rule
                                    )
                                )
                        else:
                            result_items.append(
                                plan_repo.plan_item(
                                    id=item.id,
                                    plan_id=item.plan_id,
                                    drug_id=item.drug_id,
                                    drug_name=item.drug_name,
                                    dosage=item.dosage,
                                    unit=item.unit,
                                    amount_literal=item.amount_literal,
                                    note=item.note,
                                    date=d,
                                    time=None,
                                    plan_item_rule=rule
                                )
                            )

                    d += timedelta(days=1)

            # PRN: as needed
            elif rule.repeat_type == 'PRN':
                result_items.append(
                    plan_repo.plan_item(
                        id=item.id,
                        plan_id=item.plan_id,
                        drug_id=item.drug_id,
                        drug_name=item.drug_name,
                        dosage=item.dosage,
                        unit=item.unit,
                        amount_literal=item.amount_literal,
                        note=item.note,
                        date=None,
                        time=None,
                        plan_item_rule=rule
                    )
                )

    # Sort results
    def sort_key(pi: plan_repo.plan_item):
        d = pi.date if isinstance(pi.date, date) else date.min
        t = pi.time
        if isinstance(t, str):
            try:
                h, m, *rest = t.split(":")
                s = rest[0] if rest else "00"
                t_val = dt_time(int(h), int(m), int(s))
            except Exception:
                t_val = dt_time.min
        elif isinstance(t, dt_time):
            t_val = t
        else:
            t_val = dt_time.min

        return (d, t_val, pi.id)

    result_items.sort(key=sort_key)
    return result_items