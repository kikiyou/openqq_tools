#coding:utf-8
import re
import os
import time
import json.decoder as json_decode
import openQQ, utils
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


def log(logt):
    """

    """
    print logt


def exprs(list_info):
    """
    扩展一些范围的数字
    """
    list_out = set([])
    for l in list_info:
        list_t = re.split(':|,| ', l)
        for feild in list_t:
            if '-' in feild:
                list_r = range(int(feild.split('-')[0]), int(feild.split('-')[1]) + 1)
            else:
                if feild == "":
                    continue
                list_r = [int(feild)]
            list_out = list_out | set(list_r)
    return list(list_out)


def common_get_info():
    """
    get install info
    @return list:
    """
    list_info = []
    print utils.c("请输参数信息（如：115 10.221.8.99 2014-01-17 10:00:00 支持多个服，输入!结束）:", 'b')
    while 1:
        tmp_line = raw_input()
        if tmp_line == '!': break
        if len(tmp_line.split()) != 4:
            print utils.c("输入的数据'%s'格式错误" % tmp_line, 'r')
            return []
        list_info.append(tmp_line)
    return list_info


def show_main():
    """
    显示功能列表
    return type_opts dict:操作类型信息
    """
    os.system("clear")
    type_opts = utils.read_config(ctype="optype")
    print utils.c("==============================================================", 'y')
    print utils.c("操作类型\t| 说明")
    print utils.c("--------------------------------------------------------------", 'y')
    for optype in type_opts.iterkeys():
        print "%s\t| %s" % (utils.c(optype, 'g'), utils.c(type_opts[optype]))
    print "%s\t\t| 退出此程序" % utils.c("exit ", 'g')
    print utils.c("==============================================================", 'y')
    return type_opts


def add_test_server(openqq, cur_games, test_zone_dir, test_name):
    """
    添加测试服到测试大区
    @openqq obj:操作平台的对象
    @cur_games dict:当前游戏区服的字典信息
    @test_zone_dir int:测试大区编号
    @test_name string:当前测试大区游戏名称
    @return list:[zoneid,domain]
    """

    cur_release_games = []
    zoneid, domain = 0, ""
    for key, value in cur_games.iteritems():
        if key != "封闭测试".decode('utf8'):
            cur_release_games.extend(value)

    if not any(map(lambda x: test_name.decode('utf8') == x["server_name"], cur_games["封闭测试".decode('utf8')])):
        log('%s不存在' % test_name)
        ret = openqq.add_newnode(test_zone_dir, test_name)
        log('开始添加%s' % test_name)
        ret_code = re.findall(r'"(iRet|ret)":"?(\d+)"?', ret)[0][1]
        if ret_code == "0":
            zoneid, domain, msg = re.findall(r'"iNewNodeId":"?(\d+)"?.+"sDomainName":"([^"]+)".+"msg":"([^"]+)"', ret)[
                0]
            log('添加%s完成' % test_name)
    else:
        for game in cur_games["封闭测试".decode('utf8')]:
            if test_name.decode('utf8') == game["server_name"]:
                zoneid, domain = game["zone_id"], game["server_domain"]
                log('%s已存在' % test_name)

    ret_code, msg = -1, ""
    if all([zoneid, domain]):
        log("开始修改服务器状态")
        ret = openqq.change_server_status(test_zone_dir, zoneid, 1, 0, 0)
        ret_code, _ = re.findall(r'"(iRet|ret)":"?(\d+)"?.+"msg":"([^"]+)"', ret)[0][1:]

    if ret_code != "0":
        log("修改服务器状态失败")
    else:
        log("修改服务器状态成功")

    return zoneid, domain


