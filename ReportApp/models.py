from django.db import models
from django.db import connection, connections
import json
from datetime import datetime
from sqlserver_ado.fields import LegacyDateTimeField
import urllib3
import urllib.request

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


class Dashboard(models.Model):
    DashboardId = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=100, blank=True, null=True)
    Url = models.CharField(max_length=200, blank=True, null=True)
    ModifyDate = models.DateTimeField(db_column='ModifyDate', blank=True, null=True, auto_now_add=False, auto_now=True)
    ReportDescription = models.CharField(max_length=20, blank=True, null=True)
    GroupId = models.CharField(max_length=50, blank=True, null=True)
    ReportId = models.CharField(max_length=50, blank=True, null=True)
    ReportType  = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'Dashboard'

class UserLog(models.Model):
    SessionID = models.CharField(max_length=100, primary_key=True)
    UserId = models.CharField(max_length=50, blank=True, null=True)
    Login = models.DateTimeField(db_column='Login', blank=True, null=True, auto_now_add=True, auto_now=False)
    LogOut = models.DateTimeField(db_column='LogOut', blank=True, null=True, auto_now_add=False, auto_now=True)
    PanelName = models.CharField(max_length=20, blank=True, null=True)
    IPAddress = models.CharField(max_length=20, blank=True, null=True)
    DeviceName = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'UserLog'


class UserLogDetails(models.Model):
    SessionID = models.CharField(max_length=100, primary_key=True)
    MenuId = models.CharField(max_length=50, blank=True, null=True)
    Login = models.DateTimeField(db_column='Login', blank=True, null=True, auto_now_add=True, auto_now=False)
    LogOut = models.DateTimeField(db_column='LogOut', blank=True, null=True, auto_now_add=False, auto_now=True)

    class Meta:
        managed = False
        db_table = 'UserLogDetails'
        unique_together = ["SessionID","Login"]

class UserLogOutDetails(models.Model):
    SessionID = models.CharField(max_length=100, primary_key=True)
    MenuId = models.CharField(max_length=50, blank=True, null=True)
    LogOut = models.DateTimeField(db_column='LogOut', blank=True, null=True, auto_now_add=True, auto_now=False)

    class Meta:
        managed = False
        db_table = 'UserLogOutDetails'
        unique_together = ["SessionID", "LogOut"]

