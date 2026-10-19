from fastapi import FastAPI
from sqladmin import Admin

from app.admin.auth import AdminAuth
from app.admin.views import all_views
from app.core.settings import settings

from app.core.database.connection import engine

def setup_admin(app: FastAPI) -> Admin:
    auth = AdminAuth(secret_key=settings.ADMIN_SECRET_KEY)
    admin = Admin(app, engine, authentication_backend=auth)
    for view in all_views:
        admin.add_view(view)
    return admin