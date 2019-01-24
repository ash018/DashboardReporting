from ReportApp.models import *
from django.db import models
from django.db import connection, connections
import json
from _datetime import datetime
from sqlserver_ado.fields import LegacyDateTimeField


class HitCount:
    sessionId = ''
    userId = ''
    panelName = 'MIS.DIGITAL'
    IPAddress = ''
    deviceName = ''
    menuId = ''

    def __init__(self, sessionId, userId, panelName, IPAddress, deviceName, menuId):
        self.sessionId = sessionId
        self.userId = userId
        self.panelName = panelName
        self.IPAddress = IPAddress
        self.deviceName = deviceName
        self.menuId = menuId

    def UserLogInsert(self):
        userLog = UserLog(SessionID=self.sessionId, UserId=self.userId, Login=datetime.now(), LogOut=datetime.now(), PanelName=self.panelName, IPAddress=self.IPAddress, DeviceName=self.deviceName)
        userLog.save(using='SDMSMIRRORDB')

    def UserLogDetailsInsert(self):
        userLogDetails = UserLogDetails(SessionID=self.sessionId, MenuId=self.menuId, Login=datetime.now(), LogOut=datetime.now())
        userLogDetails.save(using='SDMSMIRRORDB')

    def UserLogOutDetailsInsert(self):
        userLogoutDetails = UserLogOutDetails(SessionID=self.sessionId, MenuId=self.menuId, LogOut=datetime.now())
        userLogoutDetails.save(using='SDMSMIRRORDB')

class TraceLogoutEvent:
    @staticmethod
    def LogOutEventDetect(sessionId):
        userLog = UserLog.objects.using('SDMSMIRRORDB').get(SessionID=sessionId)
        userLog.LogOut = datetime.now()
        userLog.save()
        # Also giving an enrty into Logout Table
        userLogoutDetails = UserLogOutDetails(SessionID=sessionId, MenuId="Logout", LogOut=datetime.now())
        userLogoutDetails.save(using='SDMSMIRRORDB')


