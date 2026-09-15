from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('script/create/', views.script_create, name='script_create'),
    path('script/<int:pk>/', views.script_detail, name='script_detail'),
    path('script/<int:pk>/edit/', views.script_edit, name='script_edit'),
    path('script/<int:pk>/delete/', views.script_delete, name='script_delete'),
    path('script/<int:pk>/execute/', views.script_execute, name='script_execute'),
    path('execution/<int:pk>/', views.execution_detail, name='execution_detail'),
    path('execution/<int:pk>/realtime/', views.execution_realtime, name='execution_realtime'),
    path('execution/<int:pk>/stream/', views.execution_stream, name='execution_stream'),
    path('executions/', views.execution_history, name='execution_history'),
    path('execution/<int:pk>/download/<str:file_type>/', views.download_file, name='download_file'),
    path('excel-explorer/', views.excel_explorer, name='excel_explorer'),
    path('admin-files/', views.admin_files, name='admin_files'),
    path('admin-files/<int:pk>/delete/', views.admin_file_delete, name='admin_file_delete'),
    path('admin-files/<int:pk>/download/', views.admin_file_download, name='admin_file_download'),

    # ── Workflow Produits ──────────────────────────────────────────────────
    path('workflow-produits/', views.workflow_produits, name='workflow_produits'),
    path('workflow-produits/run/', views.workflow_produits_run, name='workflow_produits_run'),
    path('workflow-produits/<int:pk>/progress/', views.workflow_produits_progress, name='workflow_produits_progress'),
    path('workflow-produits/<int:pk>/status/', views.workflow_produits_status, name='workflow_produits_status'),
    path('workflow-produits/<int:pk>/', views.workflow_produits_detail, name='workflow_produits_detail'),
    path('workflow-produits/<int:pk>/download/', views.workflow_produits_download, name='workflow_produits_download'),
    path('workflow-produits/<int:pk>/download/erreurs/', views.workflow_produits_download_erreurs, name='workflow_produits_download_erreurs'),
    path('workflow-produits/<int:pk>/download/dupliques/', views.workflow_produits_download_dupliques, name='workflow_produits_download_dupliques'),
    path('workflow-produits/<int:pk>/download/non-dupliques/', views.workflow_produits_download_non_dupliques, name='workflow_produits_download_non_dupliques'),
    path('workflow-produits/<int:pk>/delete/', views.workflow_produits_delete, name='workflow_produits_delete'),
    path('workflow-produits/<int:pk>/reporting/', views.workflow_produits_reporting, name='workflow_produits_reporting'),
]
