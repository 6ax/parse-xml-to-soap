#!/usr/bin/python3

import re
import os
import requests
import pymysql.cursors  
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz

dbhost = ""
sitedbuser = ""
sitedbuserpassword = ""
sitedbname = ""

projectsdbuser = ""
projectsdbuserpassword  = sitedbuserpassword
projectsdbname = ""

startexporttime = "2019-09-26 21:54:14"

logfn = "export.log"

elmasoapurl = "http://localhost:8000/Modules/EleWise.ELMA.Workflow.Processes.Web/WFPWebService.asmx"

class DBHelper:

    def __init__(self, host, user, password, db):
        self.host = host
        self.user = user
        self.password = password
        self.db = db

    def __connect__(self):
        self.con = pymysql.connect(host=self.host, user=self.user, password=self.password, db=self.db)
        self.cur = self.con.cursor()

    def __disconnect__(self):
        self.con.close()

    def __commit__(self):
        self.con.commit()

    def fetch(self, sql):
        self.__connect__()
        self.cur.execute(sql)
        result = self.cur.fetchall()
        self.__disconnect__()
        return result

    def execute(self, sql):
        self.__connect__()
        self.cur.execute(sql)
        self.con.commit()
        self.__disconnect__()

class ELMA:

    def writelogfile(self):
        self.__setcurrent_time__()
        with open(logfn, 'a') as logfile:
            logfile.write("{} {} {}\n".format(self.fn, self.instanceid, self.currenttime))

    def __setcurrent_time__(self):
        self.tz = pytz.timezone('Europe/Moscow')
        self.currenttime = datetime.now(self.tz).strftime("%d/%m/%Y %H:%M:%S")
 
    def __create_SOAP_request___(self):
        tree = ET.parse(self.fn)
        source = tree.getroot()
        soap = """
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:wfp="http://www.elma-bpm.ru/WFPWebService/">
            <soapenv:Header/>
            <soapenv:Body>
                <wfp:Run>
                    <wfp:userName>admin</wfp:userName>
                    <wfp:password>admin</wfp:password>
                    <wfp:token>WFP_ApplicationFromExternalsystem</wfp:token>
                    <wfp:instanceName>ApplicationFromExternalsystem</wfp:instanceName>
                    <wfp:data>
                        <wfp:Items>
        """
        for item in source.findall(".//field"):
            #print (item.get('id'), item.text)
            soap += """
            <wfp:WebDataItem>
                <wfp:Name>{}</wfp:Name>'
                <wfp:Value>{}</wfp:Value>
            </wfp:WebDataItem>
            """.format(item.get('id'), item.text)

        soap += """
                        </wfp:Items>
                    </wfp:data>
                </wfp:Run>
            </soapenv:Body>
        </soapenv:Envelope>
        """
        soap = soap.encode('utf-8')
        #print (soap)
        return soap

    def send_SOAP(self,fn):
        self.fn = fn
        self.url = elmasoapurl
        self.headers = {'content-type': 'text/xml;charset=UTF-8', 'Accept-Encoding': 'gzip,deflate', 'SOAPAction': 'http://www.elma-bpm.ru/WFPWebService/Run'}
        try:
            response = requests.post(self.url,data=self.__create_SOAP_request___(),headers=self.headers, timeout=20)
            #print (response.content)
            regex = r"<RunResult>(\d*)</RunResult>"
            self.instanceid = re.search(regex, str(response.content)).group(1)
            if not re.finditer(regex, str(response.content), re.MULTILINE):
                print ("No instanceid received, exiting: \n")
                os._exit(0)
        except requests.exceptions.Timeout as err:
             print ("Timeout Error:",err)
        except requests.exceptions.RequestException as err:
            print ("OOps: Something Else",err)
        except requests.exceptions.HTTPError as err:
            print ("Http Error:",err)
        except requests.exceptions.ConnectionError as err:
            print ("Error Connecting:",err)

def get_filepaths_from_sitedb(): 
    conn = DBHelper(dbhost, sitedbuser, sitedbuserpassword, sitedbname)
    cursor = conn.fetch("""
                        SELECT path
                        FROM dvlp_project_application
                        WHERE updated_at >= '{}';
                        """.format(startexporttime))
    retset = set()
    for row in cursor:
        for i in row:
            i = "/var/www/vebventures/vebventures/frontend/web{}".format(i)
            #print (i)
            retset.add(i)
    return retset

def get_filepaths_from_projects():
    conn = DBHelper(dbhost, projectsdbuser, projectsdbuserpassword, projectsdbname)
    cursor = conn.fetch("""
                        SELECT `path` 
                        FROM `projects`;
                        """)
    retset = set()
    for row in cursor:
        for i in row:
            #print (i)
            retset.add(i)
    return retset

def insert_filepaths_to_projects(path):
    conn = DBHelper(dbhost, projectsdbuser, projectsdbuserpassword, projectsdbname)
    conn.execute("""
                INSERT INTO `export_projects`.`projects`
                (`path`)
                VALUES
                ('{}')
                """.format(path))

if __name__ == "__main__":
    fromsite = get_filepaths_from_sitedb()
    #print (fromelma)
    fromprojects = get_filepaths_from_projects()
    #print (fromprojects)
    newrojects = fromsite - fromprojects
    #print (newrojects)
    elma = ELMA()
    for row in newrojects:  
        elma.send_SOAP(row)
        insert_filepaths_to_projects(row)
        elma.writelogfile()
