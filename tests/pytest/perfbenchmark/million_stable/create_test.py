###################################################################
#           Copyright (c) 2016 by TAOS Technologies, Inc.
#                     All rights reserved.
#
#  This file is proprietary and confidential to TAOS Technologies.
#  No part of this file may be reproduced, stored, transmitted,
#  disclosed or used in any form or by any means other than as
#  expressly provided by the written permission from Jianhui Tao
#
###################################################################

# -*- coding: utf-8 -*-
import taos
import sys
from util.dnodes import TDDnode
from util.log import *
from util.cases import *
from util.sql import *
from util.taosdemoCfg import *
from util.pathFinding import *
from util.dnodes import *
import os
import subprocess
import datetime
import threading
import sys
from fabric import Connection

class TDTestCase:
    def init(self, conn, logSql):
        tdLog.debug("start to execute %s" % __file__)
        tdSql.init(conn.cursor(), logSql)
        self.stableLimit = 500

    def stable_creation(self, startNum, insertTemplate, localTaosdemoConfig):
        selfTemplate = insertTemplate

        selfTemplate['name'] = f'stb{startNum}'
        selfTemplate['childtable_count'] = 10
        selfTemplate['childtable_prefix'] = f'stb{startNum}_'
        selfTemplate['batch_create_tbl_num'] = 25
        selfTemplate['insert_rows'] = 0
        selfTemplate['columns'] = [{"type": "INT", "count": 2}, {
            "type": "DOUBLE", "count": 2}, {"type": "BINARY", "len": 32, "count": 1}]
        selfTemplate['tags'] = [{"type": "INT", "count": 2}, {
            "type": "BINARY", "len": 32, "count": 1}]
        localTaosdemoConfig.append_sql_stb("insert_stbs", selfTemplate)

    def createSingleFile(self, stbNum, FileIndex, IP):
        localTaosdemoConfig = TDTaosdemoCfg()
        localTaosdemoConfig.alter_db('drop','no')
        localTaosdemoConfig.alter_db('replica', 2)
        localTaosdemoConfig.alter_insert_cfg('host', IP)
        stbTemplate = dict(localTaosdemoConfig.get_template("insert_stbs"))
        for i in range(stbNum):
            self.stable_creation(int(i + 500 * FileIndex),dict(stbTemplate), localTaosdemoConfig)
        localTaosdemoConfig.generate_insert_cfg(
            'perfbenchmark/million_stable/temp', f'{stbNum}_stb_{FileIndex}')
        runPath = f'perfbenchmark/million_stable/temp/insert_{stbNum}_stb_{FileIndex}.json'
        print(f'{runPath} created')
        return runPath

    def creationThread(self, fileNum, binPath, threadIndex, IP):
        jsonFile = []
        for i in range(fileNum):
            generatedFile = self.createSingleFile(500, (i + threadIndex * fileNum) * self.stableLimit, IP)
            jsonFile.append(generatedFile)
        
        for i in jsonFile:
            os.system(f"{binPath}taosdemo -f {i} > 1 > /dev/null")

    def run(self):
        tdDnodes.stopAll()
        localIP = "127.0.0.1"
        IP1 = '192.168.1.86'
        IP2 = '192.168.1.180'
        # conn1 = Connection("{}@{}".format('ubuntu', IP1),
        #            connect_kwargs={"password": "{}".format('tbase125!')})
        # conn2 = Connection("{}@{}".format('ubuntu', IP2),
        #            connect_kwargs={"password": "{}".format('tbase125!')})

        # conn1.run(f'sudo systemctl start taosd')
        # conn2.run(f'sudo systemctl start taosd')
        # os.system('sudo systemctl start taosd')
        # tdLog.sleep(10)

        connTaos = taos.connect(host=IP1, user="root", password="taosdata", config="/etc/taos")
        c1 = connTaos.cursor()
        c1.execute('drop database if exists db')
        c1.execute('create database db replica 2')
        c1.close()
        connTaos.close()
        # conn1.close()
        # conn2.close()
        binPath = tdFindPath.getTaosdemoPath()

        thread1 = threading.Thread(target = self.creationThread, args = (1,binPath,0,IP1,))
        thread2 = threading.Thread(target = self.creationThread, args = (1,binPath,1,IP1,))
        thread3 = threading.Thread(target = self.creationThread, args = (1,binPath,2,IP1,))
        thread4 = threading.Thread(target = self.creationThread, args = (1,binPath,3,IP1,))
        thread5 = threading.Thread(target = self.creationThread, args = (1,binPath,4,IP1,))
        thread1.start()
        thread2.start()
        thread3.start()
        thread4.start()
        thread5.start()
        thread1.join()
        thread2.join()
        thread3.join()
        thread4.join()
        thread5.join()
        # os.system('sudo systemctl stop taosd')
        
        # self.createSingleFile(self.stableLimit,0)
        # self.createSingleFile(self.stableLimit,1)

        # os.system(f"{binPath}taosdemo -f {jsonPath}insert_{self.stableLimit}_stb_0.json > 1 > /dev/null")
        # os.system(f"{binPath}taosdemo -f {jsonPath}insert_{self.stableLimit}_stb_1.json > 1 > /dev/null")

    def stop(self):
        tdSql.close()
        tdLog.success("%s successfully executed" % __file__)


tdCases.addWindows(__file__, TDTestCase())
tdCases.addLinux(__file__, TDTestCase())