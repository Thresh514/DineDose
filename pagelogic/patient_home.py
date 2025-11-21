from flask import render_template, Blueprint, request, session
from datetime import date, datetime, time as dt_time, timedelta
from pagelogic.repo import food_repo, drug_repo, food_record_repo, drug_record_repo
from pagelogic.service import plan_service

patient_home_bp = Blueprint('patient_home', __name__)


@patient_home_bp.route('/patient', methods=['GET', 'POST'])
def patient_home():
    return render_template('patient_home.html')


@patient_home_bp.route('/patient/reminder', methods=['GET'])
def patient_reminder_page():
    # 获取当前用户ID
    user_id = session.get('user_id')
    if not user_id:
        # 如果没有登录，返回空数据
        return render_template('patient_reminder.html', 
                             current_reminder=None, 
                             upcoming_reminder=None)
    
    # 获取今天和未来7天的计划
    today = date.today()
    future_date = today + timedelta(days=7)
    
    try:
        plan = plan_service.get_user_plan(user_id, today, future_date)
        if plan is None or not plan.plan_items:
            return render_template('patient_reminder.html', 
                                 current_reminder=None, 
                                 upcoming_reminder=None)
    except Exception as e:
        print(f"Error getting plan for reminder: {e}")
        return render_template('patient_reminder.html', 
                             current_reminder=None, 
                             upcoming_reminder=None)
    
    # 获取当前时间
    now = datetime.now()
    current_time = now.time()
    current_date = now.date()
    
    # 找到当前提醒和即将到来的提醒
    current_reminder = None
    upcoming_reminder = None
    
    # 辅助函数：将时间转换为可比较的格式
    def get_item_time(item):
        if not item.time:
            return None
        if isinstance(item.time, str):
            try:
                parts = item.time.split(':')
                return dt_time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
            except (ValueError, IndexError):
                return None
        elif isinstance(item.time, dt_time):
            return item.time
        return None
    
    # 按日期和时间排序所有计划项
    sorted_items = sorted(plan.plan_items, 
                         key=lambda x: (x.date or date.max, 
                                       get_item_time(x) or dt_time.max))
    
    # 找到当前提醒（今天且时间最接近当前时间）
    today_items = [item for item in sorted_items 
                   if item.date == current_date and get_item_time(item) is not None]
    
    if today_items:
        # 找到今天已过但最近的，或即将到来的最近的
        past_items = [item for item in today_items 
                      if get_item_time(item) < current_time]
        future_items = [item for item in today_items 
                       if get_item_time(item) >= current_time]
        
        if future_items:
            # 有即将到来的，选择最近的
            current_reminder = min(future_items, 
                                  key=lambda x: get_item_time(x))
            # 下一个即将到来的
            future_items_sorted = sorted(future_items, 
                                        key=lambda x: get_item_time(x))
            if len(future_items_sorted) > 1:
                upcoming_reminder = future_items_sorted[1]
        elif past_items:
            # 只有已过的，选择最近的
            current_reminder = max(past_items, 
                                  key=lambda x: get_item_time(x))
    
    # 如果还没有找到即将到来的提醒，从未来日期中找
    if not upcoming_reminder:
        future_items = [item for item in sorted_items 
                       if item.date and item.date > current_date]
        if future_items:
            upcoming_reminder = min(future_items, 
                                   key=lambda x: (x.date, get_item_time(x) or dt_time.min))
    
    # 如果还没有当前提醒，使用即将到来的提醒作为当前提醒
    if not current_reminder and upcoming_reminder:
        current_reminder = upcoming_reminder
        upcoming_reminder = None
    
    # 格式化提醒数据
    def format_reminder(item):
        if not item:
            return None
        
        # 格式化时间
        time_str = "No time"
        time_obj_for_api = None
        if item.time:
            if isinstance(item.time, str):
                try:
                    parts = item.time.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    time_obj_for_api = dt_time(hour, minute)
                    time_str = time_obj_for_api.strftime('%I:%M %p')
                except (ValueError, IndexError):
                    time_str = item.time
            elif isinstance(item.time, dt_time):
                time_obj_for_api = item.time
                time_str = item.time.strftime('%I:%M %p')
        
        # 格式化日期为 ISO 格式（用于 API）
        date_str = None
        if item.date:
            date_str = item.date.isoformat()
        
        return {
            'drug_name': item.drug_name or 'Unknown',
            'note': item.note or '',
            'time': time_str,
            'time_iso': time_obj_for_api.isoformat() if time_obj_for_api else None,
            'date': item.date,
            'date_iso': date_str,
            'dosage': item.dosage,
            'unit': item.unit,
            'plan_item_id': item.id,
            'drug_id': item.drug_id
        }
    
    current_reminder_formatted = format_reminder(current_reminder)
    upcoming_reminder_formatted = format_reminder(upcoming_reminder)
    
    return render_template('patient_reminder.html', 
                         current_reminder=current_reminder_formatted, 
                         upcoming_reminder=upcoming_reminder_formatted,
                         user_id=user_id)


