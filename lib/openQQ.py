# coding=utf-8

import re
import os
import sys
import traceback
import time
import urllib
import random
import hashlib
import urllib2
import cookielib
from BeautifulSoup import BeautifulSoup
import json.encoder as json_encode


#让urllib2支持cookie
cookies = cookielib.LWPCookieJar()
handlers = [
    urllib2.HTTPHandler(),
    urllib2.HTTPSHandler(),
    urllib2.HTTPCookieProcessor(cookies)
]
opnner = urllib2.build_opener(*handlers)
urllib2.install_opener(opnner)


#产生url随机参数
def rand():
    return "0.%s" % ''.join([random.choice([str(j) for j in xrange(9)]) for i in xrange(17)])


#生成时间戳
def rtime():
    return str(time.time()).replace('.', '')


#qq密码加密
def passwd_encrypt(pwd, verifycode1, verifycode2):
    """
    对密码加密
    """

    def hexchar2bin(uin):
        uin_final = ''
        uin = uin.split('\\x')
        for i in uin[1:]:
            uin_final += chr(int(i, 16))
        return uin_final

    password_1 = hashlib.md5(pwd).digest()
    password_2 = hashlib.md5("%s%s" % (password_1, hexchar2bin(verifycode2))).hexdigest().upper()
    password_final = hashlib.md5("%s%s" % (password_2, verifycode1.upper())).hexdigest().upper()
    return password_final


