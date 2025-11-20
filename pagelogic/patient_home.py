from flask import render_template, Blueprint, request, session
from datetime import date, datetime, time as dt_time, timedelta
from pagelogic.repo import food_repo, drug_repo
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
        if item.time:
            if isinstance(item.time, str):
                try:
                    parts = item.time.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    time_obj = dt_time(hour, minute)
                    time_str = time_obj.strftime('%I:%M %p')
                except (ValueError, IndexError):
                    time_str = item.time
            elif isinstance(item.time, dt_time):
                time_str = item.time.strftime('%I:%M %p')
        
        return {
            'drug_name': item.drug_name or 'Unknown',
            'note': item.note or '',
            'time': time_str,
            'date': item.date,
            'dosage': item.dosage,
            'unit': item.unit
        }
    
    current_reminder_formatted = format_reminder(current_reminder)
    upcoming_reminder_formatted = format_reminder(upcoming_reminder)
    
    return render_template('patient_reminder.html', 
                         current_reminder=current_reminder_formatted, 
                         upcoming_reminder=upcoming_reminder_formatted)


@patient_home_bp.route('/patient/food', methods=['GET'])
def patient_food_page():
    foods = food_repo.get_foods_locally()
    drugs = drug_repo.drugs
    return render_template('patient_food_category_page.html', foods=foods, drugs=drugs)


@patient_home_bp.route('/patient/food/history', methods=['GET'])
def patient_food_history_page():
    """
    食物历史记录页面
    前端页面，后端接口预留：
    - GET /patient/food/history?period=all|today|week|month 获取食物记录列表
    - DELETE /patient/food/history/<record_id> 删除食物记录
    
    数据格式：
    food_records = [
        {
            'id': int,
            'food_name': str,  # 需要关联food表获取
            'eaten_date': date,
            'eaten_time': time,
            'amount_numeric': float,
            'unit': str,
            'amount_literal': str,
            'notes': str,
            'created_at': datetime
        }
    ]
    """
    # TODO: 后端接口实现
    # user_id = session.get('user_id')
    # period = request.args.get('period', 'all')
    # food_records = get_food_records_by_user_and_period(user_id, period)
    
    # 暂时返回空数据，前端已做好空状态处理
    return render_template('patient_food_history.html', food_records=[])


@patient_home_bp.route('/patient/plan', methods=['GET'])
def patient_plan_page():
    # 获取当前用户ID
    user_id = session.get('user_id')
    
    # 获取选中的日期（从请求参数，默认今天）
    selected_date_str = request.args.get('date')
    if selected_date_str:
        try:
            selected_date = date.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # 计算选中日期所在周的开始日期（周日）和结束日期（周六）
    days_since_sunday = (selected_date.weekday() + 1) % 7  # 转换为：0=Sunday, 6=Saturday
    week_start = selected_date - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    
    # 生成一周的日期列表（周日到周六）
    week_dates = []
    for i in range(7):
        week_date = week_start + timedelta(days=i)
        week_dates.append({
            'date': week_date,
            'day_letter': ['S', 'M', 'T', 'W', 'T', 'F', 'S'][i],
            'is_today': week_date == date.today(),
            'is_selected': week_date == selected_date
        })
    
    if not user_id:
        # 如果没有登录，返回空数据
        return render_template('patient_plan.html', 
                             morning_items=[], 
                             noon_items=[], 
                             evening_items=[],
                             selected_date=selected_date,
                             week_dates=week_dates,
                             week_start=week_start,
                             week_end=week_end)
    
    # 获取该日期所在周的所有数据
    from_when = week_start
    to_when = week_end
    
    # 调用服务获取计划
    try:
        plan = plan_service.get_user_plan(user_id, from_when, to_when)
        if plan is None:
            # 如果没有计划，返回空数据
            return render_template('patient_plan.html', 
                                 morning_items=[], 
                                 noon_items=[], 
                                 evening_items=[],
                                 selected_date=selected_date,
                                 week_dates=week_dates,
                                 week_start=week_start,
                                 week_end=week_end)
    except Exception as e:
        # 如果获取计划出错（比如用户没有计划），返回空数据
        print(f"Error getting plan: {e}")
        return render_template('patient_plan.html', 
                             morning_items=[], 
                             noon_items=[], 
                             evening_items=[],
                             selected_date=selected_date,
                             week_dates=week_dates,
                             week_start=week_start,
                             week_end=week_end)
    
    # 过滤出选中日期的 plan_items
    day_items = [item for item in plan.plan_items 
                 if item.date == selected_date]
    
    # 根据时间分组
    morning_items = []
    noon_items = []
    evening_items = []
    
    for item in day_items:
        if item.time is None:
            # 如果没有时间，默认放到中午
            noon_items.append(item)
            continue
        
        # 将 time 转换为可比较的格式
        if isinstance(item.time, str):
            try:
                # 处理字符串格式的时间，如 "08:00:00"
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
        
        # 分组：morning (6-12), noon (12-17), evening (17-24)
        if 6 <= hour < 12:
            morning_items.append(item)
        elif 12 <= hour < 17:
            noon_items.append(item)
        elif 17 <= hour < 24:
            evening_items.append(item)
        else:
            # 0-6 点也归为早晨
            morning_items.append(item)
    
    return render_template('patient_plan.html', 
                         morning_items=morning_items,
                         noon_items=noon_items,
                         evening_items=evening_items,
                         selected_date=selected_date,
                         week_dates=week_dates,
                         week_start=week_start,
                         week_end=week_end)