# Generated by Selenium IDE
import os
import pytest
import time
import json
import logging
import sqlite3
import configparser
from os import listdir
from os.path import isfile, join
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from sqlalchemy import create_engine, Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_

Base = declarative_base()

class MigrationStatus(Base):
  __tablename__ = 'migration_status'

  progress = Column(String, primary_key=True)
  status = Column(String)
  messages = Column(String)
  startdate = Column(String)
  enddate = Column(String)

class WebProDataFiller():
  # Initial preparation and get file parameter
  def setupMethod(self):
    # get parent directory
    self.workDir = os.getcwd()

    # read config.ini
    path = self.workDir + "\Config"
    self.config = configparser.ConfigParser()
    self.config.read(os.path.join(path, 'config.ini'))

    # read JSON File
    jsonfile = path + "\data"
    with open(os.path.join(jsonfile, 'tagSet.json'), 'r') as config_file:
      self.tagData = json.load(config_file)
    with open(os.path.join(jsonfile, 'categoryMenu.json'), 'r') as config_file:
      self.menuData = json.load(config_file)

    # read Folder and list All File
    filePath = self.workDir + "\Content\Files"
    self.files = [f for f in listdir(filePath) if isfile(join(filePath, f))]
    csvPath = self.workDir + "\Content\Csv"
    self.csvs = [f for f in listdir(csvPath) if isfile(join(csvPath, f))]

    # Database
    self.configDB()
    self.progress = self.config['WEBPRO']['progress'].split(',')
    logging.info('--> Start '+ self.progress[0])
  
  # Call browser & login
  def tearUpMethod(self):
    self.initiateData()

    service = Service(self.workDir + '\Bin\chromedriver.exe')
    chrome_options = webdriver.ChromeOptions() 
    chrome_options.add_argument("--ignore-certificate-error")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    self.driver = webdriver.Chrome(service = service, options = chrome_options)
    self.vars = {}

    webpro_username = self.config['WEBPRO']['username']
    webpro_password = self.config['WEBPRO']['password']
    webpro_url = self.config['WEBPRO']['webProUrl']
    
    self.driver.get(webpro_url)
    self.driver.find_element(By.ID, "maintainer").send_keys(webpro_username)
    self.driver.find_element(By.ID, "pw").send_keys(webpro_password)
    self.driver.find_element(By.NAME, "bv:act_OK").click()
  
  # Close Browser
  def tearDownMethod(self):
    logging.info("--> Finish "+self.progress[0])
    self.driver.quit()
    self.updateDB(self.progress[0], "Finished", "")  
  
  # ------------------
  # 1. Create Tag Set
  # ------------------
  def webProCreateTagSet(self):
    # check if there is error, then halt process, else forward
    migration = self.session.query(MigrationStatus).filter(MigrationStatus.status == "Error").first()
    if not migration or migration.progress == self.progress[1]:
      try:
        logging.info("--> 1. " +self.progress[1]+ ", Begin!")
        self.updateDB(self.progress[1], "In Progress", "")

        self.driver.find_element(By.CSS_SELECTOR, "#menu_item_account > span").click()
        self.driver.find_element(By.LINK_TEXT, "Tag sets").click()

        for tag in self.tagData['data-tags']:
          if tag["tagset"] == "audience":
            # self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(1) > td span").click()
            self.driver.find_element(By.NAME, "bv:act_create_vocabulary").click()
            self.driver.find_element(By.ID, "voc_id-value").send_keys(tag["tagset"])
            self.driver.find_element(By.ID, "voc_friendly_name-value").send_keys(tag["tagset"].capitalize())
            self.driver.find_element(By.ID, "voc_multi-value").click()
            self.driver.find_element(By.CSS_SELECTOR, ".formSection:nth-child(5) > .checkbox").click() # decision_tree
            self.driver.find_element(By.NAME, "bv:act_create_vocabulary").click()
            self.driver.find_element(By.NAME, "bv:act_assign").click()
            self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(4) .input-checkbox").click()
            self.driver.find_element(By.CSS_SELECTOR, ".footer > .btn").click()
          elif tag["tagset"] == "taxonomy-1":
            self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(2) > td span").click()
          elif tag["tagset"] == "taxonomy-2":
            self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(3) > td span").click()
          elif tag["tagset"] == "taxonomy-3":
            self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(4) > td span").click()
            self.driver.find_element(By.NAME, "bv:act_assign").click()
            self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(5) .input-checkbox").click() # quick-link
            self.driver.find_element(By.CSS_SELECTOR, ".footer > .btn").click()
          
          for data in tag["data"]:
            self.createTagSet(data["tag"], data["name"])
          
          self.driver.find_element(By.NAME, "bv:act_back").click()
        
        self.updateDB(self.progress[1], "Finished", "")
      except Exception as e:
        logging.error("--> 1. " +self.progress[1]+ ", Error: "+str(e))
        self.updateDB(self.progress[1], "Error", str(e))
    else:
      logging.info("--> 1. " +self.progress[1]+ ", Skipped, there is error on previous process!")

  def createTagSet(self, tag, name):
    self.driver.find_element(By.NAME, "bv:act_add").click()
    self.driver.find_element(By.ID, "term_id-value").send_keys(tag)
    self.driver.find_element(By.ID, "term_friendly_name-value").send_keys(name)
    self.driver.find_element(By.ID, "term_admin_name-value").send_keys(name)
    self.driver.find_element(By.NAME, "bv:act_create_term").click()
    
  # ------------------
  # 2. Upload file
  # ------------------
  def webProUploadFileLibrary(self):
    # check if there is error, then halt process, else forward
    migration = self.session.query(MigrationStatus).filter(MigrationStatus.status == "Error").first()
    if not migration or migration.progress == self.progress[2]:
      try:
        logging.info("--> 2. " +self.progress[2]+ ", Begin!")
        self.updateDB(self.progress[2], "In Progress", "")

        self.driver.find_element(By.CSS_SELECTOR, "#menu_item_entries").click()
        self.driver.find_element(By.CSS_SELECTOR, ".unselected:nth-child(10) span").click()
        
        bulkFilesDir = self.workDir + "\Content\Files"
        bulkFiles = self.files
        for name in bulkFiles:
          self.bulkFilesUpload(name, bulkFilesDir)

        self.updateDB(self.progress[2], "Finished", "")
      except Exception as e:
        logging.error("--> 2. " +self.progress[2]+ ", Error: "+str(e))
        self.updateDB(self.progress[2], "Error", str(e))
    else:
      logging.info("--> 2. " +self.progress[2]+ ", Skipped, there is error on previous process!")

  def bulkFilesUpload(self, fileName, fileDir):
    self.driver.find_element(By.NAME, "bv:act_UploadFile").click()
    self.driver.find_element(By.ID, "resourcePath").send_keys(fileName)
    self.driver.find_element(By.ID, "resourceName").send_keys(fileName)
    self.driver.find_element(By.XPATH, "//input[@id=\'imageName\']").send_keys(fileDir + "/" + fileName)
    self.driver.find_element(By.NAME, "bv:act_action_Public").click()

  # ------------------
  # 3. Create Category & it Subcategory
  # ------------------
  def webProCreateCategory(self):
    # check if there is error, then halt process, else forward
    migration = self.session.query(MigrationStatus).filter(MigrationStatus.status == "Error").first()
    if not migration or migration.progress == self.progress[3]:
      try:
        logging.info("--> 3. " +self.progress[3]+ ", Begin!")
        self.updateDB(self.progress[3], "In Progress", "")

        self.driver.find_element(By.ID, "menu_item_account").click()

        # Create Categories
        categories = self.menuData["data-menu"]["categories"]
        for category in categories:
          self.createCategory(category["id"], category["name"])

        # Create Subcategories
        subcategories = self.menuData["data-menu"]["subcategories"]
        self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(1) > td:nth-child(2) span").click()
        self.driver.find_element(By.LINK_TEXT, "Subcategories").click()
        for subcategory in subcategories:
          self.createSubcategory(subcategory["id"], subcategory["name"])
      
        self.updateDB(self.progress[3], "Finished", "")
      except Exception as e:
        logging.error("--> 3. " +self.progress[3]+ ", Error: "+str(e))
        self.updateDB(self.progress[3], "Error", str(e))
    else:
      logging.info("--> 3. " +self.progress[3]+ ", Skipped, there is error on previous process!")

  def createCategory(self, categoryKey, category):
    wait = self.config['WEBPRO']['timewait']

    self.driver.find_element(By.LINK_TEXT, "Category List").click()
    self.driver.find_element(By.NAME, "bv:act_Create").click()
    self.driver.find_element(By.ID, "moduleID").send_keys(categoryKey)
    self.driver.find_element(By.ID, "moduleName").send_keys(category)
    self.driver.find_element(By.ID, "adminName").send_keys(category)
    select = Select(WebDriverWait(self.driver, wait).until(expected_conditions.element_to_be_clickable((By.ID, "client_source"))))
    select.select_by_visible_text("Template - Knowledge Category")
    self.driver.find_element(By.NAME, "bv:act_OK").click()

  def createSubcategory(self, subcategoryKey, subcategory):     
    self.driver.find_element(By.ID, "topiclist-topicID").send_keys(subcategoryKey)
    self.driver.find_element(By.ID, "topiclist-topicName").send_keys(subcategory)
    self.driver.find_element(By.ID, "topiclist-topicAdminName").send_keys(subcategory)
    self.driver.find_element(By.NAME, "bv:act_OK").click()

  # ------------------
  # 4. Upload Csv Content
  # ------------------
  def webProUploadCsvContent(self):
    # check if there is error, then halt process, else forward
    migration = self.session.query(MigrationStatus).filter(MigrationStatus.status == "Error").first()
    if not migration or migration.progress == self.progress[4]:
      try:
        logging.info("--> 4. " +self.progress[4]+ ", Begin!")
        self.updateDB(self.progress[4], "In Progress", "")

        self.driver.find_element(By.CSS_SELECTOR, "#menu_item_downloads > span").click()

        contentDir = self.workDir + "\Content\Csv"
        contentFiles = self.csvs
        for content in contentFiles:
          if content == "alerts.csv":
            category = "Alerts" # category
            subcategory = "Alert" # subcategory
          elif content == "gloss.csv":
            category = "Glossary" # category
            subcategory = "Glossary Term" # subcategory
          else:
            contentCategory = content.replace(".csv", "").split('-')
            if len(contentCategory) > 2:
              category = contentCategory[1].capitalize() +" "+ contentCategory[2].capitalize()# category
            else:
              category = contentCategory[1].capitalize() # category

            subcategory = contentCategory[0]
            if subcategory == "faq":
              subcategory = subcategory.upper() # subcategory
            else:
              subcategory = subcategory.capitalize() # subcategory
          
          self.bulkCsvContentUpload(category, subcategory, content, contentDir)

        self.updateDB(self.progress[4], "Finished", "")
      except Exception as e:
        logging.error("--> 4. " +self.progress[4]+ ", Error: "+str(e))
        self.updateDB(self.progress[4], "Error", str(e))
    else:
      logging.info("--> 4. " +self.progress[4]+ ", Skipped, there is error on previous process!")

  def bulkCsvContentUpload(self, category, subCategory, fileName, contentDir):
    wait = self.config['WEBPRO']['timewait']

    self.driver.find_element(By.LINK_TEXT, "Content Upload").click()
    select = Select(WebDriverWait(self.driver, wait).until(expected_conditions.element_to_be_clickable((By.ID, "Category-items"))))
    select.select_by_visible_text(category)
    select = Select(WebDriverWait(self.driver, wait).until(expected_conditions.element_to_be_clickable((By.ID, "ULSchemas-items"))))
    select.select_by_visible_text(subCategory)
    self.driver.find_element(By.XPATH, "//input[@id=\'ULFileName\']").send_keys(contentDir + "/" + fileName)
    self.driver.find_element(By.NAME, "bv:act_upload").click()

  # ------------------
  # 5. Publish Content
  # ------------------
  def webProPublishContent(self):
    # check if there is error, then halt process, else forward
    migration = self.session.query(MigrationStatus).filter(MigrationStatus.status == "Error").first()
    if not migration or migration.progress == self.progress[5]:
      try:
        logging.info("--> 5. " +self.progress[5]+ ", Begin!")
        self.updateDB(self.progress[5], "In Progress", "")

        self.driver.find_element(By.CSS_SELECTOR, "#menu_item_entries > span").click()
        self.driver.find_element(By.CSS_SELECTOR, ".unselected:nth-child(7) span").click()

        wait = self.config['WEBPRO']['timewait']
        categories = self.menuData["data-menu"]["categories"]
        for cat in categories:
          category = cat["name"]
          if category != "Glossary":
            select = Select(WebDriverWait(self.driver, wait).until(expected_conditions.element_to_be_clickable((By.ID, "Category-items"))))
            select.select_by_visible_text(category)

            keyChild = ""
            try:
              keyChild = self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(1) > td > a > span")
            except NoSuchElementException:
              keyChild = ""
              logging.info("Skipped: "+category)

            while (keyChild != ""):
              self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(1) > td > a > span").click()
              self.driver.find_element(By.NAME, "bv:act_approve").click()

              keyCheck = ""
              try:
                keyCheck = self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(1) > td > a > span")
              except NoSuchElementException:
                keyCheck == ""

              if (keyCheck == ""):
                break
      
        self.updateDB(self.progress[5], "Finished", "")
      except Exception as e:
        logging.error("--> 5. " +self.progress[5]+ ", Error: "+str(e))
        self.updateDB(self.progress[5], "Error", str(e))
    else:
      logging.info("--> 5. " +self.progress[5]+ ", Skipped, there is error on previous process!")
  
  # ------------------
  # 6. Group Config
  # ------------------
  def webProGroupConfig(self):
    # check if there is error, then halt process, else forward
    migration = self.session.query(MigrationStatus).filter(MigrationStatus.status == "Error").first()
    if not migration or migration.progress == self.progress[6]:
      try:
        logging.info("--> 6. " +self.progress[6]+ ", Begin!")
        self.updateDB(self.progress[6], "In Progress", "")

        self.driver.find_element(By.CSS_SELECTOR, "#menu_item_account > span").click()
        self.driver.find_element(By.LINK_TEXT, "Group Settings").click()
        self.driver.find_element(By.LINK_TEXT, "Included categories").click()
        numbArray = [1,3,4,6,7,8,9,10,13]
        for numb in numbArray:
          self.driver.find_element(By.XPATH, "//div[@id=\'main\']/div/div[2]/div/div[2]/table/tbody/tr["+str(numb)+"]/td/input").click()
        self.driver.find_element(By.NAME, "bv:act_OK").click()

        self.driver.find_element(By.LINK_TEXT, "Account Settings").click()
        self.driver.find_element(By.LINK_TEXT, "Visitor site indexes").click()
        self.driver.find_element(By.LINK_TEXT, "content-en").click()
        self.driver.find_element(By.CSS_SELECTOR, "tr:nth-child(3) a > span").click()

        wait = self.config['WEBPRO']['timewait']
        categories = self.menuData["data-menu"]["all_categories"]
        for category in categories:
          cat = "categories-categories_"+category.replace(" ","-").lower()
          WebDriverWait(self.driver, wait).until(expected_conditions.element_to_be_clickable((By.ID, cat))).click()

        self.driver.find_element(By.ID, "schemas-schemas_5").click()
        self.driver.find_element(By.NAME, "bv:act_Sync").click()
        for category in categories:
          cat = "categories-categories_"+category.replace(" ","-").lower()
          WebDriverWait(self.driver, wait).until(expected_conditions.element_to_be_clickable((By.ID, cat))).click()

        self.driver.find_element(By.ID, "schemas-schemas_5").click()
        self.driver.find_element(By.NAME, "bv:act_OK").click()
      
        self.updateDB(self.progress[6], "Finished", "")
      except Exception as e:
        logging.error("--> 6. " +self.progress[6]+ ", Error: "+str(e))
        self.updateDB(self.progress[6], "Error", str(e))
    else:
      logging.info("--> 6. " +self.progress[6]+ ", Skipped, there is error on previous process!")

  def readRunningTime(self, start, end):
    hours, rem = divmod(end-start, 3600)
    minutes, seconds = divmod(rem, 60)
    if int(hours) != 0:
        return "{:0>2} Hours {:0>2} Minutes".format(int(hours), int(minutes))
    else:
        return "{:0>2} Minutes {:0>2} Seconds".format(int(minutes), round(seconds, 3))

  def configDB(self):
    db_name = 'migrateWebPro.db'
    self.engine = create_engine('sqlite:///'+os.getcwd().replace("\\","/")+'/'+db_name, future=True)
    Base.metadata.create_all(self.engine)
    Session = sessionmaker(bind=self.engine)
    self.session = Session()

  def saveDB(self, progress, status, messages):
    data = MigrationStatus(progress=progress, status=status, messages=messages, startdate=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    self.session.add(data)
    self.session.commit()

  def updateDB(self, progress, status, messages, startdate=""):
    if startdate == "":
      self.session.query(MigrationStatus).filter(MigrationStatus.progress == progress).update({'status':status, 'messages':messages, 'enddate':datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})
    else:
      self.session.query(MigrationStatus).filter(MigrationStatus.progress == progress).update({'status':status, 'messages':messages, 'startdate':datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), 'enddate':""})
    self.session.commit()

  def initiateData(self):
    # check if data in DB still empty
    migration = self.session.query(MigrationStatus).first()
    if not migration : # empty
      for p in self.progress:
        if p == "WebPro migration":
          self.saveDB(p, "In Progress", "")
        else:
          self.saveDB(p, "Pending", "")
    else:
      # check if there is no progress with status pending or error
      migration = self.session.query(MigrationStatus).filter(or_(MigrationStatus.status == "Error", MigrationStatus.status == "Pending")).first()
      if not migration : # no status pending or error in progress
        for p in self.progress:
          if p == "WebPro migration":
            self.updateDB(p, "In Progress", "", "start")
          else:
            self.updateDB(p, "Pending", "", "start")

  def runMigration(self, progress=""):
    if progress == self.progress[1]:
      self.webProCreateTagSet()
    elif progress == self.progress[2]:
      self.webProUploadFileLibrary()
    elif progress == self.progress[3]:
      self.webProCreateCategory()
    elif progress == self.progress[4]:
      self.webProUploadCsvContent()
    elif progress == self.progress[5]:
      self.webProPublishContent()
    elif progress == self.progress[6]:
      self.webProGroupConfig()

if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s') 
  timeStart = time.time()
  dataFiller = WebProDataFiller()
  dataFiller.setupMethod()
  dataFiller.tearUpMethod()

  # # check current progress from DB
  # migration = dataFiller.session.query(MigrationStatus).filter(or_(MigrationStatus.status == "Error", MigrationStatus.status == "Pending")).all()
  # if not migration : # no status pending or error in progress
  #   for run in dataFiller.progress:
  #     dataFiller.runMigration(run.progress)
  # else:
  #   for reRun in migration:
  #     dataFiller.runMigration(reRun.progress)

  # # check current progress from DB
  # migration = dataFiller.session.query(MigrationStatus).filter(or_(MigrationStatus.status == "Error", MigrationStatus.status == "Pending")).all()
  # if not migration :
  #   dataFiller.tearDownMethod()

  timeEnd = time.time()
  runningTime = dataFiller.readRunningTime(timeStart, timeEnd)
  logging.info('--> [PROCESS TIME] ' + runningTime)