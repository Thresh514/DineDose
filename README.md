# DineDose

A healthcare application for managing diet and medication plans remotely.


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
python app.py
```

### Repo Structure
- **app.py**: main file to start the project
- **pagelogic**: backend logic
- **template**: frontend template
- **staic**: store public image, frontend CSS and JS file
- **requirements.txt**: Python package dependencies needed to run the project

| 成员       | 角色定位                           | 主要负责模块                                                   | 具体任务                                                                                                                         |
| -------- | ------------------------------ | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **前端 A** | 🧱 用户端界面开发（Patient View）       | - Reminder 页面<br>- Add Meal 页面<br>- Patient Dashboard 页面 | • 设计模板（HTML + Jinja）<br>• 表单布局和样式（Bootstrap）<br>• 加入“Mark as completed”等交互逻辑（JS）<br>• 与 Flask 路由联调（`/reminder`, `/meal/add`） |
| **前端 B** | 📊 医生端界面开发（Doctor View + 数据展示） | - Doctor Dashboard 页面<br>- View History Charts 页面        | • 设计医生主控台（查看患者、留言）<br>• 集成 Chart.js 绘制图表<br>• 负责通用 base.html 模板（导航栏、页脚）<br>• 调整样式保持全站统一                                      |
| **后端 A** | ⚙️ 功能逻辑实现 + 模型管理               | - Reminder 模块<br>- Meal Intake 模块<br>- History 数据查询接口    | • 编写路由与视图函数<br>• SQLAlchemy 模型 (`Reminder`, `MealEntry`, `Food`)<br>• 实现“标记完成”“添加饮食记录”等数据库操作<br>• 为图表提供数据接口                  |
| **后端 B** | 🧠 计划编辑与仪表盘逻辑 + 数据验证           | - Edit Plan 模块<br>- Dashboard 管理（医生+病人）<br>- 权限与反馈模块     | • 路由：`/plan/edit`, `/dashboard/...`<br>• 设计 Plan、Feedback 模型<br>• 编写表单验证逻辑（Flask-WTF）<br>• 整合医生端与病人端视图的数据源                   |

## Database Schema:
Drug Database
```sql
CREATE TABLE IF NOT EXISTS drugs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_ndc VARCHAR(50) UNIQUE,
    brand_name VARCHAR(255),
    brand_name_base VARCHAR(255),
    generic_name TEXT,
    labeler_name VARCHAR(255),
    dosage_form VARCHAR(255),
    route VARCHAR(255),
    marketing_category VARCHAR(255),
    product_type VARCHAR(255),
    application_number VARCHAR(255),
    marketing_start_date VARCHAR(20),
    listing_expiration_date VARCHAR(20),
    finished BOOLEAN
);

CREATE TABLE IF NOT EXISTS active_ingredients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    drug_ndc VARCHAR(50),
    name VARCHAR(255),
    strength VARCHAR(100),
    FOREIGN KEY (drug_ndc) REFERENCES drugs(product_ndc)
        ON DELETE CASCADE
);
```

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

## Course

CS411 Project

---

*2025 Fall*