class OpenQQ(object):
    def __init__(self, opts):
        self.appid = opts["appid"]
        self.uin = opts["qq_uin"]
        self.aid = opts["aid"]
        self.passwd = opts["qq_password"]
        self.salt_auth = opts["salt_auth"]

    @property
    def login_sig(self):
        """
        生成安全参数
        """
        url = "http://ui.ptlogin2.qq.com/cgi-bin/login?hide_title_bar=1&no_verifyimg=1&link_target=blank&appid=" + self.appid + "&target=parent&f_url=http%3A%2F%2Fimgcache.qq.com%2Fqzone%2Fvas%2Flogin%2Fjump.html%3Fret%3D1&s_url=http%3A%2F%2Fimgcache.qq.com%2Fqzone%2Fvas%2Flogin%2Fjump.html%3Fret%3D0"
        request = urllib2.Request(url)
        login_sig = "zkGmuln1tf8YN*eLEgqIHYxZFQqKa*2df2HJk-uhVVS*JzWZ*m4dw06G55XUY97u"
        try:
            response = urllib2.urlopen(request).read()
            p = re.compile(r'g_login_sig="(.*)"')
            login_sig = p.search(response).group(1)
        except AttributeError:
            pass
        return login_sig

    def login(self):
        """
        登陆服务器，登陆之前检查是否需要验证码
        """
        param_data = {
            "uin": self.uin,
            "appid": self.aid,
            "login_sig": self.login_sig,
            "u1": "http%3A%2F%2Fimgcache.qq.com%2Fqzone%2Fvas%2Flogin%2Fjump.html%3Fret%3D0"
        }
        url = "http://check.ptlogin2.qq.com/check?uin=%(uin)s&appid=%(appid)s&js_ver=10033&js_type=0&login_sig=%(login_sig)s&u1=%(u1)s&r=0.9162478815443776" % param_data
        request = urllib2.Request(url)
        response = ""
        try:
            response = urllib2.urlopen(request).read()
            m = re.search(r"'(\d)','(.+)','(.+)'", response)
            verifyCode1 = m.group(2)
            verifyCode2 = m.group(3)
            if m.group(1) == "0":
                print u"免验证码！"
            else:
                print u"需要输入验证码！"
                imgurl = "http://captcha.qq.com/getimage?aid=" + self.aid + "&r=0.3268821237981411&uin=" + self.uin
                request = urllib2.Request(imgurl)
                try:
                    response = urllib2.urlopen(request).read()
                    jpg_file = os.path.split(os.path.realpath(sys.argv[0]))[0] + os.sep + "code.gif"
                    with open(jpg_file, "wb") as img:
                        img.write(response)
                    promotStr = "验证码下载完毕(%s)，请输入：" % jpg_file
                    verifyCode1 = raw_input(promotStr)
                except AttributeError:
                    print "获取验证码出错！"
                    return response
                    #登陆开放平台服务器
            param_data = {
                "u": self.uin,
                "p": passwd_encrypt(self.passwd, verifyCode1, verifyCode2),
                "code": verifyCode1,
                "aid": self.aid,
                "login_sig": self.login_sig,
                "u1": "http%3A%2F%2Fimgcache.qq.com%2Fqzone%2Fvas%2Flogin%2Fjump.html%3Fret%3D0"
            }
            url = "http://ptlogin2.qq.com/login?u=%(u)s&p=%(p)s&verifycode=%(code)s&aid=%(aid)s&u1=%(u1)s&h=1&ptredirect=2&ptlang=2052&from_ui=1&dumy=&fp=loginerroralert&action=3-26-16984&mibao_css=&t=1&g=1&js_type=0&js_ver=10033&login_sig=%(login_sig)s" % param_data
            request = urllib2.Request(url)
            try:
                response = urllib2.urlopen(request).read()
            except AttributeError:
                pass
        except AttributeError:
            pass
        return response

    def getACSRFToken(self):
        """
        获取CSRF验证码
        """
        skey = ""
        for cookie in cookies:
            if cookie.name == "skey":
                skey = cookie.value
        if skey:
            i = 0
            h = 5381
            while i < len(skey):
                h += (h << 5) + ord(skey[i])
                i += 1
            return h & 0x7fffffff
        else:
            return 0

    def zones_info(self):
        """
        获取大区信息
        @return dict {
                    zone_id:
                    {"server_name":游戏区服的名称,
                    "node_dir":大区目录编号,
                    "server_status":运营中 or 停机钟,
                    "server_type":正式服 or 测试服,
                    "server_domain":分区域名
                    }

        """
        url = "http://wlop.ieodopen.qq.com/GetDetailInfo.php?iAppId=%s&rd=%s" % (self.appid, rand())
        response = ""
        tries = 1
        while tries <= 3:
            try:
                request = urllib2.Request(url)
                response = urllib2.urlopen(request).read()
                break
            except:
                tries += 1
                time.sleep(5)
        ret_games = {}
        if response:
            soup = BeautifulSoup(response)
            area_level = soup.findAll("div", {"class": "area-level1"})
            for i in area_level:
                area_name = i.findAll("div", {"class": "area-level-name strong"})[0].contents[0].strip()
                if not ret_games.get(area_name):
                    ret_games[area_name] = []
                for j in i.findAll("tr")[1:]:
                    server_name = j.findAll("div", {"class": "area-level-name"})[0].contents[0].strip()
                    server_status = j.findAll("span", {"class": "server_status"})[0].contents[0].strip()
                    server_type = j.findAll("span", {"class": "server_type"})[0].contents[0].strip()
                    server_domain = "unknown"
                    zone_id = -1
                    node_dir = 0
                    for k in j.findAll("a"):
                        domain = re.findall("s\d+.app%s.qqopenapp.com" % self.appid, k.attrs[0][1])
                        if domain:
                            server_domain = domain[0]
                            zone_id = server_domain.split('.')[0].replace('s', '')
                        for attr in k.attrs:
                            if "href" in attr[0] and re.findall("UpdateStatus", attr[1]):
                                node_dir = re.findall(r"\d+", attr[1])[1]
                    ret_games[zone_id] = {"server_name": server_name, "node_dir": node_dir,
                                          "server_status": server_status, "server_type": server_type,
                                          "server_domain": server_domain}
        return ret_games


    def get_games(self):
        url = "http://wlop.ieodopen.qq.com/GetDetailInfo.php?iAppId=%s&rd=%s" % (self.appid, rand())
        response = ""
        tries = 1
        while tries <= 3:
            try:
                request = urllib2.Request(url)
                response = urllib2.urlopen(request).read()
                break
            except:
                tries += 1
                time.sleep(5)
        ret_games = {}
        if response:
            soup = BeautifulSoup(response)
            area_level = soup.findAll("div", {"class": "area-level1"})
            for i in area_level:
                area_name = i.findAll("div", {"class": "area-level-name strong"})[0].contents[0].strip()
                if not ret_games.get(area_name):
                    ret_games[area_name] = []
                for j in i.findAll("tr")[1:]:
                    server_name = j.findAll("div", {"class": "area-level-name"})[0].contents[0].strip()
                    server_status = j.findAll("span", {"class": "server_status"})[0].contents[0].strip()
                    server_type = j.findAll("span", {"class": "server_type"})[0].contents[0].strip()
                    server_domain = "unknown"
                    zone_id = -1
                    for k in j.findAll("a"):
                        domain = re.findall("s\d+.app%s.qqopenapp.com" % self.appid, k.attrs[0][1])
                        if domain:
                            server_domain = domain[0]
                            zone_id = server_domain.split('.')[0].replace('s', '')
                    servere_info = {"server_name": server_name, "zone_id": zone_id, "server_status": server_status,
                                    "server_type": server_type, "server_domain": server_domain}
                    if ret_games[area_name]:
                        ret_games[area_name].append(servere_info)
                    else:
                        ret_games[area_name] = [servere_info]
        return ret_games

    def change_name(self, dirid, nodeid, name):
        response = ""
        param = {"iAppId": self.appid,
                 "iDirId": dirid,
                 "iNodeId": nodeid,
                 "sName": name,
                 "rd": rand(),
                 "_": rtime()
        }
        get_query = urllib.urlencode(param)
        url = "http://wlop.ieodopen.qq.com/ChangeName.php?%s" % get_query
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        if response:
            ret_regx = re.compile(r'.+"(iRet|ret)":(\d+).+"msg":"([^"]+)".+')
            retcode, msg = ret_regx.findall(response)[0][1:]
            msg = msg.decode("unicode_escape")
            return retcode, msg
        return "1", u"出现未知错误"

    def add_newnode(self, dirid, name):
        response = ""
        param = {"iAppId": self.appid,
                 "iDirId": dirid,
                 "sName": name,
                 "rd": rand(),
                 "_": rtime()
        }
        get_query = urllib.urlencode(param)
        url = "http://wlop.ieodopen.qq.com/AddNewNode.php?%s" % get_query
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def update_order(self, dirid, nodeid, order, updown):
        response = ""
        param = {"iAppId": self.appid,
                 "iDirId": dirid,
                 "iNodeId": nodeid,
                 "iOrder": order,
                 "iUpDown": updown,
                 "rd": rand(),
                 "_": rtime()
        }
        get_query = urllib.urlencode(param)
        url = "http://wlop.ieodopen.qq.com/UpdateOrder.php?%s" % get_query
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass

        return response

    def update_staus(self, dirid, nodeid, status):
        """
        停机或者运行
        """
        response = ""
        if status not in [0, 1]:
            return response
        url = "http://wlop.ieodopen.qq.com/UpdateStatus.php?iAppId=%s&iDirId=%s&iNodeId=%s&iStatus=%s&rd=%s&_=%s" % (
            self.appid, dirid, nodeid, status, rand(), rtime())
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        if response:
            ret_regx = re.compile(r'.+"(iRet|ret)":(\d+).+"msg":"([^"]+)".+')
            retcode, msg = ret_regx.findall(response)[0][1:]
            msg = msg.decode("unicode_escape")
            return retcode, msg
        return "1", u"出现未知错误"

    def update_staus_v2(self, dirid, nodeids, status):
        """
        停机或者运行
        """
        response = ""
        if status not in [0, 1]:
            return response
        url = "http://wlop.ieodopen.qq.com/BulkUpdateStatus.php?iAppId=%s&iDirId=%s&iNodeIds=%s&iStatus=%s&rd=%s&_=%s" % (
            self.appid, dirid, '|'.join(nodeids), status, rand(), rtime())
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        if response:
            ret_regx = re.compile(r'.+"(iRet|ret)":(\d+).+"msg":"([^"]+)".+')
            retcode, msg = ret_regx.findall(response)[0][1:]
            msg = msg.decode("unicode_escape")
            return retcode, msg
        return "1", u"出现未知错误"

    def update_server_node(self, dirid, dirid_old, nodeid):
        response = ""
        param = {"iAppId": self.appid,
                 "iDirId": dirid,
                 "iNodeId": nodeid,
                 "iDirId_old": dirid_old,
                 "rd": rand(),
                 "_": rtime()
        }
        get_query = urllib.urlencode(param)
        url = "http://wlop.ieodopen.qq.com/server_manage/UpdateServerNode.php?%s" % get_query
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass

        if response:
            ret_regx = re.compile(r'.+"(iRet|ret)":(\d+).+"msg":"([^"]+)".+')
            retcode, msg = ret_regx.findall(response)[0][1:]
            msg = msg.decode("unicode_escape")
            return retcode, msg
        return "1", u"出现未知错误"

    def offer2_addserver_info(self, nodeid, game_name, server_ip, port, flag):
        response = ""
        r = {"FServerID": nodeid,
             "FServerName": game_name,
             "FAppIP": server_ip,
             "FAppPort": port,
             "FAppRelativeURL": "tx/pay",
             "FOfferID": self.appid,
             "FEnvFlag": flag
        }
        post_data = urllib.urlencode({"info": json_encode.JSONEncoder().encode(r)}).encode("utf-8")
        url = "http://cpay.qq.com/qqzone/offer2/addServerInfo"
        request = urllib2.Request(url, post_data)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def offer2_editserver_info(self, nodeid, game_name, server_ip, port, flag):
        response = ""
        r = {"FServerID": nodeid,
             "FServerName": game_name,
             "FAppIP": server_ip,
             "FAppPort": port,
             "FAppRelativeURL": "tx/pay",
             "FOfferID": self.appid,
             "FEnvFlag": flag
        }
        post_data = urllib.urlencode({"info": json_encode.JSONEncoder().encode(r)}).encode("utf-8")
        url = "http://cpay.qq.com/qqzone/offer2/saveServerInfo"
        request = urllib2.Request(url, post_data)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def add_zone_info(self, nodeid, server_id, pay_server, flag):
        response = ""
        r = {"ZoneID": nodeid,
             "ZoneName": "%s" % server_id,
             "ProvideServerNameList": pay_server[0],
             "ProvideServerIDList": pay_server[1],
             "MpServerNameList": pay_server[0],
             "MpServerIDList": pay_server[1],
             "MarketServerNameList": pay_server[0],
             "MarketServerIDList": pay_server[1],
             "OfferID": self.appid,
             "EnvFlag": flag
        }

        post_data = urllib.urlencode({"info": json_encode.JSONEncoder().encode(r)}).encode("utf-8")
        url = "http://cpay.qq.com/qqzone/offer2/addZoneInfo"
        request = urllib2.Request(url, post_data)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def edit_zone_info(self, nodeid, server_id, pay_server, flag="1"):
        response = ""
        r = {"zoneID": nodeid,
             "zoneName": "%s" % server_id,
             "provideServerNameList": pay_server[0],
             "provideServerIDList": pay_server[1],
             "mpServerNameList": pay_server[0],
             "mpServerIDList": pay_server[1],
             "marketServerNameList": pay_server[0],
             "marketServerIDList": pay_server[1],
             "envFlag": flag
        }
        post_data = urllib.urlencode({"data": json_encode.JSONEncoder().encode(r)}).encode("utf-8")
        url = "http://cpay.qq.com/qqzone/offer2/confirmInfo/%s" % self.appid
        request = urllib2.Request(url, post_data)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def update_zone(self, flag):
        url = "http://cpay.qq.com/qqzone/offer2/updateZone/%s/%s/" % (self.appid, flag)
        request = urllib2.Request(url)
        response = ""
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def bind_domain(self, domain_name, lanips, mc_gtk, port):
        response = ""
        r = {
            "appId": self.appid,
            "domainName": domain_name,
            "lanIps": lanips,
            "mc_gtk": mc_gtk,
            "port": port
        }

        post_data = urllib.urlencode(r).encode("utf-8")
        url = "http://gz.yun.qq.com/ajax/Domain/BindCVMDomain.php"
        request = urllib2.Request(url, post_data)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def change_display(self, dirid, nodeid, display):
        response = ""
        if str(display) not in ["0", "1"]:
            return response

        param = {"iAppId": self.appid,
                 "iDirId": dirid,
                 "iNodeId": nodeid,
                 "iDisplay": display,
                 "rd": rand(),
                 "_": rtime()
        }
        get_query = urllib.urlencode(param)
        url = "http://wlop.ieodopen.qq.com/ChangeDisplay.php?%s" % get_query
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def change_server_status(self, dirid, nodeid, display, isnew=1, isrecommend=1):
        #联通：isp=3,电信=2
        response = ""
        if str(display) not in ["0", "1"]:
            return response

        param = {"iAppId": self.appid,
                 "iDirId": dirid,
                 "iNodeId": nodeid,
                 "iDisplay": display,
                 "iBusyStatus": 0,
                 "iIsRecommend": isrecommend,
                 "iIsNew": isnew,
                 "rd": rand(),
                 "_": rtime()
        }
        get_query = urllib.urlencode(param)
        url = "http://wlop.ieodopen.qq.com/server_manage/UpdateServerStatus.php?%s" % get_query
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
            ret_regx = re.compile(r'.+"(iRet|ret)":(\d+).+')
            ret = ret_regx.findall(response)
            if ret and int(ret[0][1]) == 0:
                response = self.change_display(dirid, nodeid, display)
            else:
                response = ""
        except AttributeError:
            print traceback.format_exc()
            pass
        return response

    def get_task_status(self, task_id, task_type, mc_gtk):
        response = ""
        param = {
            "appId": self.appid,
            "taskId": task_id,
            "mc_gtk": mc_gtk,
            "taskType": task_type
        }
        get_query = urllib.urlencode(param)
        url = "http://gz.yun.qq.com/ajax/GetFlowStatusByTaskId.php?%s" % get_query
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def release(self):
        """
        发布游戏
        """
        response = ""
        param = {"action": "doRealse",
                 "appid": self.appid,
                 "sFrom": "website",
                 "rd": rand(),
                 "_": rtime()
        }
        get_query = urllib.urlencode(param)
        url = "http://wlop.ieodopen.qq.com/preview.php?%s" % get_query
        request = urllib2.Request(url)
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response

    def del_zone_info(self, zone_id, flag="0"):
        response = ""
        r = {"FOfferID": self.appid,
             "FServerID": zone_id,
             "FEnvFlag": flag
        }
        post_data = json_encode.JSONEncoder().encode(r)

        url = "http://cpay.qq.com/qqzone/offer2/delServerInfo"
        request = urllib2.Request(url, post_data)
        print post_data
        try:
            response = urllib2.urlopen(request).read()
        except AttributeError:
            pass
        return response