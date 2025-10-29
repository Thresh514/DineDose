from repository.db import db
from domains.user import User

class UserRepository:

    @staticmethod
    def create_user(username, email, role='user'):
        """
        创建用户，可指定角色（默认 user）
        """
        user = User(username=username, email=email, role=role)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_user(user_id, new_username=None, new_email=None, new_role=None):
        """
        更新用户信息，可同时修改 username / email / role
        """
        user = User.query.get(user_id)
        if not user:
            return None
        if new_username:
            user.username = new_username
        if new_email:
            user.email = new_email
        if new_role:
            user.role = new_role
        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        """
        删除用户
        """
        user = User.query.get(user_id)
        if not user:
            return False
        db.session.delete(user)
        db.session.commit()
        return True