class UserPanel(models.Model):
    UserId = models.CharField(db_column='UserId', max_length=50, primary_key=True)
    Password = models.CharField(db_column='Password', max_length=50, blank=False, null=False)
    Email = models.CharField(db_column='Email', max_length=100, blank=True, null=True)
    IsActive = models.IntegerField(db_column='IsActive', blank=True, null=True)
    Username = models.CharField(db_column='Username', max_length=200, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'UserPanel'

class UserDashboardMap(models.Model):
    UserId = models.ForeignKey(UserPanel, on_delete=models.CASCADE)
    DashboardId = models.ForeignKey(Dashboard, on_delete=models.CASCADE)
    ReportOrder = models.IntegerField()
    class Meta:
        managed = False
        db_table = 'UserDashboardMap'


def dictfetchall(cur):
    dataset = cur.fetchall()
    columns = [col[0] for col in cur.description]
    return [
        dict(zip(columns, row))
        for row in dataset
        ]

def GetGraphDataForChurn(tables):
    resultSet = []
    for table in tables:
        jsonData = []
        for row in table:
            date = str(row['InvoicePeriod'])[:4] + "-" +  str(row['InvoicePeriod'])[4:6] + "-" + "01"
            obj = {'time': date, 'value': float("{0:.2f}".format(row['ChurnRate']))}
            jsonData.append(obj)
        resultSet.append(json.dumps(jsonData))

    return resultSet

# Check login of a provided username and password
def ValidateLoginDB(user,password):
    cur = connections['default'].cursor()
    cur.execute("SELECT count(*) FROM [dbo].[UserPanel] where UserId = '" + user + "' and Password = '" + password + "' and IsActive = 1")
    total = int(cur.fetchone()[0])
    cur.close()
    if(total > 0):
        return True
    else:
        return False

# Check login of a provided username and password
def GerUsernameFromUserId(userid):
    cur = connections['default'].cursor()
    cur.execute("SELECT username FROM [dbo].[UserPanel] where UserId = '" + userid + "'")
    results = dictfetchall(cur)
    cur.close()
    return results



def GetDashboards(userid):
    cur = connections['default'].cursor()
    cur.execute("SELECT  A.[DashboardId] \
                          ,[Title]\
                          ,[Url]\
                          ,ReportDescription \
                      FROM [dbo].[Dashboard] A inner join\
                        [dbo].[UserPanel] B on A.[DashboardId] = B.[DashboardId]\
                        and B.UserId = '" + userid + "'")
    results = dictfetchall(cur)
    cur.close()
    return results

def GetReportUrl(userid, id):
    cur = connections['default'].cursor()
    cur.execute("SELECT   [Title]\
                          ,[Url]\
                          ,ReportDescription \
                          ,A.DashboardId \
                          ,A.GroupId    \
                          ,A.ReportId   \
                          ,A.ReportType \
                      FROM [dbo].[Dashboard] A inner join\
                        [dbo].[UserDashboardMap] B on A.[DashboardId] = B.[DashboardId]\
                        and B.UserId = '" + userid + "' \
                        and A.DashboardId = " + id)
    result = dictfetchall(cur)
    cur.close()
    return result



##All model functions related to manage dashboard page.
class DashboardClass():
    def GetAllDashboardList(self):
        cur = connections['default'].cursor()
        cur.execute("SELECT  *  FROM [dbo].[Dashboard] order by DashboardId")
        result = dictfetchall(cur)
        cur.close()
        return result

    def InsertDashboardInfo(self, title, description, url, groupId, reportId, reportType):
        add_dashboard = "INSERT INTO dbo.dashboard \
        VALUES('" + title + "', '" + url + "', '" + datetime.now().strftime('%d/%m/%Y') + "', '" + description + "','" + groupId + "', '" + reportId + "', " + str(reportType) + ")"
        print(add_dashboard)
        cur = connections['default'].cursor()
        cur.execute(add_dashboard)
        cur.close()

    def UpdateDashboardInfo(self, dashboardId, title, description, url, groupId, reportId, reportType):
        update_dashboard = "Update dbo.dashboard \
        Set Title = '" + title + "', Url = '" + url + "', ReportDescription = '" + description + "', GroupId = '" + groupId + "', ReportId='" + reportId + "', ReportType=" + str(reportType) + "  Where  DashboardId = " + str(dashboardId)
        # data_dashboard = (title, url, datetime.datetime.strptime(p_date,'%d-%b-%y %H.%M.%S.%f'), description)
        print(update_dashboard)
        cur = connections['default'].cursor()
        cur.execute(update_dashboard)
        cur.close()

    def DeleteDashboardInfo(self,dashboardId):
        delete_dashboard = "Delete from dbo.dashboard Where  DashboardId = " + str(dashboardId)
        cur = connections['default'].cursor()
        cur.execute(delete_dashboard)

        updare_report_order = "update T1  \
                                        set T1.ReportOrder = T2.NewOrder    \
                                        from    \
                                        ( \
                                            select userid,  \
                                                dashboardid,  \
                                                ReportOrder,    \
                                                row_number() over(PARTITION BY userid  order by userid, ReportOrder) as NewOrder  \
                                            from [dbo].[UserDashboardMap]   \
                                        ) as T2     \
                                        inner join [dbo].[UserDashboardMap] as T1 On T1.userid = T2.userid and  T1.dashboardid = T2.dashboardid"
        cur.execute(updare_report_order)
        cur.close()

    def GetPBIEmbeddedReportToken(self, groupId, reportId):
        pbitoken = {}
        try:
            with urllib.request.urlopen("http://192.168.100.61:90/pbiembeddedapi/Home/EmbedReport/" + groupId + "/" + reportId) as url:
                data = json.loads(url.read().decode())
                pbitoken['EmbedToken'] = data['EmbedToken']['Token']
                pbitoken['EmbedUrl'] = data['EmbedUrl']
                pbitoken['Id'] = data['Id']
            return pbitoken
        except:
            return None

    def GetPBIEmbeddedDashboardToken(self, groupId, reportId):
        pbitoken = {}
        try:
            with urllib.request.urlopen("http://192.168.100.61:90/pbiembeddedapi/Home/EmbedDashboard/" + groupId + "/" + reportId) as url:
                data = json.loads(url.read().decode())
                pbitoken['EmbedToken'] = data['EmbedToken']['Token']
                pbitoken['EmbedUrl'] = data['EmbedUrl']
                pbitoken['Id'] = data['Id']
            return pbitoken
        except:
            return None




class UserPanel():
    def GetAllUserList(self):
        cur = connections['default'].cursor()
        cur.execute("SELECT  *  FROM [dbo].[UserPanel] where userid != 'admin' order by UserId")
        result = dictfetchall(cur)
        cur.close()
        return result

    def InsertUserInfo(self, userid, username, password, email, isactive):
        ##Check if the usedid is already available in the database
        cur = connections['default'].cursor()
        cur.execute("SELECT count(*) FROM [dbo].[UserPanel] where UserId = '" + userid + "'")
        total = int(cur.fetchone()[0])
        if total > 0:
            return False
        add_user = "INSERT INTO dbo.UserPanel \
                VALUES('" + userid + "', '" + password + "',  '" + email + "', '" + str(isactive) + "', '" + username + "')"
        print(add_user)
        cur.execute(add_user)
        cur.close()
        return True

    def UpdateUserInfo(self, userid, password, email, isactive):
        update_user = "Update dbo.UserPanel \
        Set Password = '" + password + "', Email = '" + email + "', IsActive = '" + str(isactive) + "' Where  UserId = '" + str(userid) + "'"
        print(update_user)
        cur = connections['default'].cursor()
        cur.execute(update_user)
        cur.close()

    def DeleteUserInfo(self,userid):
        # When a user is deleted, all of his data from [dbo].[UserDashboardMap] will be deleted because of cascade delete is ON is database. After deleting, report order should be updated
        # Only for
        delete_user = "Delete from dbo.UserPanel Where  UserId = '" + str(userid) + "'"
        print(delete_user)
        cur = connections['default'].cursor()
        cur.execute(delete_user)

        # updare_report_order = "update T1  \
        #                         set T1.ReportOrder = T2.NewOrder    \
        #                         from    \
        #                         ( \
        #                             select userid,  \
        #                                 dashboardid,  \
        #                                 ReportOrder,    \
        #                                 row_number() over(PARTITION BY userid  order by userid, ReportOrder) as NewOrder  \
        #                             from [dbo].[UserDashboardMap]   \
        #                         ) as T2     \
        #                         inner join [dbo].[UserDashboardMap] as T1 On T1.userid = T2.userid and  T1.dashboardid = T2.dashboardid     \
        #                         where T1.userid = '" + userid + "'"
        # cur.execute(updare_report_order)
        cur.close()



    def GetAllUserWithDashboard(self):
        dashboard_list = "SELECT B.UserId , B.Email, B.IsActive, C.Title, C.Url, A.ReportOrder, C.ModifyDate, C.ReportDescription \
        FROM [dbo].[UserDashboardMap] A inner join [dbo].[UserPanel] B \
        On A.UserId = B.UserId \
        inner join [dbo].[Dashboard] C \
        On A.DashboardId = C.DashboardId order by B.UserId, A.ReportOrder"
        cur = connections['default'].cursor()
        cur.execute(dashboard_list)
        result = dictfetchall(cur)
        cur.close()
        return result

    def GetDistinctUserList(self):
        distinct_user = "SELECT distinct UserId from dbo.UserPanel where IsActive = 1"
        cur = connections['default'].cursor()
        cur.execute(distinct_user)
        result = dictfetchall(cur)
        cur.close()
        return result

    def GetDistinctDashboardList(self, userid):
        #Get all dashboards that are not already assigned to that user, so that user can be assigned
        distinct_user = "SELECT distinct DashboardId, title from dbo.Dashboard \
                          where \
                          dashboardid not in \
                          ( \
                              Select distinct DashboardId from [dbo].[UserDashboardMap]  \
                              Where UserId = '" + userid + "' \
                          )"
        cur = connections['default'].cursor()
        cur.execute(distinct_user)
        result = dictfetchall(cur)
        cur.close()
        return result

    def GetDashboardsByUser(self, userid):
        distinct_user = "SELECT  B.UserId, C.DashboardId ,C.title ,A.ReportOrder, C.Url, C.ReportDescription \
                              FROM [dbo].[UserDashboardMap] A inner join [dbo].[UserPanel] B \
                              On A.UserId = B.UserId \
                              inner join [dbo].[Dashboard] C \
                              On A.DashboardId = C.DashboardId  \
                          where B.UserId = '" + userid + "' Order by A.ReportOrder"
        cur = connections['default'].cursor()
        cur.execute(distinct_user)
        result = dictfetchall(cur)
        cur.close()
        return result

    def AddNewUserDashboard(self, userid, dashboardId):
        cur = connections['default'].cursor()
        #Check if the mapping exists already or not
        cur.execute("SELECT count(*) FROM [dbo].[UserDashboardMap] where UserId = '" + str(userid) + "' and DashboardId = " + str(dashboardId) )
        total = int(cur.fetchone()[0])
        if total > 0:
            return False

        add_dashboard = "INSERT INTO dbo.UserDashboardMap( [UserId] ,[DashboardId],[ReportOrder] ) \
                        SELECT '" + userid + "' as UserId, " + dashboardId + " as DashboardId, ISNULL(MAX(ReportOrder), 0)  + 1 as ReportOrder  FROM dbo.UserDashboardMap where userid = '" + userid + "'"
        cur.execute(add_dashboard)




        # if reportOrder == 0:    #if reportorder is 0, then update all reports order by 1 and insert the newly coming report to order 1
        #     #update_order = "Update [dbo].[UserDashboardMap] \
        #     #       Set ReportOrder = ReportOrder + 1 Where  UserId = '" + str(userid) + "'"
        #     #cur.execute(update_order)
        #     add_dashboard = "INSERT INTO [dbo].[UserDashboardMap] \
        #         VALUES('" + userid + "', " + str(dashboardId) + ",  0)"
        #     cur.execute(add_dashboard)
        # else:
        #     update_order = "Update [dbo].[UserDashboardMap] \
        #                         Set ReportOrder = ReportOrder + 1 Where  ReportOrder > " + str(reportOrder)
        #     cur.execute(update_order)
        #     new_order = reportOrder+1
        #     add_dashboard = "INSERT INTO [dbo].[UserDashboardMap] \
        #                     VALUES('" + userid + "', " + str(dashboardId) + ", " + str(new_order) + ")"
        #     cur.execute(add_dashboard)
        #
        # # for safety: adjust all report orders
        # updare_report_order = "update T1  \
        #                                set T1.ReportOrder = T2.NewOrder    \
        #                                from    \
        #                                ( \
        #                                    select userid,  \
        #                                        dashboardid,  \
        #                                        ReportOrder,    \
        #                                        row_number() over(PARTITION BY userid  order by userid, ReportOrder) as NewOrder  \
        #                                    from [dbo].[UserDashboardMap]   \
        #                                ) as T2     \
        #                                inner join [dbo].[UserDashboardMap] as T1 On T1.userid = T2.userid and  T1.dashboardid = T2.dashboardid"
        # cur.execute(updare_report_order)

        cur.close()
        return True

    def DeleteReportMapping(self, userid, dashboardId):
        # when a dashboard is deleted, update order of all the remaining dashboards order by order = order - 1
        # First: Get the "to be deleted" report order
        cur = connections['default'].cursor()
        # cur.execute("SELECT reportorder FROM [dbo].[UserDashboardMap] where UserId = '" + userid + "' and DashboardId = " + str(dashboardId) )
        # reportOrder = int(cur.fetchone()[0])
        delete_mapping = "Delete from [dbo].[UserDashboardMap] Where  UserId = '" + str(userid) + "' and DashboardId = "+ str(dashboardId)
        print(delete_mapping)
        cur.execute(delete_mapping)

        # Now for the rest of the reports, update their order
        updare_report_order = "update T1  \
                                       set T1.ReportOrder = T2.NewOrder    \
                                       from    \
                                       ( \
                                           select userid,  \
                                               dashboardid,  \
                                               ReportOrder,    \
                                               row_number() over(PARTITION BY userid  order by userid, ReportOrder) as NewOrder  \
                                           from [dbo].[UserDashboardMap]  where userid = '" + userid + "'  \
                                       ) as T2     \
                                       inner join [dbo].[UserDashboardMap] as T1 On T1.userid = T2.userid and  T1.dashboardid = T2.dashboardid"
        cur.execute(updare_report_order)
        cur.close()

    def UpdateReportOrder(self, userid, strNewOrder):
        cur = connections['default'].cursor()
        # query = "{exec dbo.SP_UpdateReportOrder(?,?)}", (userid, strNewOrder)
        #print('exec SP_UpdateReportOrder ?, ?', userid, '\"' + str(strNewOrder) + '\"')

        #cur.callproc("[dbo].[dbo.SP_UpdateReportOrder]", [userid, strNewOrder])
        #cur.execute('exec SP_UpdateReportOrder ?, ?', userid, strNewOrder)
        params = (userid, strNewOrder)
        query = "exec [dbo].[SP_UpdateReportOrder] '%s', '%s'" % params
        cur.execute(query)
        cur.close()


    def UpdateUserPassword(self, userid, password):
        cur = connections['default'].cursor()
        update_user_password = "Update dbo.UserPanel Set Password = '" + password + "' Where  UserId = '" + str(userid) + "'"
        cur.execute(update_user_password)
        cur.close()


##All model functions related to manage dashboard page.
class Feedback():
    def AddFeedback(self, userid, rating, comment):
        cur = connections['default'].cursor()
        add_feedback = "INSERT INTO dbo.feedback  \
                        VALUES('" + userid + "', " + rating + ", '" + comment + "', '" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "')"
        cur.execute(add_feedback)
        cur.close()

    def GetAllFeedbacks(self, userid):
        cur = connections['default'].cursor()
        get_feedback = "Select * from [dbo].[feedback] order by FeedbackDate desc"
        cur.execute(get_feedback)
        result = dictfetchall(cur)
        cur.close()
        return result