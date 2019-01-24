from django.conf.urls import url
from .views import *
from . import views

urlpatterns = [
    # url(r'^$', views.index, name='index'),
    url(r'^dashboard', views.index, name='index'),
    # url(r'hp', views.hp, name='hp'),

    url(r'^managedashboard', views.managedashboard, name='managedashboard'),
    url(r'^manageuser', views.manageuser, name='manageuser'),
    url(r'^managepermission', views.managepermission, name='managepermission'),
    url(r'^AJX_GetUserDashboardsNotAssigned/$', views.AJX_GetUserDashboardsNotAssigned, name='AJX_GetUserDashboardsNotAssigned'),
    url(r'^AJX_GetUserDashboardsAssigned/$', views.AJX_GetUserDashboardsAssigned, name='AJX_GetUserDashboardsAssigned'),
    url(r'^AJX_BrowserCloseEvent', views.AJX_BrowserCloseEvent, name='AJX_BrowserCloseEvent'),
    # url(r'^AJX_UpdateReportOrder/$', views.AJX_UpdateReportOrder, name='AJX_UpdateReportOrder'),
    url(r'^changePassword', views.changePassword, name='changePassword'),
    #url(r'home/(?P<userid>\w+)/$', views.home, name='home'),
    url(r'^home', views.home, name='home'),
    url(r'^feedback', views.feedback, name='feedback'),
    url(r'^showfeedback', views.showfeedback, name='showfeedback'),

    #url(r'report/(?P<url>.+)/$', views.report, name='report'),
    #url(r'^report/(?P<id>.+)/$', views.report, name='report'),
    url(r'^report', views.report, name='report'),
    url(r'^login', views.login, name='login'),
    url(r'^logout', views.logout, name='logout'),
	url(r'^$', views.login , name='login')
]