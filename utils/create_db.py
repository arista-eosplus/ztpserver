#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import sys

con = lite.connect('/usr/share/ztpserver/db/resources.db')

with con:

    for table in ['mgmt_subnet', 'tor_hostnames', 'ip_vlan100', 'ip_loopback']:
        print "Working on: ",table
        cur = con.cursor()
        sql = "DROP TABLE IF EXISTS `%s`" % table
        cur.execute(sql)
        sql = "CREATE TABLE `%s`(key TEXT, node_id TEXT)" % table
        cur.execute(sql)
        if table == "mgmt_subnet":
            base = "172.16.130."
            subnet = "/24"
        elif table == "tor_hostnames":
            base = "veos-dc1-pod1-tor"
            subnet = ""
        elif table == "ip_vlan100":
            base = "10.100.1."
            subnet = "/24"
        elif table == "ip_loopback":
            base = "1.1.1."
            subnet = "/32"

        for x in range(1,500):
            sql = "INSERT INTO %s VALUES('%s%s%s',NULL)" % (table, base, str(x), subnet)
            cur.execute(sql)

        sql = "SELECT * FROM `%s`" % table
        print sql
        cur.execute(sql)
        rows = cur.fetchall()
        for row in rows:
            print row
