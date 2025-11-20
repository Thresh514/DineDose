from flask import render_template, Blueprint, request, session
from datetime import date, datetime, time as dt_time
from pagelogic.repo import food_repo, drug_repo
from pagelogic.service import plan_service

patient_home_bp = Blueprint('patient_home', __name__)


@patient_home_bp.route('/patient', methods=['GET', 'POST'])
def patient_home():
    return render_template('patient_home.html')


@patient_home_bp.route('/patient/reminder', methods=['GET'])
def patient_reminder_page():
    return render_template('patient_reminder.html')


@patient_home_bp.route('/patient/food', methods=['GET'])
def patient_food_page():
    foods = food_repo.get_foods_locally()
    drugs = drug_repo.drugs
    return render_template('patient_food_category_page.html', foods=foods, drugs=drugs)


@patient_home_bp.route('/patient/plan', methods=['GET'])
def patient_plan_page():
    # 获取当前用户ID
    user_id = session.get('user_id')
    if not user_id:
        # 如果没有登录，返回空数据
        return render_template('patient_plan.html', 
                             morning_items=[], 
                             noon_items=[], 
                             evening_items=[])
    
    # 获取选中的日期（从请求参数，默认今天）
    selected_date_str = request.args.get('date')
    if selected_date_str:
        try:
            selected_date = date.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # 获取该日期所在周的开始和结束日期（用于获取一周的数据）
    # 或者只获取当天的数据
    from_when = selected_date
    to_when = selected_date
    
    # 调用服务获取计划
    try:
        plan = plan_service.get_user_plan(user_id, from_when, to_when)
        if plan is None:
            # 如果没有计划，返回空数据
            return render_template('patient_plan.html', 
                                 morning_items=[], 
                                 noon_items=[], 
                                 evening_items=[],
                                 selected_date=selected_date)
    except Exception as e:
        # 如果获取计划出错（比如用户没有计划），返回空数据
        print(f"Error getting plan: {e}")
        return render_template('patient_plan.html', 
                             morning_items=[], 
                             noon_items=[], 
                             evening_items=[],
                             selected_date=selected_date)
    
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
                         selected_date=selected_date)