@patient_home_bp.route('/patient/food', methods=['GET'])
def patient_food_page():
    foods = food_repo.get_foods_locally()
    drugs = drug_repo.drugs
    return render_template('patient_food_category_page.html', foods=foods, drugs=drugs)


@patient_home_bp.route('/patient/food/detail/<int:food_id>', methods=['GET'])
def patient_food_detail_page(food_id):
    """
    食物详情/添加餐食页面
    """
    food = food_repo.get_food_by_id_locally(food_id)
    if not food:
        return "Food not found", 404
    
    # 获取当前用户ID（从session）
    user_id = session.get('user_id', 1)  # 默认值，实际应从session获取
    
    return render_template('patient_food_detail.html', 
                          food=food.to_dict(), 
                          user_id=user_id)


@patient_home_bp.route('/patient/food/history', methods=['GET'])
def patient_food_history_page():
    """
    食物历史记录页面
    支持筛选：GET /patient/food/history?period=all|today|week|month
    """
    # 获取当前用户ID
    user_id = session.get('user_id')
    if not user_id:
        return render_template('patient_food_history.html', food_records=[])
    
    # 获取筛选时间段
    period = request.args.get('period', 'all')
    
    # 获取所有食物记录
    records = food_record_repo.get_food_records_by_user_id(user_id)
    
    # 根据时间段筛选
    today = date.today()
    if period == 'today':
        records = [r for r in records if r.eaten_date == today]
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        records = [r for r in records if r.eaten_date >= week_start and r.eaten_date <= today]
    elif period == 'month':
        month_start = date(today.year, today.month, 1)
        records = [r for r in records if r.eaten_date >= month_start and r.eaten_date <= today]
    # period == 'all' 时不需要筛选
    
    # 关联food表获取food_name，构建适合模板的数据结构
    food_records_with_name = []
    for record in records:
        food = food_repo.get_food_by_id_locally(record.food_id)
        # 直接使用record对象的属性，保持date和time对象的原始类型
        record_dict = {
            'id': record.id,
            'food_id': record.food_id,
            'food_name': food.description if food else 'Unknown Food',
            'eaten_date': record.eaten_date,  # date对象
            'eaten_time': record.eaten_time,  # time对象或None
            'amount_numeric': record.amount_numeric,
            'unit': record.unit,
            'amount_literal': record.amount_literal,
            'notes': record.notes,
            'created_at': record.created_at,
            'status': record.status
        }
        food_records_with_name.append(record_dict)
    
    return render_template('patient_food_history.html', 
                          food_records=food_records_with_name, 
                          user_id=user_id,
                          current_period=period)


