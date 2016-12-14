import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
import json,os,time
import pymysql.cursors
connection = pymysql.connect(host='***********',
                             user='********',
                             password='***********',
                             db='res',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
                             
def reconnect():
    global connection
    try:
        with connection.cursor() as cursor:
            sql = "SELECT un FROM user where id='1'"
            cursor.execute(sql)
        cursor.close()
        print("still on connect")
        
    except Exception as e:  
        
        connection = pymysql.connect(host='us-cdbr-azure-east2-d.cloudapp.net',
                                 user='b6e855a41d86b5',
                                 password='60bbd286',
                                 db='res',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
        print("reconnect succeeded")
                             
define("port", default=80, help="run on the given port", type=int)
 
class CookieHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")
        
    def get_user_type(self):
        user = self.get_current_user()
        with connection.cursor() as cursor:
            sql = "SELECT user_info.TYPE as TYPE FROM user,user_info WHERE user.un='%s' AND user.id = user_info.ID"%(str(user)[2:-1])
            cursor.execute(sql)
            result = cursor.fetchone()
            return result["TYPE"]
        cursor.close()

class IndexHandler(CookieHandler):
    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            initMap = self.getArea()
            self.render('map.html', userName=self.current_user,status="ok",mapData=initMap)
        else:
            initMap = self.getArea()
            self.render('map.html', userName=None,status=None,mapData=initMap)
    
    def post(self):
        postType = self.get_argument("postType")
        initMap = self.getArea()
        if postType == "login":
            username = self.get_argument("username")
            password = self.get_argument("password")
            sqlStatus = self.loginChk(username,password)
            if sqlStatus == "ok":
                self.set_secure_cookie("username", username)
                self.render("map.html",userName=username,status = sqlStatus,mapData=initMap)
            else:
                self.render("map.html",userName=None,status=sqlStatus,mapData=initMap)
        elif postType == "signup":
            username = self.get_argument("username")
            respond = self.signupChk(username)
            if respond != "Taken":
                password = self.get_argument("password")
                cPassword = self.get_argument("cPassword")
                if cPassword != password:
                    self.render("map.html",userName=None,status="Please confirm your password!",mapData=initMap)
                else:
                    lName = self.get_argument("lname")
                    fName = self.get_argument("fname")
                    phone = self.get_argument("phone")
                    email = self.get_argument("email")
                    userID = int(respond) + 1
                    self.signUp(userID,username,password,email,phone,lName,fName)
                    self.set_secure_cookie("username", username)
                    self.render("map.html",status="ok",userName=username,mapData=initMap)
            else:
                self.render("map.html",status="Username has been taken",userName=username,mapData=initMap)    
        elif postType == "chkPrice":
            areaNum = self.get_argument("deptArea")
            s = self.getPrice(areaNum)
            self.write(json.dumps(s))
        elif postType == "loginFromRes":
            username = self.get_argument("un")
            password = self.get_argument("pw")
            chkLogin = self.loginChk(username,password)
            if chkLogin == "ok":
                self.set_secure_cookie("username", username)
                self.write("ok")
            else:
                self.write("failed")
                
        elif postType == "getBalance":
            un = self.get_argument("un")
            s = self.getBalance(un)
            self.write(s)
            
        elif postType == "submitRes":
            un = self.get_argument('un')
            dept = self.get_argument('dept')
            dest = self.get_argument('dest')
            date = self.get_argument('date')
            time = self.get_argument('time')
            size = self.get_argument('size')
            price = self.get_argument('price')
            num = self.get_argument('num')
            s = self.submit(un,dept,dest,date,time,size,price,num)
            self.write(s)
        elif postType == "signUpFromRes":
            un = self.get_argument("un")
            respond = self.signupChk("un")
            if respond != "Taken":
                password = self.get_argument("pw")
                cPassword = self.get_argument("cpw")
                if cPassword != password:
                    self.write("Please Confirm Your Password!")
                else:
                    lName = self.get_argument("lname")
                    fName = self.get_argument("fname")
                    phone = self.get_argument("phone")
                    email = self.get_argument("email")
                    userID = int(respond) + 1
                    self.signUp(userID,un,password,email,phone,lName,fName)
                    self.set_secure_cookie("username", un)
                    self.write("ok")
            else:
                self.write("Username Is Already Taken!") 
            
                
    def getArea(self):
        areaDict = {}
        with connection.cursor() as cursor:
            for num in range (1,15):
                areaArray = []
                sql = "SELECT ID,X,Y FROM `area` WHERE ID='%s'"%(str(num))
                cursor.execute(sql) 
                result = cursor.fetchone()
                if result is None:
                    break
                areaArray.append(result["X"])
                areaArray.append(result["Y"])
                areaDict[str(num)] = areaArray
        cursor.close()  
        return areaDict
        
    def getPrice(self,num):
        with connection.cursor() as cursor:
            sql = "SELECT SETTING,PRICE FROM area_price WHERE ID='%s'"%(str(num))
            cursor.execute(sql)
            result = cursor.fetchone()
        cursor.close()
        return result
        
    def getBalance(self,un):
        with connection.cursor() as cursor:
            sql = "SELECT user_bill.BALANCE FROM user,user_bill WHERE user.id = user_bill.ID AND user.un='%s'"%(un)
            cursor.execute(sql)
            result = cursor.fetchone()
        cursor.close()
        if result == None:
            return "null"
        else:return result
    
    def loginChk(self,un,pw):
        with connection.cursor() as cursor:
            sql = "SELECT un,pw FROM `user` WHERE `un` = '%s'"%(un)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result == None:
                return "un"
            elif result is not None:
                if result['un'] == un and result['pw'] == pw:
                    return "ok"
                elif result['pw'] != pw:
                    return "pw"
                else:return "un"
        cursor.close()
        
    def signupChk(self,un):
        with connection.cursor() as cursor:
            sql = "SELECT un,pw,id FROM `user` WHERE `un` = '%s'"%(un)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result == None:
                sql = "SELECT MAX(id) FROM `user`"
                cursor.execute(sql)
                IDresult = cursor.fetchone()
                return IDresult["MAX(id)"]
            else:
                return("Taken")
        cursor.close()
                
    def signUp(self,ac_id,un,pw,email,phone,fname,lname):
        with connection.cursor() as cursor:
            sql = "INSERT INTO `user` (`id`, `un`, `pw`, `email`, `phone`) VALUES ('%s', '%s', '%s', '%s','%s')"%(ac_id,un,pw,email,phone)
            cursor.execute(sql)
            sql = "INSERT INTO `user_info` (`ID`,`LASTNAME`,`FIRSTNAME`,`TYPE`) VALUES ('%s','%s','%s','2')"%(ac_id,fname,lname)
            cursor.execute(sql)   
            sql = "INSERT INTO `user_bill` (`ID`,`BALANCE`) VALUES ('%s','0')"%(ac_id)
            cursor.execute(sql)
            connection.commit()
        cursor.close()
        
    def submit(self,un,dept,dest,date,time,size,price,num):
        sql = ""
        with connection.cursor() as cursor:
            sql = "SELECT MAX(ID) as num FROM `order`"
            cursor.execute(sql)
            idResult = cursor.fetchone()
            newID = int(idResult["num"]) + 1
            sql = "INSERT INTO `order` (`ID`,`USERNAME`, `DEPT`, `DEST`, `DATE`, `TIME`, `SIZE`,`FARE`,`CUSTNUM`,`CARNUM`,`STATUS`) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','000','P')"%(newID,un,dept,dest,date,time,size,price,num)
            cursor.execute(sql)         
            connection.commit()
            result = cursor.fetchone()
        cursor.close()
        if result == None:
            return "ok"
        else:return result
        cursor.close()

class cpHandler(CookieHandler):
    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            username = self.current_user
            userInfo= self.getInfo(username)
            self.render('cp.html', userName=self.current_user,
                        phone=userInfo["phone"],
                        userType = userInfo["TYPE"],
                        userID = userInfo['id'],
                        email = userInfo['email'],
                        lastName = userInfo['LASTNAME'],
                        firstName = userInfo['FIRSTNAME'],
                        status="ok")
        else:
            self.render('map.html', userName=None,status=None)
            
    def post(self):
        username = self.current_user
        userID = self.get_argument('ID')
        fstName = self.get_argument('firstname')
        lstName = self.get_argument('LASTNAME')
        Phone = self.get_argument('phone')
        Email = self.get_argument('email')
        s = self.editInfo(userID,fstName,lstName,Phone,Email)
        userInfo= self.getInfo(username)
        self.render('cp.html', userName=self.current_user,
                        phone=userInfo["phone"],
                        userType = userInfo["TYPE"],
                        userID = userInfo['id'],
                        email = userInfo['email'],
                        lastName = userInfo['LASTNAME'],
                        firstName = userInfo['FIRSTNAME'],
                        status=s)
                        
    def getInfo(self,un):
        with connection.cursor() as cursor:
            sql = "SELECT * FROM `user`,`user_info` WHERE user.id=user_info.ID AND un = '%s'"%(str(un)[2:-1])
            cursor.execute(sql) 
            result = cursor.fetchone()
        cursor.close()
        return result
        
    def editInfo(self,userID,fstName,lstName,phone,email):
        sql = ""
        with connection.cursor() as cursor:
            sql = "UPDATE (`user`, `user_info`) SET user.email = '%s', user.phone='%s', user_info.FIRSTNAME='%s', user_info.LASTNAME='%s' WHERE user_info.ID=user.id AND user.id= %s"%(email,phone,fstName,lstName,userID)
            cursor.execute(sql)
            result = cursor.fetchone()
            connection.commit()
        cursor.close()
        if result == None:
            return "ok"
        else:
            return result

class CP_PWHandler(CookieHandler):
    global usertype

    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            username = self.current_user
            pwDict = self.getPW(username)
            global usertype,password 
            usertype = self.get_user_type()
            password = pwDict["pw"]
            self.render('cp-pw.html',userName=username,status="ok",userType = usertype)
        else:
            self.render('map.html', userName=None,status="Not Logged in Yet",userType = usertype)
            
    def post(self):
        oldPassword = self.get_argument("oldPassword")
        newPassword = self.get_argument("newPassword")
        cPassword = self.get_argument("cPassword")
        username = self.current_user
        usertype = self.get_user_type()
        if cPassword != newPassword:
            self.render('cp-pw.html',userName=username,userType = usertype,status="Please Confirm Your Password!")
        elif newPassword == oldPassword:
            self.render('cp-pw.html',userName=username,userType = usertype,status="Please Enter A New password!")
        elif oldPassword != password:
            self.render('cp-pw.html',userName=username,userType = usertype,status="Please Enter Correct Old Password!")
        else:
            self.editPW(username,newPassword)
            self.render('cp-pw.html',userName=username,status="ok",userType = usertype)

    def getPW(self,un):
        with connection.cursor() as cursor:
            sql = "SELECT pw FROM `user` WHERE `un` = '%s'"%(str(un)[2:-1])
            cursor.execute(sql) 
            result = cursor.fetchone()
        cursor.close()
        return result     
        
    def editPW(self,un,pw):
        with connection.cursor() as cursor:
            sql = "UPDATE `user` SET user.pw = '%s' WHERE user.un = '%s'"%(pw,str(un)[2:-1])
            cursor.execute(sql) 
            connection.commit()
        cursor.close() 

class CP_PMHandler(CookieHandler):
    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            username = self.current_user
            usertype = self.get_user_type()
            s = self.getBalance(username)
            self.render('cp-pm.html',userName=username,status="ok",userType = usertype,balance=s["BALANCE"])
        else:
            self.render('map.html', userName=None,status="Not Logged in Yet")
    
    def post(self):
        username = self.current_user
        amount = self.get_argument("amount")
        usertype = self.get_user_type()
        s = self.getBalance(username)
        newBalance = int(s["BALANCE"]) + int(amount)
        self.addBalance(username,newBalance)
        self.render('cp-pm.html',userName=username,status="ok",userType = usertype,balance=newBalance)
            
    def getBalance(self,un):
        with connection.cursor() as cursor:
            sql = "SELECT user_bill.BALANCE FROM user,user_bill WHERE user_bill.ID = user.id AND user.un = '%s'"%(str(un)[2:-1])
            cursor.execute(sql) 
            result = cursor.fetchone()
        cursor.close() 
        return result
    
    def addBalance(self,un,newAmount):
        with connection.cursor() as cursor:
            sql = "UPDATE user_bill,user SET user_bill.BALANCE='%s' WHERE user.id = user_bill.ID AND user.un='%s'"%(newAmount,str(un)[2:-1])
            cursor.execute(sql) 
            connection.commit()
        cursor.close() 
            
class Admin_Map(CookieHandler):
    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            username = self.current_user
            initMap = self.getArea()
            areaNum = self.getAreaNum()
            if areaNum != "0":
                self.render('admin-map.html',userName=username,status="ok",areaList = json.dumps(initMap),areas = areaNum)
            else:self.render('admin-map.html',userName=username,status="ok",areaList="None",areas="None")
        else:
            self.render('map.html', userName=None,status="Not Logged in Yet")
            
    def post(self):
        postType = self.get_argument("postType")
        if postType == "deleteAreas":
            areaNum = self.get_argument("areaNum")
            s = self.deleteArea(areaNum)
            self.write(s)
            
        elif postType == "saveAreas":   
            areaNum = self.get_argument("areaNum")
            xCoord = self.get_argument("xCoord")
            yCoord = self.get_argument("yCoord")
            s = self.writeArea(areaNum,xCoord,yCoord)
            self.write(s)
            
        elif postType == "updateAreas":
            areaNum = self.get_argument("areaNum")
            xCoord = self.get_argument("xCoord")
            yCoord = self.get_argument("yCoord")
            s = self.updateArea(areaNum,xCoord,yCoord)
            self.write(s)
            
        elif postType == "selectArea":
            areaNum = self.get_argument("areaNum")
            getArea = self.selectArea(areaNum)
            self.write(json.dumps(getArea))
            
        elif postType == "updatePrices":
            areaNum = self.get_argument("areaNum")
            price = self.get_argument("price")
            setting = self.get_argument("setting")
            s = self.updateAreaPrice(areaNum,setting,price)
            self.write(s)
        
    def getArea(self):
        areaDict = {}
        with connection.cursor() as cursor:
            for num in range (1,15):
                areaArray = []
                sql = "SELECT ID,X,Y FROM `area` WHERE ID='%s'"%(str(num))
                cursor.execute(sql) 
                result = cursor.fetchone()
                if result is None:
                    break
                areaArray.append(result["X"])
                areaArray.append(result["Y"])
                areaDict[str(num)] = areaArray
        cursor.close()
        return areaDict
        
    def getAreaNum(self):
        with connection.cursor() as cursor:
            sql = "SELECT COUNT(ID) as num FROM area"
            cursor.execute(sql) 
            result = cursor.fetchone()
        return result['num']
        cursor.close()  
        
    def selectArea(self,num):
        with connection.cursor() as cursor:
            sql = "SELECT area.ID,area_price.SETTING,area_price.PRICE,area.X,area.Y FROM area_price,area WHERE area_price.ID = area.ID AND area.ID='%s'"%(str(num))            
            cursor.execute(sql) 
            result = cursor.fetchone()
            cursor.close()
        return result
        

    def writeArea(self,num,x,y):
        with connection.cursor() as cursor:  
            sql = "INSERT INTO `area` (`ID`, `X`, `Y`) VALUES ('%s', '%s', '%s')"%(str(num),x,y)
            cursor.execute(sql)
            sql = "INSERT INTO `area_price` (`ID`,`SETTING`,`PRICE`) VALUES('%s','A','0')"%(str(num))
            cursor.execute(sql)
            result = cursor.fetchone()
            connection.commit()
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result
            
    def updateArea(self,num,x,y):
        with connection.cursor() as cursor:  
            sql = "UPDATE `area` SET X = '%s', Y='%s' WHERE ID = '%s'"%(x,y,str(num))
            cursor.execute(sql) 
            result = cursor.fetchone()
            connection.commit()
        cursor.close()              
        if result == None:
            return "ok"
        else:
            return result
            
    def deleteArea(self,num):
        with connection.cursor() as cursor:  
            sql = "DELETE FROM `area_price` WHERE ID='%s'"%(str(num))
            cursor.execute(sql) 
            sql = "DELETE FROM `area` WHERE ID='%s'"%(str(num))
            cursor.execute(sql) 
            sql = "SET @count = 0" #reassign area ID to the rest of areas
            cursor.execute(sql) 
            sql =  "UPDATE `area_price` SET `area_price`.`ID` = @count:= @count + 1"
            cursor.execute(sql) 
            sql = "SET @count = 0" #reassign area ID to the rest of areas
            cursor.execute(sql) 
            sql =  "UPDATE `area` SET `area`.`ID` = @count:= @count + 1"
            cursor.execute(sql) 
            result = cursor.fetchone()
            connection.commit()
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result
            
    def updateAreaPrice(self,num,st,p):
        with connection.cursor() as cursor:  
            sql = "UPDATE `area_price` SET SETTING = '%s', PRICE='%s' WHERE ID = '%s'"%(st,p,str(num))
            cursor.execute(sql) 
            result = cursor.fetchone()
            connection.commit()  
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result
    
        
class Admin_User_Handler(CookieHandler):
    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            username = self.current_user
            usertype = self.get_user_type()
            self.render('admin-users.html',userName=username,status="ok",userType = usertype)
        else:
            self.render('map.html', userName=None,status="Not Logged in Yet")
    
    def post(self):
        postType = self.get_argument('postType')
        if postType == 'getResult':
            userToFind = self.get_argument('userName')
            searchType = self.get_argument('searchType')
            s = self.getUsers(userToFind,searchType)
            self.write(json.dumps(s))
            
        elif postType == 'updateResult':
            userID = self.get_argument('uID')
            username = self.get_argument('userName')
            pw = self.get_argument('pw')
            fName = self.get_argument('fname')
            lName = self.get_argument('lname')
            email = self.get_argument('email')
            phoneNum = self.get_argument('phone')
            uType = self.get_argument('userType')
            updateStatus = self.updateUser(userID,username,pw,fName,lName,email,phoneNum,uType)
            self.write(updateStatus)
            
        elif postType == 'deleteResult':
            userID = self.get_argument('uID')
            updateStatus = self.deleteUser(userID)
            self.write(updateStatus)
        
    def getUsers(self,user,sType):
        dataToPass = {}
        sql = ""
        with connection.cursor() as cursor:  
            if sType != "0":
                sql = "SELECT * FROM `user`,`user_info` WHERE user.id = user_info.ID AND user_info.TYPE = '%s' AND user.un like '%s'"%(sType,"%" + str(user) + '%')
            else:
                sql = "SELECT * FROM `user`,`user_info` WHERE user.id = user_info.ID AND user.un like '%s'"%("%" + str(user) + '%')
            cursor.execute(sql) 
            result = cursor.fetchall()
            connection.commit()
        cursor.close()  
        n = 1        
        for user in result:
            dataToPass[str(n)] = user
            n += 1
        return dataToPass
        
    def updateUser(self,uID,un,pw,em,phone,fname,lname,uType):
        with connection.cursor() as cursor:
            sql = "UPDATE `user` SET un = '%s', pw='%s' ,email='%s',phone='%s' WHERE id = '%s'"%(un,pw,em,phone,str(uID))
            cursor.execute(sql) 
            sql = "UPDATE `user_info` SET FIRSTNAME='%s',LASTNAME='%s',TYPE='%s' WHERE ID='%s'"%(fname,lname,uType,str(uID))
            cursor.execute(sql) 
            result = cursor.fetchone()
            connection.commit()
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result
            
    def deleteUser(self,uID):
        with connection.cursor() as cursor:  
            sql = "DELETE FROM `res`.`user` WHERE id='%s'"%(str(uID))
            cursor.execute(sql) 
            sql1 = "SET @count = 0" #reassign area ID to the rest of areas
            cursor.execute(sql1) 
            sql =  "UPDATE `user` SET `id` = @count:= @count + 1"
            cursor.execute(sql) 
            result = cursor.fetchone()
            connection.commit()
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result
            
class Admin_Res_Handler(CookieHandler):
    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            username = self.current_user
            usertype = self.get_user_type()
            self.render('admin-res.html',userName=username,status="ok",userType = usertype)
        else:
            self.render('map.html', userName=None,status="Not Logged in Yet")
            
    def post(self):
        postType = self.get_argument("postType")
        if postType == "getResult":
            data = {}
            n = 1
            infoType = self.get_argument("infoType")
            info = self.get_argument("info")
            s = self.searchRes(infoType,info)
            for res in s:
                data[str(n)] = res
                n += 1
            self.write(json.dumps(data))
        elif postType == "delRes":
            resID = self.get_argument("resID")
            s = self.deleteRes(resID)
            self.write(s)
        elif postType == "updateRes":
            resID = self.get_argument("resID")
            status = self.get_argument("status")
            time = self.get_argument("time")
            date = self.get_argument("date")
            dept = self.get_argument("dept")
            dest = self.get_argument("dest")
            size = self.get_argument("size")
            custNum = self.get_argument("custNum")
            fare = self.get_argument("fare")
            carNum = self.get_argument("carNum")
            coord = self.get_argument("coord",default=None)
            s = self.updateRes(resID,status,time,date,dept,dest,size,custNum,fare,carNum,coord)
            self.write(s)
        elif postType == "getDriver":
            infoType = self.get_argument("infoType")
            data = {}
            n = 1
            s = self.getDriver(infoType)
            for dr in s:
                data[str(n)] = dr
                n+=1 
            self.write(json.dumps(data))
        elif postType == "unassign":
            carNum = self.get_argument("carNum")
            s = self.cancelDriver(carNum)
            self.write(s)
        elif postType == "drCoord":
            carNum = self.get_argument("carNum")
            s = self.getDriverCoord(carNum)
            self.write(json.dumps(s))
            
                
    def searchRes(self,infoType,info):
        with connection.cursor() as cursor:  
            infoStr = '%' + str(info) + '%'
            tp = ""
            if infoType == "I":
                tp = "ID"
            elif infoType == "U":
                tp = "USERNAME"
            elif infoType == "D":
                tp = "CARNUM"
            elif infoType == "S":
                tp = "STATUS"
            elif infoType == "P":
                tp = "FARE"
            sql = "SELECT * FROM `order` WHERE %s like '%s'"%(tp,infoStr)
            cursor.execute(sql) 
            result = cursor.fetchall()
            connection.commit()
        cursor.close()  
        return result
    
    def updateRes(self,resID,status,time,date,dept,dest,size,custNum,fare,carNum,coord):
        with connection.cursor() as cursor:  
            sql = "UPDATE `order` SET `STATUS`='%s',`TIME`='%s',`DATE`='%s',`DEPT`='%s',`DEST`='%s',`SIZE`='%s',`CUSTNUM`='%s',`FARE`='%s',`CARNUM`='%s' WHERE ID='%s'"%(status,time,date,dept,dest,size,custNum,fare,carNum,str(resID))
            cursor.execute(sql) 
            result1 = cursor.fetchone()
            if carNum != "0":
                sql = "UPDATE `driver_info` SET `CURRENTJOB`='%s',`COORD`='%s' WHERE CAR_NUM = '%s'"%(resID,coord,carNum)
                cursor.execute(sql)
            connection.commit()  
            result2 = cursor.fetchone()
        cursor.close()  
        if result1 == None and result2 == None:
            return "ok"
        else:
            return result1
        
    def deleteRes(self,resID):
        with connection.cursor() as cursor:  
            sql = "UPDATE `order` SET `STATUS` = 'D' WHERE ID='%s'"%(str(resID))
            cursor.execute(sql) 
            result = cursor.fetchone()
            connection.commit()
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result
            
    def getDriver(self,infoType):
        sql = ""
        with connection.cursor() as cursor: 
            if infoType == "all":
                sql = "SELECT * FROM driver_info"
            elif infoType == "avb":
                sql = "SELECT * FROM driver_info WHERE CURRENTJOB = '0' AND CURRENTJOB != '999'"
            cursor.execute(sql) 
            result = cursor.fetchall()
        cursor.close()  
        return result
        
    def getDriverCoord(self,carNum):
        with connection.cursor() as cursor: 
            sql = "SELECT COORD FROM driver_info WHERE CAR_NUM='%s'"%(carNum)
            cursor.execute(sql) 
            result = cursor.fetchone()
        cursor.close()  
        return result
        
    def cancelDriver(self,carNum):
        with connection.cursor() as cursor:
            sql = "UPDATE `order` SET CARNUM='0',STATUS='P' WHERE CARNUM ='%s'"%(str(carNum))
            cursor.execute(sql)
            sql = "UPDATE driver_info SET CURRENTJOB='0' WHERE CAR_NUM='%s'"%(str(carNum))
            cursor.execute(sql)
            connection.commit()
            result = cursor.fetchone()
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result
            
        
class CP_RLHandler(CookieHandler):
    def get(self):
        pageNum = self.get_argument("page",default=None) 
        ifcookie = self.get_cookie("username")
        if ifcookie and pageNum == None:
            self.redirect("/cp-rl?page=1",True)
        elif pageNum != None and ifcookie:
            username = self.current_user
            usertype = self.get_user_type()
            global currentPage
            currentPage = pageNum
            self.render('res-list.html',userName=username,status="ok",userType = usertype)
        else:
            self.render('map.html', userName=None,status="Not Logged in Yet")
            
    def post(self):
        postType = self.get_argument("postType")
        if postType == "getResList":
            orderDict = {}
            n = 1
            userToFind = self.get_argument('un')
            s = self.getList(userToFind)
            for order in s:
                orderDict[str(n)] = order
                n += 1
            self.write(json.dumps(orderDict))
    
    def getList(self,un):
        with connection.cursor() as cursor:  
            sql = "SELECT ID,DATE,TIME,FARE,CARNUM,STATUS FROM `order` WHERE username = '%s'"%(str(un))
            cursor.execute(sql) 
            result = cursor.fetchall()
        cursor.close()  
        return result
        
class CP_ResDetailedHandler(CookieHandler):
    def get(self):
        resID = self.get_argument("resid",default=None)
        ifcookie = self.get_cookie("username")
        if ifcookie and resID == None:
            self.redirect("/cp-rd?resid=error")
        elif resID != None and ifcookie:
            username = self.current_user
            usertype = self.get_user_type()
            s = self.getlist(resID)
            self.render('res-det.html',userName=username,status="ok",userType = usertype,resInfo = json.dumps(s))
        else:
            self.render('map.html', userName=None,status="Not Logged in Yet")
    
    def getlist(self,resID):
        with connection.cursor() as cursor:  
            sql = "SELECT * FROM `order` WHERE ID = '%s'"%(str(resID))
            cursor.execute(sql) 
            result = cursor.fetchone()
            connection.commit()
        cursor.close()  
        return result
        
class DRHandler(CookieHandler):
    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            username = self.current_user
            usertype = self.get_user_type()
            if usertype == 3:
                self.render('driver.html',userName=username,status="ok",userType = usertype)
            else:self.redirect("/cp?error=deny") #prevent accessing with in-correct user type
        else:
            self.redirect("/?error=deny")
    
    def post(self):
        postType = self.get_argument('postType')
        if postType == "getCurJob":
            username = self.get_argument('un')
            s = self.getDriverJob(username)
            if s == "0":
                self.write(s)
            else:
                self.write(json.dumps(s))
        elif postType == 'getResList':
            username = self.get_argument('un')
            s = self.getResList()
            self.write(json.dumps(s))
        elif postType == "takeRes":
            orderID = self.get_argument('id')
            un = self.get_argument("un")
            s = self.takeOrder(orderID,un)
            self.write(s)
        
    def getDriverJob(self,un):
        sql = ""
        with connection.cursor() as cursor:  
            sql = "SELECT driver_info.CURRENTJOB  as job FROM user,driver_info WHERE user.un='%s' AND user.id = driver_info.ID"%(un)
            cursor.execute(sql) 
            result = cursor.fetchone()
            if str(result['job']) != "0" and str(result["job"]) != "None":
                sql = "SELECT USERNAME FROM `order` WHERE ID='%s'"%(result['job'])
                cursor.execute(sql)
                user = cursor.fetchone()
                sql = "SELECT * FROM `order`,`user`,`user_info` WHERE order.USERNAME ='%s' AND order.USERNAME = user.un AND user.id = user_info.ID"%(user["USERNAME"])
                cursor.execute(sql)
                result = cursor.fetchone()
                return result
            else:
                return result['job']
        cursor.close()  
        
    def getResList(self):
        data = {}
        templeAry = []
        with connection.cursor() as cursor:
            sql = "SELECT * FROM `order`,`user`,`user_info` WHERE order.STATUS = 'P' AND order.USERNAME = user.un AND user.id=user_info.ID"
            cursor.execute(sql)
            result = cursor.fetchall()
            getSorted = False
            while getSorted == False:
                n = 0
                for i in range(0,len(result)):     
                    try:  #sort result by date
                        time = int(result[i]["DATE"] + result[i]["TIME"])
                        nxtTime = int(result[i+1]["DATE"] + result[i+1]["TIME"]) 
                        if time > nxtTime:
                            templeAry = result[i+1]
                            result[i+1] = result[i]
                            result[i] = templeAry
                        else:
                            n +=1 #add 1 to counter if time of current index is smaller than the time of next index
                    except IndexError: #break from if there is no more result
                        break;
                if n == len(result) - 1: #end sorting if there is no more unsorted time 
                    getSorted = True
            for i in range(0,len(result)):
                data[str(i+1)] = result[i]
        cursor.close()  
        return data   
        
        
    def takeOrder(self,oID,un):
        with connection.cursor() as cursor:
            sql = "SELECT driver_info.CAR_NUM as carNum FROM `user`,`driver_info` WHERE user.un='%s' AND user.id = driver_info.ID"%(un)
            cursor.execute(sql)
            result = cursor.fetchone() 
            carNum = result['carNum']
            sql = "UPDATE `order` SET CARNUM='%s',STATUS='C' WHERE ID ='%s'"%(str(carNum),str(oID))
            cursor.execute(sql)
            sql = "UPDATE `driver_info` SET CURRENTJOB='%s' WHERE CAR_NUM='%s'"%(str(oID),str(carNum))
            cursor.execute(sql)
            connection.commit()
            result = cursor.fetchone()
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result
            
class DR_Info_Handler(CookieHandler):
    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            username = self.current_user
            usertype = self.get_user_type()
            userInfo = self.getInfo(username)
            if usertype == 3:
                self.render('driver-info.html',userName=username,
                            status="ok",userType = usertype,
                            userID=userInfo["id"],carNum=userInfo["CAR_NUM"],
                            carModel=userInfo["CAR_MODEL"],carYear=userInfo["CAR_YEAR"],
                            carColor=userInfo["CAR_COLOR"],carSize=userInfo["CAR_SIZE"])
            else:self.redirect("/cp?error=deny") #prevent accessing with in-correct user type
        else:
            self.redirect("/?error=deny") #prevent accessing without login in
    
    def post(self):
        postType = self.get_argument('postType')
        if postType == "updateDr":
            carNum = self.get_argument('num')
            model = self.get_argument('model')
            year = self.get_argument('year')
            color = self.get_argument('color')
            size = self.get_argument('size')
            s = self.updateInfo(carNum,model,year,color,size)
            self.write(s)
    
    def getInfo(self,un):
        with connection.cursor() as cursor:
            sql = "SELECT un.id,dr.CAR_NUM,dr.CAR_SIZE,dr.CAR_MODEL,dr.CAR_YEAR,dr.CAR_COLOR FROM user un,driver_info dr WHERE un.id = dr.ID AND un.un = '%s'"%(str(un)[2:-1])
            cursor.execute(sql)
            result = cursor.fetchone()
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result

    def updateInfo(self,num,model,year,color,size):
        with connection.cursor() as cursor:
            sql = "UPDATE `driver_info` SET CAR_MODEL='%s',CAR_SIZE='%s',CAR_YEAR='%s',CAR_COLOR='%s' WHERE CAR_NUM='%s'"%(model,size,year,color,str(num))
            cursor.execute(sql)
            result = cursor.fetchone()
            connection.commit()
        cursor.close()  
        if result == None:
            return "ok"
        else:
            return result

class admin_Handler(CookieHandler):
    def get(self):
        ifcookie = self.get_cookie("username")
        if ifcookie:
            username = self.current_user
            usertype = self.get_user_type()
            s = self.getWebInfo()
            self.render('admin.html',userName=username,status="ok",userType = usertype,
                        usNum=s["user"],drNum=s["driver"],resNum=s["res"],resP = s["resP"],
                        resC = s["resC"],custNum = s["cust"],adminNum = s["admin"],resD=s["resD"])
        else:
            self.render('map.html', userName=None,status="Not Logged in Yet")
    
    def post(self):
        postType = self.get_argument("postType")
        if postType == "getFile":
            fType = self.get_argument("fType")
            s = self.getFile(fType)  
            self.write(s)
        elif postType == "writeFile":
            fType = self.get_argument("fType")
            s = self.writeFile(fType)  
            self.write(s)
        elif postType == "clrFile":
            fType = self.get_argument("fType")
            s = self.clrFile(fType)
            self.write(s)            
            
    def getFile(self,fType):
        data = {}       
        listFile = os.path.abspath(os.getcwd() + "/static/csv")
        folder = os.listdir(listFile)
        n = 1
        if fType == "User":
            for file in folder:
                if file[0:3] == "urs":
                    data[str(n)] = file
                    n+= 1
        elif fType == "Order":
            for file in folder:
                if file[0:3] == "res":
                    data[str(n)] = file
                    n+= 1
        
        if len(data) != 0:
            return data
        else: return ("None")        
        
    def writeFile(self,uType):
        fileTitle = ""
        firstLine = ""
        sql = ""
        if uType == "User":
            fileTitle = "urs"
            firstLine = "ID,Username,E-mail,Phone#,FirstName,LastName,Type,Balance\n"
            sql = "SELECT * FROM user,user_info,user_bill WHERE user.id = user_info.ID AND user.id = user_bill.ID"
        elif uType == "Order":
            fileTitle = "res"
            firstLine = "ID,Departure,Destination,Date,Time,Size,Customer#,Username,Car#,Status\n"
            sql = "SELECT * FROM `order`"
            
        fileName = fileTitle + time.strftime("%m%d%M%S")
        
        with connection.cursor() as cursor:
            cursor.execute(sql) 
            result = cursor.fetchall()
        cursor.close()
        f = open("static/csv/"+ fileName + ".csv", 'a')
        f.write(firstLine)
        if uType == "User":
            for line in result:
                info = ""
                info += str(line["id"]) + ","
                info += line["un"] + ","
                info += line["email"] + ","
                info += line["phone"] + ","
                info += line["FIRSTNAME"] + ","
                info += line["LASTNAME"] + ","
                info += str(line["TYPE"]) + ","
                info += str(line["BALANCE"]) + "\n"
                f.write(info)
        elif uType == "Order":
            for line in result:
                info = ""
                info += str(line["ID"]) + ","
                info += line["DEPT"] + ","
                info += line["DEST"] + ","
                info += line["DATE"] + ","
                info += line["TIME"] + ","
                info += line["SIZE"] + ","
                info += str(line["CUSTNUM"]) + ","
                info += str(line["USERNAME"]) + ","
                info += str(line["CARNUM"]) + ","
                info += str(line["STATUS"]) + "\n"
                f.write(info)
                
        f.close()
        return "ok"
        
    def clrFile(self,uType):
        fileTitle = ""
        if uType == "User":
            fileTitle = "urs"
        elif uType == "Order":
            fileTitle = "res"
        listFile = os.path.abspath(os.getcwd() + "/static/csv")
        folder = os.listdir(listFile)
        for file in folder:
            if file[0:3] == fileTitle:
                os.remove(listFile + "/" + file)
        
        return "ok"
    
    def getWebInfo(self):
        webInfo = {}
        with connection.cursor() as cursor:
            sql = "SELECT * FROM (SELECT COUNT( ID ) AS p FROM  `order`  WHERE STATUS =  'P') AS p, (SELECT COUNT( ID ) AS a FROM  `order`) AS a, (SELECT COUNT( ID ) AS c FROM  `order`  WHERE STATUS = 'C') AS c, (SELECT COUNT( id ) AS user FROM user) AS u, (SELECT COUNT( ID ) AS dr FROM user_info WHERE TYPE =3) AS dr, (SELECT COUNT( ID ) AS cu FROM user_info WHERE TYPE =2) AS cu,(SELECT COUNT( ID ) AS em FROM user_info WHERE TYPE =1) AS em,(SELECT COUNT( ID ) AS d FROM  `order`  WHERE STATUS = 'D') AS d"
            cursor.execute(sql)
            result = cursor.fetchone()
            webInfo["user"] = result["user"]
            webInfo["driver"] = result["dr"]
            webInfo["admin"] = result["em"]
            webInfo["res"] = result["a"]
            webInfo["resD"] = result["d"]
            webInfo["resP"] = result["p"]
            webInfo["resC"] = result["c"]
            webInfo["cust"] = result["cu"]
        cursor.close()  
        return webInfo
        
class LogoutHandler(CookieHandler):
    def get(self):
        self.clear_cookie("username")
        self.redirect("/")

if __name__ == '__main__':
    
    
    tornado.options.parse_command_line()
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": "72lxDcmqRoiCQMUnqwUDFGNEWdTEH0U5lTxsEM+dh/E=",
        "xsrf_cookies": True,
        "login_url": "/login",
        "debug":True
    }    
    interval_ms = 4 * 60 * 1000
    app = tornado.web.Application(
        handlers=[(r'/',IndexHandler),
                  (r'/logout',LogoutHandler),
                  (r'/cp',cpHandler),
                  (r'/cp-pw',CP_PWHandler),
                  (r'/admin-map',Admin_Map),
                  (r'/admin-user',Admin_User_Handler),
                  (r'/admin-res',Admin_Res_Handler),
                  (r'/cp-pm',CP_PMHandler),
                  (r'/cp-rl',CP_RLHandler),
                  (r'/cp-rd',CP_ResDetailedHandler),
                  (r'/driver',DRHandler),
                  (r'/dr-info',DR_Info_Handler),
                  (r'/admin',admin_Handler)]
                  , **settings)
    main_loop = tornado.ioloop.IOLoop.instance()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    reconnectSQL = tornado.ioloop.PeriodicCallback(reconnect,interval_ms, io_loop = main_loop)
    reconnectSQL.start()
    main_loop.start()
    

