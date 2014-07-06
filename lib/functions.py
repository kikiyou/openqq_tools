#coding:utf-8
import traceback
from common import *


def openqq_create():
    """
    平台大区创建操作（zoneid、支付、域名）
    """
    main_opts = utils.read_config()
    list_info = common_get_info()
    #获取游戏服可用的网关端口
    globs = ["game_%s" % i.split()[1] for i in list_info]
    game_ports = get_gateway_port(';'.join(globs))
    main_opts["game_ports"] = game_ports
    if not list_info:
        return 0
    openqq_init_do(list_info, main_opts)


def payment_create():
    """
    支付配置
    """
    #搭建环境
    main_opts = utils.read_config()
    list_info = []
    print utils.c("请输参数信息（格式：[zoneid]如：837 支持多个服，输入!结束）:", 'b')
    while 1:
        tmp_line = raw_input()
        if tmp_line == '!': break
        if len(tmp_line.split()) != 1:
            print utils.c("输入的数据'%s'格式错误" % tmp_line, 'r')
            return 0
        list_info.append(tmp_line)
        #登陆开放平台
    list_info = exprs(list_info)
    openqq = openQQ.OpenQQ(main_opts)
    log_ret = openqq.login()
    log(log_ret.split("'")[-4])
    for zoneid in list_info:
        print utils.c("\n开始创建[zoneid=%s]的支付配置" % zoneid)
        add_pay_entry(openqq, zoneid)


def payment_modify():
    """
    支付修改
    """

    main_opts = utils.read_config()
    list_info = []
    print utils.c("请输参数信息（格式：[sever_id]如：6020支持多个服，输入!结束）:", 'b')
    while 1:
        tmp_line = raw_input()
        if tmp_line == '!': break
        if len(tmp_line.split()) != 1:
            print utils.c("输入的数据'%s'格式错误" % tmp_line, 'r')
            return 0
        list_info.append(tmp_line)
    list_info = exprs(list_info)
    game_zones = {}
    openqq = openQQ.OpenQQ(main_opts)
    log_ret = openqq.login()
    log(log_ret.split("'")[-4])
    log("开始获取游戏区服信息")
    cur_games = openqq.get_games()
    log("获取游戏区服信息完毕")

    print utils.c("##############################", 'y')
    for part_name in cur_games:
        for game in cur_games[part_name]:
                server_id = re.findall("\d+", game["server_name"])
                if server_id:
                    if part_name == "联盟区".decode('utf8'):
                        server_id = str(int(server_id[0]) + 6000)
                    else:
                        server_id = str(server_id[0])
                    game_zones[server_id] = game["zone_id"]
    for server_id in list_info:
        zoneid = game_zones[str(server_id)]
        if zoneid:
            edit_pay_entry(openqq, zoneid, server_id)
        else:
            print utils.c("游戏%s服的zoneid获取不到", 'y')
        time.sleep(0.01)


def payment_sync():
    """
    同步沙箱和现网
    """
    print utils.c("请输入同步类型：现网、沙箱（输入!结束）:", 'b')
    list_info = []
    while 1:
        tmp_line = raw_input()
        if tmp_line == '!': break
        if len(tmp_line.split()) != 1 or tmp_line not in ["现网", "沙箱"]:
            print utils.c("输入的数据'%s'格式错误，请输入‘现网’或者‘沙箱’" % tmp_line, 'r')
            return 0
        list_info.append(tmp_line)
    main_opts = utils.read_config()
    openqq = openQQ.OpenQQ(main_opts)
    log_ret = openqq.login()
    log(log_ret.split("'")[-4])
    mc_gtk = openqq.getACSRFToken()
    for item in list_info:
        if item == "沙箱":
            log("开始同步沙箱")
            ret_code = update_zone(openqq, 0)
            if ret_code:
                log("沙箱同步成功")
            else:
                log("沙箱同步失败")
        elif item == "现网":
            log("开始同步现网")
            ret_code = update_zone(openqq, 1)
            if ret_code:
                log("现网同步成功")
            else:
                log("现网同步失败")
        else:
            print utils.c("暂时不支持'%s'操作" % item)


def openqq_gateway():
    """
    游戏入口操作
    """
    main_opts = utils.read_config()
    openqq = openQQ.OpenQQ(main_opts)
    op1_type = ""
    while 1:
        print "[A] 关平台入口\n[B] 开平台入口\n[C] 退出"
        op1_type = raw_input("请输入操作类型:")
        if op1_type in ['A', 'B', 'C']:
            break
        elif op1_type == "C":
            return
        else:
            continue

    log_ret = openqq.login()
    print log_ret.split("'")[-4]
    print "正在获取大区信息。。。"
    cur_games = openqq.zones_info()
    print "获取大区信息完毕!"
    game_zones = get_z(openqq)

    op2_type = ""
    while 1:
        print "[A] 继续\n[B] 退出"
        op2_type = raw_input("请输入操作类型:")
        if op2_type in ['A', 'B']: break

    if op2_type == 'B':
        sys.exit(0)

    action1 = 0 if op1_type == 'A' else 1
    nodeids = {}
    for k, v in game_zones.iteritems():
        for zone in v.split():
            node_dir = cur_games[zone]["node_dir"]
            if node_dir in nodeids:
                nodeids[node_dir].append(zone)
            else:
                nodeids[node_dir] = [zone]
    for node_dir in nodeids:
        openqq.update_staus_v2(node_dir, nodeids[node_dir], action1)
        time.sleep(0.001)

    cur_games = openqq.zones_info()
    print "查看当前平台入口情况"
    print "#########################"
    for k, v in game_zones.iteritems():
        for zone in v.split():
            try:
                server_status = cur_games[zone]["server_status"]
                print "%s %s" % (cur_games[zone]["server_name"], server_status)
            except:
                print "error:%s desc:%s" % (cur_games[zone]["server_name"], traceback.format_exc())
    op3_type = ""
    while 1:
        print "#########################"
        print "[A] 正式发布\n[B] 退出"
        op3_type = raw_input("请输入操作类型:")
        if op3_type in ['A', 'B']:
            break

    if op3_type == 'A':
        do_ret = openqq.release()
        if int(do_ret.split('"')[3]) == 0:
            print "正式发布成功"
        else:
            print "正式发布失败"


def del_zone_infos():
    """
    删除沙箱环境配置
    """
    main_opts = utils.read_config()
    openqq = openQQ.OpenQQ(main_opts)
    log_ret = openqq.login()
    print log_ret.split("'")[-4]
    list_info = []
    print utils.c("请输参数信息（格式：[zone_id]如：115支持多个服，输入!结束）:", 'b')
    while 1:
        tmp_line = raw_input()
        if tmp_line == '!':
            break
        if len(tmp_line.split()) != 1:
            print utils.c("输入的数据'%s'格式错误" % tmp_line, 'r')
            return 0
        list_info.append(tmp_line)
    list_info = exprs(list_info)
    for zoneid in list_info:
        print openqq.del_zone_info(zoneid)
