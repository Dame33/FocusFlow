import time
import logging
import pygetwindow as gw
import datetime
import mysql.connector
from mysql.connector import Error
from threading import Thread, Event

class DB_Connector:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect( #connect to sql db
                host="", database="", user="", password=""
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
        except Error as e:
            print(f"Cannot connect to the database: {e}")

    def execute_query(self, sql, params=None):
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            self.connection.commit()  
        except Error as e:
            print(f"Error executing query: {e}")

    def connection_close(self):
        try:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
        except Error as e:
            print(f"Error closing connection: {e}")

class CustomHandler(logging.StreamHandler):
    def __init__(self, db):
        super().__init__()
        self.db = db

    #def emit(self, record):
        #if record:  
            #sql = "INSERT INTO tablename (APP_NAME, START_TIME, END_TIME, TOTAL_TIME) VALUES (%s, %s, %s, %s)"
            #params = (record.filename, record.funcName, record.lineno, record.msg)
            #self.db.execute_query(sql, params)

def track_app(db, logger, stop_event):
    currentApp = ""
    startTime = time.time()
    startDate = datetime.datetime.now()
    app_times = {} #Use this to store the total time

    try:
        while not stop_event.is_set():
            activeWindow = gw.getActiveWindow()
            activeTitle = activeWindow.title if activeWindow else None

            if activeTitle != currentApp:
                if currentApp:
                    timeSpent = time.time() - startTime
                    endDate = datetime.datetime.now()

                    if currentApp in app_times: #check if current app exists in app_times, if yes we add up the times 
                        app_times[currentApp] += timeSpent
                    else: #if not adds the current app into app_times
                        app_times[currentApp] = timeSpent

                    sql = ("INSERT INTO tablename (APP_NAME, START_TIME, END_TIME, TOTAL_TIME) "
                           "VALUES (%s, %s, %s, %s)")
                    params = (currentApp, startDate, endDate, app_times[currentApp])
                    db.execute_query(sql, params)
                    logger.info(f"App: {currentApp}, Time spent this session: {timeSpent:.2f} seconds, Total time: {app_times[currentApp]:.2f} seconds, \nStart Date: {startDate}, End Date: {endDate}") #logs info into terminal

                if activeTitle:
                    currentApp = activeTitle
                    startTime = time.time()
                    startDate = datetime.datetime.now()
                    logger.info(f"App Switched to: {currentApp}")

                else:
                    logger.info("No Active Window")

            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("Tracking Stopped")


def main(logger, db):
    stop_event = Event()
    try:
        tracker = Thread(target=track_app, args=(db, logger, stop_event))
        tracker.start()
        input("Press Enter to stop the tracking...")
        stop_event.set()  #stops program
        tracker.join()
    except Exception as e:
        logger.critical(f"critical mode: {e}")
    finally:
        db.connection_close()

if __name__ == "__main__":
    db = DB_Connector()
    logger = logging.getLogger("tester")
    logger.setLevel(logging.DEBUG)
    customhandler = CustomHandler(db)
    logger.addHandler(customhandler)
    main(logger, db)