@patient_home_bp.route('/patient/plan', methods=['GET'])
def patient_plan_page():
    # 从 session 获取当前用户ID
    user_id = session.get('user_id')

    # 获取选中的日期（默认今天）
    selected_date_str = request.args.get('date')
    if selected_date_str:
        try:
            selected_date = date.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # 计算选中日期所在周的开始日期（周日）和结束日期（周六）
    days_since_sunday = (selected_date.weekday() + 1) % 7  # 0=Sunday, 6=Saturday
    week_start = selected_date - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    
    # 一周日期列表
    week_dates = []
    for i in range(7):
        week_date = week_start + timedelta(days=i)
        week_dates.append({
            'date': week_date,
            'day_letter': ['S', 'M', 'T', 'W', 'T', 'F', 'S'][i],
            'is_today': week_date == date.today(),
            'is_selected': week_date == selected_date
        })
    
    # 未登录：空数据
    if not user_id:
        return render_template(
            'patient_plan.html',
            user_id=None,
            morning_items=[], 
            noon_items=[], 
            evening_items=[],
            completed_map={},
            selected_date=selected_date,
            week_dates=week_dates,
            week_start=week_start,
            week_end=week_end
        )
    
    from_when = week_start
    to_when = week_end
    
    try:
        plan = plan_service.get_user_plan(user_id, from_when, to_when)
        if plan is None:
            return render_template(
                'patient_plan.html',
                user_id=user_id,
                morning_items=[], 
                noon_items=[], 
                evening_items=[],
                completed_map={},
                selected_date=selected_date,
                week_dates=week_dates,
                week_start=week_start,
                week_end=week_end
            )
    except Exception as e:
        print(f"Error getting plan: {e}")
        return render_template(
            'patient_plan.html',
            user_id=user_id,
            morning_items=[], 
            noon_items=[], 
            evening_items=[],
            completed_map={},
            selected_date=selected_date,
            week_dates=week_dates,
            week_start=week_start,
            week_end=week_end
        )
    
    # ====== 关键：查这一周内已经记录过的 drug_records，构建 completed_map ======
    # ====== 查这一周内已经记录过的 drug_records，构建 completed_map ======
    records = drug_record_repo.get_drug_records_by_date_range(
        user_id=user_id,
        start=week_start,
        end=week_end
    )

    completed_map = {}
    for r in records:
        # 必须要挂在某个 plan_item 上，且有 expected_date
        if r.plan_item_id is None or r.expected_date is None:
            continue

        key = f"{r.plan_item_id}_{r.expected_date.isoformat()}_{r.expected_time.isoformat() if r.expected_time else ''}"

        # 用 expected_date + expected_time 和 updated_at 来判断 EARLY / LATE / ON_TIME
        timing_status = "ON_TIME"
        if r.updated_at and r.expected_time:
            if r.expected_time:
                expected_dt = datetime.combine(r.expected_date, r.expected_time)
            else:
                expected_dt = datetime.combine(r.expected_date, dt_time.min)

            # updated_at 是 aware，取它的 tzinfo
            tz = r.updated_at.tzinfo
            expected_dt = expected_dt.replace(tzinfo=tz)

            diff_hours = (r.updated_at - expected_dt).total_seconds() / 3600.0
            abs_diff = abs(diff_hours)

            if abs_diff < 1:
                timing_status = "ON_TIME"
            elif diff_hours > 0:
                timing_status = "LATE"
            else:
                timing_status = "EARLY"

        # 记录下实际记录时间（HH:MM）
        taken_time_str = r.updated_at.isoformat() if r.updated_at else None
        # e.g. "2025-11-20T22:16:52.843000"
        completed_map[key] = {
            "status": timing_status,
            "taken_time": taken_time_str,
        }
    
    # 过滤出选中日期的 plan_items
    day_items = [item for item in plan.plan_items if item.date == selected_date]
    
    # 根据时间分组
    morning_items = []
    noon_items = []
    evening_items = []
    
    for item in day_items:
        if item.time is None:
            noon_items.append(item)
            continue
        
        if isinstance(item.time, str):
            try:
                parts = item.time.split(':')
                hour = int(parts[0])
            except (ValueError, IndexError):
                noon_items.append(item)
                continue
        elif isinstance(item.time, dt_time):
            hour = item.time.hour
        else:
            noon_items.append(item)
            continue
        
        if 6 <= hour < 12:
            morning_items.append(item)
        elif 12 <= hour < 17:
            noon_items.append(item)
        elif 17 <= hour < 24:
            evening_items.append(item)
        else:
            morning_items.append(item)
    
    return render_template(
        'patient_plan.html', 
        user_id=user_id,
        morning_items=morning_items,
        noon_items=noon_items,
        evening_items=evening_items,
        completed_map=completed_map,
        selected_date=selected_date,
        week_dates=week_dates,
        week_start=week_start,
        week_end=week_end
    )