def add_pay_entry(openqq, zoneid):
    """
    编辑服务器配置和分区发货配置
    @openqq obj:操作平台的对象
    @zoneid int:大区编号
    @return:none
    """

    #分区发货配置,现网环境
    pay_servers = {1: ("支付一", 9991), 2: ("支付二", 9992), 3: ("支付三", 9993), 0: ("支付四", 9994)}
    pay_server = pay_servers[int(zoneid) % 4]
    ret = openqq.add_zone_info(zoneid, zoneid, pay_server, "1")
    msg = u"修改%s服分区发货配置【%s】，现网环境失败" % (zoneid, pay_server[0])
    if ret:
        ret = json_decode.JSONDecoder().decode(ret)
        msg = ret["msg"] or u"修改%s服分区发货配置【%s】，现网环境成功" % (zoneid, pay_server[0])
    log(msg)


def edit_pay_entry(openqq, zoneid, server_id):
    """
    编辑服务器配置和分区发货配置
    @openqq obj:操作平台的对象
    @zone_id int:大区编号
    @server_id int:服务器编号
    @return:none
    """
    pay_servers = {1: ("支付一", 9991), 2: ("支付二", 9992), 3: ("支付三", 9993), 0: ("支付四", 9994)}
    pay_server = pay_servers[int(zoneid) % 4]
    ret = openqq.edit_zone_info(zoneid, zoneid, pay_server, "1")
    ret_code = -1
    log(u"游戏服[sid=%s zoneid=%s]修改支付到[%s]" % (server_id, zoneid, pay_server[0]))
    msg = u"修改%s服分区发货配置【%s】，现网环境失败" % (server_id, pay_server[0])
    if ret:
        ret = json_decode.JSONDecoder().decode(ret)
        ret_code = ret["code"]
        msg = ret["msg"] or u"修改%s服分区发货配置【%s】，现网环境成功" % (server_id, pay_server[0])
    log(msg)


def update_zone(openqq, ztype, tries=3):
    """
    同步沙箱或者现网
    @openqq obj:操作平台的对象
    @ztype string:1代表现网，0代表沙箱
    @return int:0 or 1
    """
    tr = 1
    while tr <= tries:
        ret_msg = openqq.update_zone(str(ztype))
        ret = re.findall(r"alert\(.(.+).\)", ret_msg)
        if ret and ret[0].strip() == "同步成功！":
            return 1
        else:
            tr += 1
            time.sleep(3)
            print "同步失败，再同步一次，失败信息如下：%s" % ret_msg
    print "同步了%s次了，还是失败了，请手动同步" % tr
    return 0


def bind_domain(openqq, domain, server_ip, mc_gtk, port):
    """
    域名绑定
    @openqq obj:操作平台的对象
    @domain string:域名
    @server_ip string:服务器ip
    @mc_gtk int:安全参数
    @port int:绑定的端口
    @return list: [msg, retcode]
    """
    bind_ret = json_decode.JSONDecoder().decode(openqq.bind_domain(domain, server_ip, mc_gtk, port))
    if bind_ret.get("retcode") == 0:
        task_id = bind_ret["data"]["taskId"]
        task_type = bind_ret["data"]["taskType"]
        time.sleep(10)
        tries = 1
        while tries <= 6:
            task_ret = json_decode.JSONDecoder().decode(openqq.get_task_status(task_id, task_type, mc_gtk))
            if task_ret and task_ret.get("retcode") == 0 and task_ret["data"]["status"] == 0:
                break
            else:
                tries += 1
                time.sleep(20)
        if tries > 6:
            msg = "域名绑定失败"
            retcode = 0
        else:
            msg = "域名绑定成功"
            retcode = 1
    else:
        msg = "域名绑定失败，%s" % (bind_ret.get("errmsg"))
        retcode = 0
    return msg, retcode


def pub_game(openqq):
    """
    发布游戏
    @openqq obj:操作平台的对象
    @return int:1 or 0
    """
    ret = openqq.release()
    ret_code, state = re.findall(r'"(iRet|ret)":"?(\d+)"?.+"msg":"([^"]+)"', ret)[0][1:]
    if ret_code == '000000':
        return 1
    else:
        return 0


