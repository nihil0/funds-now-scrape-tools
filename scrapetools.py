# -*- coding: utf-8 -*-
"""
FundsNowScrapeTools

@author: nihil0
"""
from selenium import webdriver
from bs4 import BeautifulSoup
import re, json, sqlite3, time, csv

def getPageHTML(browser,buttonID):
    ''' Clicks a button and returns the page HTML of the resulting page'''
    tab = browser.find_element_by_id(buttonID);
    tab.click();
    return browser.page_source;

         
def getTable(fileName):
    ''' Returns a table with various fields as a list if dicts given a fileName
    where filename in set(Overview.html,Returns.html,Risk.html,Cost.html)'''
    with open(fileName,'r') as f:
        pageHTML = f.read();
        soup = BeautifulSoup(pageHTML);
        scriptList = soup.find_all('script')
    
    for sc in scriptList:
        metaData = re.search('(?<=var MetaData =).*(?=;)',sc.text);
        if metaData:
            metaDataDict = json.loads(metaData.group(0));
        
    table = [];
    for k in metaDataDict.keys():
        table.append(metaDataDict[k]);
    
    return table;
        
    
def createDBTable(dbName,tableName, lod):
    ''' Converts a table represented by list of dicts (lod) into a database table in 
    'dbName' called 'tableName' '''
    dbConn = sqlite3.connect(dbName);
    with dbConn:
        c = dbConn.cursor();
        mergeKeys = lambda x,y:\
            {foo:None for foo in set(x.keys()).union(set(y.keys()))}; 
       
        colNames = reduce(mergeKeys,lod).keys()
        
        tableFieldsSQL = '('
        for col in colNames:
            tableFieldsSQL+= (col + ' text,')
            
        tableFieldsSQL = tableFieldsSQL.rstrip(',') + ')';
            
        
        sql = 'create table if not exists '+tableName+tableFieldsSQL;
        c.execute(sql);
    
        tableContents = [[row[k] if k in row else '' for k in colNames]\
        for row in lod];
    
        sql = 'insert into '+tableName+ ' values ('\
        +','.join(['?']*len(tableContents[0]))+')';
    
        c.executemany(sql,tableContents);
        
def sourceDump():
    """
    Captures and dumps HTML from Nordea's FundsNow webpage into files. Data about
    various fund metrics can be found in the following files:
        
        1) Daily NAV - Overview.html
        2) Cumulative Returns - Returns.html
        3) Risk and performance metrics - Risk.html
        4) Costs and Expense Ratios - Cost.html 
        
    """
    buttonIdList = [
    'ctl00_PageContentPlaceHolder_TabsList_FundType_ATabsAll', # Switch from 'focus' to all funds
    'ctl00_PageContentPlaceHolder_TabsList_listreturn', # Funds Return button
    'ctl00_PageContentPlaceHolder_TabsList_listrisk', # ditto for Risk
    'ctl00_PageContentPlaceHolder_TabsList_listfees', # ditto for costs etc. 
    ]

    fileNames = ['Overview.html','Returns.html','Risk.html','Cost.html'];        
       
    # Open browser and navigate to page
    browser = webdriver.Firefox();
    browser.get('http://www.nordea.fi/personal+customers/savings/funds/funds+now/1113312.html');

    for (f,bt) in zip(fileNames,buttonIdList):
        with open(f,'w+') as htmlFile:
            htmlFile.write(getPageHTML(browser,bt));
        time.sleep(2);

    # Close browser
    browser.quit();
    
def createPerfCSV(isinCode):
    """
    Creates a CSV file with fields <Date>,<Price100> of a fund with a specific 
    isinCode. The price of the first entry is 100€. This is NOT the NAV, but it
    doesn't really matter if you're interested in only the returns. In order to 
    get the NAV timeseries, simply divide the entire timeseries by today's Price100
    and multiply by today's NAV. The filename of the CSV file is <isinCode>.csv 
    """
    url = ('http://www.nordea.fi/PageTemplates/ContentWide.aspx?pid=1113312&rw=1'
    +'&url=/fundsnow/InfoReturn.aspx?isin='+isinCode+'&segment=CustomerFIIF&Doma'
    +'ins=NordeaFundsNow,NordeaFinland&lang=en-GB&buyBtn=on&mode=on\&shelves=FII'
    +'F&search=on&catid=Focus&compare=on&xray=on&factsheet=on');

    # Open browser and navigate to page
    browser = webdriver.Firefox();
    browser.get(url);
    sinceLaunchButton = ('ctl00_PageContentPlaceHolder_performaceGraph'+
    '_PeriodTabSinceInception');
    time.sleep(2)
    foo = getPageHTML(browser,sinceLaunchButton)
    
    browser.close()
    
    soup = BeautifulSoup(foo);
    baz = soup.find('map',id="PerfChartMap").find_all('area');
    
    
    fileName = isinCode+'.csv';
    
    with open(fileName,'w+') as f:
        wr = csv.writer(f);
        dateRE = re.compile("(?<=popupon\(').{10}");
        valRE = re.compile("(?<=\[\[')([0-9]|\.)*");
        for m in baz:
            wr.writerow([dateRE.search(m.attrs['onmouseover']).group(0)\
            ,valRE.search(m.attrs['onmouseover']).group(0)]);
    

    
        
    