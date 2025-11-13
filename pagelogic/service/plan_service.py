#获取某个patient 从一个时间点到另一个时间点的所有plan
#return plan, 以方便前端直接显示
from pagelogic.repo import drug_repo, plan_repo
from datetime import datetime, date, time as dt_time, timedelta

def get_user_plan(
            id, #获取谁的Plan
            from_when, #从这个时间
            to_when,   #到这个时间
                ):
    """
    Fetches a user’s medication plan, expands plan items by their repeat rules
    into actual date/time entries, attaches drug info, and returns a sorted plan
    for frontend display.

    Param: from_when and to_when should be date or datetime

    sample call:
    ------------------------
    1) 最简单调用(不推荐，推荐specify 时间)
    ------------------------
    plan = get_user_plan(
        id=2,
        from_when=None,
        to_when=None
    )
    print(plan)


    ------------------------
    2) 通过date调用（最推荐，传入date）
    ------------------------
    plan = get_user_plan(
        id=2,
        from_when=date(2025, 11, 1),
        to_when=date(2025, 12, 31)
    )
    print(plan)


    ------------------------
    3) 通过datetime调用
    ------------------------
    plan = get_user_plan(
        id=2,
        from_when=datetime(2025, 11, 11, 8, 0, 0),
        to_when=datetime(2025, 11, 30, 23, 59, 59)
    )
    print(plan)


    ------------------------
    4) 字符串格式
    ------------------------
    plan = get_user_plan(
        id=2,
        from_when="2025-11-11",
        to_when="2025-12-05"
    )
    print(plan)
    """
    plan = plan_repo.get_plan_by_user_id(id) 
    #获取用户对应的plan, assume每个用户目前只有一个plan

    plan_items = plan_repo.get_all_plan_items_by_plan_id(plan.id)
    #获取每个plan_item

    
    item_ids_to_rules = plan_repo.get_plan_item_rules_by_plan_id(plan.id)
    #获取每个plan_item对应的plan_item_rule
    #item_ids_to_rules 是一个dictionary，
    #Key: plan_item.id
    #Value: 对应的 plan_item_rule
    
    drug_ids = [item.drug_id for item in plan_items]
    #获取plan_items中，drug_id对应的drug_name,
    
    drugs = drug_repo.get_drugs_by_ids(drug_ids)
    #返回一个dictionary
    #key: drug_id
    #value: drug的name 注意，这里具体返回哪个name，或者是不是可以直接返回drug instances？有待讨论

    drug_id_to_names = {}
    for drug in drugs:
        drug_id_to_names[drug.id] = drug.generic_name


    #开始算法部分！
  
    # 填充drug name
    for i in range(len(plan_items)):
        plan_items[i].drug_name = drug_id_to_names[plan_items[i].drug_id]

    
    
    plan_items = fill_date_and_time(plan_items, item_ids_to_rules, from_when, to_when)
    #这里设计一下，通过item_ids_to_rules generate出来加上重复后的plan_items，
    #并且每个plan_items需要带上date和time
    #顺便把plan_item的plan_item_rule帮订到plan_item上
    plan.plan_items = plan_items

    
    return plan
from datetime import datetime, date, time as dt_time, timedelta


def fill_date_and_time(plan_items, item_ids_to_rules, from_when, to_when):
    """
    根据 plan_item_rule 展开出[from_when, to_when]内所有具体的服药记录，
    返回新的 plan_items 列表（每条都有具体的 date、time、plan_item_rule）。
    """

    # ------- 1. 统一把 from_when / to_when 变成 date -------

    # 处理 from_when
    if isinstance(from_when, datetime):
        start_date = from_when.date()
    elif isinstance(from_when, date):
        start_date = from_when
    elif from_when is None:
        # 不限制下界 → 用最小日期
        start_date = date.min
    else:
        # 如果你以后想支持字符串，比如 "2025-11-05"
        # 可以用 fromisoformat 解析
        start_date = datetime.fromisoformat(from_when).date()

    # 处理 to_when
    if isinstance(to_when, datetime):
        end_date = to_when.date()
    elif isinstance(to_when, date):
        end_date = to_when
    elif to_when is None:
        # 不限制上界 → 用最大日期
        end_date = date.max
    else:
        end_date = datetime.fromisoformat(to_when).date()

    result_items = []

    for item in plan_items:
        rules = item_ids_to_rules.get(item.id)
        if not rules:
            # 没有规则就跳过
            continue

        # 兼容：如果不是 list，就包一层
        if not isinstance(rules, (list, tuple)):
            rules = [rules]

        for rule in rules:
            # 规则自身的有效时间区间
            rule_start = rule.start_date
            # 如果 rule.end_date 为空，用全局 end_date 顶上
            rule_end = rule.end_date or end_date

            # 实际要生成的时间区间 = 规则区间 ∩ 查询区间
            cur_start = max(rule_start, start_date)
            cur_end = min(rule_end, end_date)

            if cur_start > cur_end:
                # 区间完全不相交
                continue

            times = rule.times or []  # 一天内的服药时间列表（time 或 str）

            # ---------- ONCE：只执行一次 ----------
            if rule.repeat_type == 'ONCE':
                # ONCE 只在 start_date 那天执行一次
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

            # ---------- DAILY：按天、间隔 interval_value ----------
            elif rule.repeat_type == 'DAILY':
                interval = rule.interval_value or 1  # 1 表示每天一次；2 表示隔一天
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

            # ---------- WEEKLY：按周 + 星期几 flag ----------
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

            # ---------- PRN：按需服用 ----------
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

    # ------- 排序 --------
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