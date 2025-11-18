# DineDose

A healthcare application for managing diet and medication plans remotely.

Live Demo: [https://dinedose.onrender.com](https://dinedose.onrender.com)

## Development
Run the command below to start development server
```python
python -m venv venv
```

```python
source venv/bin/activate
```

```python
pip install -r requirements.txt
```

```python
gunicorn app:app
```

## How to make a query to DB
conn = mydb()
cur = conn.cursor(dictionary=True)  # ✅ 返回字典格式
query = "SELECT * FROM users WHERE id = %s AND role = 'doctor'"
cur.execute(query, (doctor_id,))
result = cur.fetchone()
cur.close()
conn.close()

### Repo Structure
- **app.py**: Flask app factory & entrypoint (registers Blueprints)
- **pagelogic/**: backend routes and page logic (Blueprints)
- **templates/**: Jinja2 templates (incl. `components/`)
- **static/**: static assets (CSS/JS) and images under `public/`
- **requirements.txt**: Python package dependencies needed to run the project

| 成员       | 角色定位                           | 主要负责模块                                                   | 具体任务                                                                                                                         |
| -------- | ------------------------------ | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **前端 A** | 🧱 用户端界面开发（Patient View）       | - Reminder 页面<br>- Add Meal 页面<br>- Patient Dashboard 页面 | • 设计模板（HTML + Jinja）<br>• 表单布局和样式（Bootstrap）<br>• 加入“Mark as completed”等交互逻辑（JS）<br>• 与 Flask 路由联调（`/reminder`, `/meal/add`） |
| **前端 B** | 📊 医生端界面开发（Doctor View + 数据展示） | - Doctor Dashboard 页面<br>- View History Charts 页面        | • 设计医生主控台（查看患者、留言）<br>• 集成 Chart.js 绘制图表<br>• 负责通用 base.html 模板（导航栏、页脚）<br>• 调整样式保持全站统一                                      |
| **后端 A** | ⚙️ 功能逻辑实现 + 模型管理               | - Reminder 模块<br>- Meal Intake 模块<br>- History 数据查询接口    | • 编写路由与视图函数<br>• SQLAlchemy 模型 (`Reminder`, `MealEntry`, `Food`)<br>• 实现“标记完成”“添加饮食记录”等数据库操作<br>• 为图表提供数据接口                  |
| **后端 B** | 🧠 计划编辑与仪表盘逻辑 + 数据验证           | - Edit Plan 模块<br>- Dashboard 管理（医生+病人）<br>- 权限与反馈模块     | • 路由：`/plan/edit`, `/dashboard/...`<br>• 设计 Plan、Feedback 模型<br>• 编写表单验证逻辑（Flask-WTF）<br>• 整合医生端与病人端视图的数据源                   |

## Database Schema:
### See ```create.sql```

## Team

**DJLS Team**:
- Zetian Jin
- Lingjie Su 
- Jiayong Tu
- Dingwen Yang

## Features

**For Users**:
- View daily medication and diet plans
- Receive notifications for meals/medication
- Get doctor feedback and health tips
- View past data charts

**For Admins**:
- Create/edit diet and medication plans
- Search medicines
- Set notifications and alerts
- View patient data

## Tech Stack

- Web application
- Role-based interface
- SMS/Email notifications

## Session:
Session are set in login.py:

```
    session.update({
        'type': user.get('role', 'patient'),
        'email': email,
        'session_token': secrets.token_hex(16),
        'user_id': user['id']
    })
```
to get it and display to html:
```
<div>{{ session.get('user_id') }}</div>
```

## Course

CS411 Project

---

*2025 Fall*