def openqq_init_do(list_info, opts):
    """
    开放平台大区、支付、域名等创建和配置
    @list_info list:["115 10.221.8.99 2014-01-17 10:00:00","116 10.221.8.100 2014-01-17 12:00:00"]
    @return game_zones dict:{"519":"570","520":"571","521":"572"}
    """

    #登陆开放平台
    log("开始登陆平台")
    test_dir_no = 25
    openqq = openQQ.OpenQQ(opts)
    openqq.login()
    log_ret = openqq.login()
    log(log_ret.split("'")[-4])
    mc_gtk = openqq.getACSRFToken()

    log("开始获取游戏区服信息")
    cur_games = openqq.get_games()
    log("获取游戏区服信息完毕")
    print utils.c("##############################", 'y')
    game_zones = {}
    for item in list_info:
        #安装测试区
        server_id, server_ip, online_date, online_time = item.split()
        log("开始安装测试%s服" % server_id)
        test_info = add_test_server(openqq, cur_games, test_dir_no, "测试%s服" % server_id)
        if test_info:
            log(u"游戏%s服对应的zoneid是 %s，域名是 %s" % (server_id, test_info[0], test_info[1]))
        else:
            log(u"游戏%s服创建测试大区失败")
            continue

        #支付配置
        zoneid, domain = test_info
        game_zones[str(server_id)] = zoneid
        #add_pay_entry(openqq, zoneid)

        #绑定域名
        log("开始进行域名解析")
        mod = int(server_id) % 4
        router_info = {
            0: "10.168.0.128",
            1: "10.168.0.60",
            2: "10.168.0.61",
            3: "10.168.0.93"
        }
        router_ip = router_info.get(mod)

        msg, retcode = bind_domain(openqq, domain, router_ip, mc_gtk, 80)
        log("游戏%s服，router(%s) %s " % (server_id, "80", msg))

        gateway_port = opts["game_ports"].get("game_%s" % server_ip)
        if gateway_port:
            msg, retcode = bind_domain(openqq, domain, server_ip, mc_gtk, gateway_port)
            log("游戏%s服，游戏网关(%s)%s " % (server_id, gateway_port, msg))
        else:
            log("游戏%s服，游戏网关获取失败，不能继续解析，请手动解析" % server_id)

        #修改服务器状态，去掉游戏服的“荐”，“新“这些状态标志
        ret = openqq.change_server_status(test_dir_no, zoneid, 1, 0, 0)
        ret_code, msg = re.findall(r'"(iRet|ret)":"?(\d+)"?.+"msg":"([^"]+)"', ret)[0][1:]
        msg = msg.decode("unicode_escape")
        if ret_code != "0":
            log('游戏%s服，修改服务器状态失败' % server_id)
        else:
            log('游戏%s服，修改服务器状态成功' % server_id)

        #修改游戏服为正式服，初始化的大区是处于测试状态
        (ret_code, state) = openqq.update_staus(test_dir_no, zoneid, 1)
        if int(ret_code) == 0:
            log("游戏%s服，修改节点状态成功" % server_id)
        else:
            log("游戏%s服，修改节点状态失败" % server_id)

    print utils.c("##############################", 'y')
    log("开始发布游戏")
    retcode = pub_game(openqq)
    if retcode:
        log("游戏发布成功")
    else:
        log("游戏发布失败，请手动发布")

    #log("开始同步沙箱")
    #ret_code = update_zone(openqq, 0)
    #if ret_code:
    #    log("沙箱同步成功")
    #else:
    #    log("沙箱同步失败")

    log("跳过现网同步，请手动同步")
    #log("开始同步现网")
    #ret_code = update_zone(openqq, 1)
    #if ret_code:
    #    log("现网同步成功")
    #else:
    #    log("现网同步失败")

    return game_zones

