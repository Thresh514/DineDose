from flask import render_template, Blueprint, request, session, jsonify
from datetime import date, datetime, time as dt_time, timedelta
from pagelogic.repo import food_repo, drug_repo, food_record_repo, drug_record_repo, feedback_repo
from pagelogic.service import plan_service

patient_home_bp = Blueprint('patient_home', __name__)


@patient_home_bp.route('/patient', methods=['GET', 'POST'])
def patient_home():
    return render_template('patient_home.html')


@patient_home_bp.route('/patient/reminder', methods=['GET'])
def patient_reminder_page():
    user_id = session.get('user_id')
    if not user_id:
        return render_template('patient_reminder.html', 
                             current_reminder=None, 
                             upcoming_reminder=None)
    
    # Get plan for today and next 7 days
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
    
    now = datetime.now()
    current_time = now.time()
    current_date = now.date()
    
    current_reminder = None
    upcoming_reminder = None
    
    # Helper function: convert time to comparable format
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
    
    # Sort all plan items by date and time
    sorted_items = sorted(plan.plan_items, 
                         key=lambda x: (x.date or date.max, 
                                       get_item_time(x) or dt_time.max))
    
    # Find current reminder (today, closest to current time)
    today_items = [item for item in sorted_items 
                   if item.date == current_date and get_item_time(item) is not None]
    
    if today_items:
        past_items = [item for item in today_items 
                      if get_item_time(item) < current_time]
        future_items = [item for item in today_items 
                       if get_item_time(item) >= current_time]
        
        if future_items:
            current_reminder = min(future_items, 
                                  key=lambda x: get_item_time(x))
            future_items_sorted = sorted(future_items, 
                                        key=lambda x: get_item_time(x))
            if len(future_items_sorted) > 1:
                upcoming_reminder = future_items_sorted[1]
        elif past_items:
            current_reminder = max(past_items, 
                                  key=lambda x: get_item_time(x))
    
    # If no upcoming reminder found, search future dates
    if not upcoming_reminder:
        future_items = [item for item in sorted_items 
                       if item.date and item.date > current_date]
        if future_items:
            upcoming_reminder = min(future_items, 
                                   key=lambda x: (x.date, get_item_time(x) or dt_time.min))
    
    # If no current reminder, use upcoming as current
    if not current_reminder and upcoming_reminder:
        current_reminder = upcoming_reminder
        upcoming_reminder = None
    
    # Format reminder data
    def format_reminder(item):
        if not item:
            return None
        
        # Format time
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
        
        # Format date as ISO format (for API)
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
    Food detail / add meal page
    """
    food = food_repo.get_food_by_id_locally(food_id)
    if not food:
        return "Food not found", 404
    
    user_id = session.get('user_id', 1)
    
    return render_template('patient_food_detail.html', 
                          food=food.to_dict(), 
                          user_id=user_id)


@patient_home_bp.route('/patient/food/history', methods=['GET'])
def patient_food_history_page():
    """
    Food history page
    Supports filtering: GET /patient/food/history?period=all|today|week|month
    """
    user_id = session.get('user_id')
    if not user_id:
        return render_template('patient_food_history.html', food_records=[])
    
    period = request.args.get('period', 'all')
    records = food_record_repo.get_food_records_by_user_id(user_id)
    
    # Filter by time period
    today = date.today()
    if period == 'today':
        records = [r for r in records if r.eaten_date == today]
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        records = [r for r in records if r.eaten_date >= week_start and r.eaten_date <= today]
    elif period == 'month':
        month_start = date(today.year, today.month, 1)
        records = [r for r in records if r.eaten_date >= month_start and r.eaten_date <= today]
    
    # Join with food table to get food_name
    food_records_with_name = []
    for record in records:
        food = food_repo.get_food_by_id_locally(record.food_id)
        record_dict = {
            'id': record.id,
            'food_id': record.food_id,
            'food_name': food.description if food else 'Unknown Food',
            'eaten_date': record.eaten_date,
            'eaten_time': record.eaten_time,
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


@patient_home_bp.route('/patient/get_feedback', methods=['GET'])
def get_patient_feedback():
    """
    Get doctor feedback for a specific date
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    feedback_date_str = request.args.get('date')
    if not feedback_date_str:
        return jsonify({"error": "date parameter is required"}), 400
    
    try:
        feedback_date = date.fromisoformat(feedback_date_str)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    feedback = feedback_repo.get_feedback_by_date(user_id, feedback_date)
    
    if feedback:
        return jsonify({"feedback": feedback.to_dict()}), 200
    else:
        return jsonify({"feedback": None}), 200


