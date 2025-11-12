#获取某个patient 从一个时间点到另一个时间点的所有plan
#return plan, 以方便前端直接显示
from pagelogic.repo import plan_repo


def GetUserPlan(
            id, #获取谁的Plan
            frofrom_when, #从这个时间
            to,   #到这个时间
                ): 
    plan = plan_repo.get_plan_by_user_id(id) 
    #获取用户对应的plan, assume每个用户目前只有一个plan
    
    plan_items = get_all_plan_items_by_plan_id(plan.id)
    #获取每个plan_item
    
    item_ids_to_rules = plan_repo.get_plan_item_rules_by_plan_id(plan.id)
    #获取每个plan_item对应的plan_item_rule
    #item_ids_to_rules 是一个dictionary，
    #Key: plan_item.id
    #Value: 对应的 plan_item_rules
    
    drug_ids = get_drug_ids_from_plan_items(plan_items)
    #获取plan_items中，drug_id对应的drug_name,
    #drug_ids_to_names 应该是一个dictionary
    
    drug_id_to_names = drug_repo.get_names_by_ids(drug_ids)
    #返回一个dictionary
    #key: drug_id
    #value: drug的name 注意，这里具体返回哪个name，或者是不是可以直接返回drug instances？有待讨论
    

    
    #通过上面的5个方法，已经获取了所有需要的信息，开始算法部分
    
    plan_items = fill_drug_names(drug_id_to_names)
    
    
    plan_items = fill_date_and_time(plan_items, item_ids_to_rules)
    #这里设计一下，通过item_ids_to_rules generate出来加上重复后的plan_items，
    #并且每个plan_items需要带上date和time
    #顺便把plan_item的plan_item_rule帮订到plan_item上
    
    plan.plan_items = plan_items
    
    return plan
    
#查看GetUserPlan的demo version，返回一些dummy data方便测试前端
#查看plan,plan_item,plan_item_rules如何定义: repo/plan_repo.py
def GetUserPlanDemo(id, from_when, to_when):
    #想怎么改怎么改
    plan_items = [plan_repo.plan_item(...), plan_repo.plan_item(...), plan_repo.plan_item(...)]
    return plan_repo.plan(1, 1, 2, "Zetian", "Tony", "diabetes", plan_items)