@patient_home_bp.route('/patient/feedback', methods=['GET'])
def patient_feedback_page():
    """
    Patient feedback page - displays all doctor feedbacks
    """
    user_id = session.get('user_id')
    if not user_id:
        return render_template('patient_feedback.html', feedbacks=[])
    
    # Get feedbacks from 3 days before to 3 days after today
    today = date.today()
    start_date = today - timedelta(days=3)
    end_date = today + timedelta(days=3)
    
    try:
        feedbacks = feedback_repo.get_feedbacks_by_date_range(
            patient_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Convert to dict format and format date/time display
        feedbacks_list = []
        for fb in feedbacks:
            fb_dict = fb.to_dict()
            if fb.feedback_date:
                fb_dict['feedback_date_display'] = fb.feedback_date.strftime('%B %d, %Y')
                fb_dict['feedback_date_weekday'] = fb.feedback_date.strftime('%A')
            else:
                fb_dict['feedback_date_display'] = 'Unknown Date'
                fb_dict['feedback_date_weekday'] = ''
            if fb.created_at:
                if isinstance(fb.created_at, datetime):
                    fb_dict['created_at_display'] = fb.created_at.strftime('%I:%M %p')
                else:
                    fb_dict['created_at_display'] = None
            else:
                fb_dict['created_at_display'] = None
            
            feedbacks_list.append(fb_dict)
        
        print(f"DEBUG: Found {len(feedbacks_list)} feedbacks for user {user_id}")
        
    except Exception as e:
        print(f"ERROR: Failed to get feedbacks: {e}")
        import traceback
        traceback.print_exc()
        feedbacks_list = []
    
    return render_template('patient_feedback.html', feedbacks=feedbacks_list, user_id=user_id)


@patient_home_bp.route('/patient/plan', methods=['GET'])
def patient_plan_page():
    user_id = session.get('user_id')

    selected_date_str = request.args.get('date')
    today_date = date.today()
    yesterday_date = today_date - timedelta(days=1)
    if selected_date_str:
        try:
            selected_date = date.fromisoformat(selected_date_str)
        except ValueError:
            selected_date = today_date
    else:
        selected_date = today_date
    
    days_since_sunday = (selected_date.weekday() + 1) % 7  # 0=Sunday, 6=Saturday
    week_start = selected_date - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    
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
        return render_template(
            'patient_plan.html',
            user_id=None,
            morning_items=[], 
            noon_items=[], 
            evening_items=[],
            completed_map={},
            selected_date=selected_date,
            today_date=today_date,
            yesterday_date=yesterday_date,
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
                today_date=today_date,
                yesterday_date=yesterday_date,
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
            today_date=today_date,
            yesterday_date=yesterday_date,
            week_dates=week_dates,
            week_start=week_start,
            week_end=week_end
        )
    
    # Get drug records for this week and build completed_map
    records = drug_record_repo.get_drug_records_by_date_range(
        user_id=user_id,
        start=week_start,
        end=week_end
    )

    completed_map = {}
    for r in records:
        # Must be linked to a plan_item with expected_date
        if r.plan_item_id is None or r.expected_date is None:
            continue

        key = f"{r.plan_item_id}_{r.expected_date.isoformat()}_{r.expected_time.isoformat() if r.expected_time else ''}"

        # Determine EARLY / LATE / ON_TIME using expected_date + expected_time vs updated_at
        timing_status = "ON_TIME"
        if r.updated_at and r.expected_time:
            if r.expected_time:
                expected_dt = datetime.combine(r.expected_date, r.expected_time)
            else:
                expected_dt = datetime.combine(r.expected_date, dt_time.min)

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

        taken_time_str = r.updated_at.isoformat() if r.updated_at else None
        completed_map[key] = {
            "status": timing_status,
            "taken_time": taken_time_str,
        }
    
    # Filter plan_items for selected date
    day_items = [item for item in plan.plan_items if item.date == selected_date]
    
    # Group by time
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
        today_date=today_date,
        yesterday_date=yesterday_date,
        week_dates=week_dates,
        week_start=week_start,
        week_end=week_end
    )