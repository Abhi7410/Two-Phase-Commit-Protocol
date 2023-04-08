from flask import Flask, request, jsonify
import requests
import json
import os
import threading
import time
import pymysql.cursors
import pandas as pd
import uuid
import colorama
from colorama import Fore, Back, Style
import logging 
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# uuid = universally unique identifier (unique id for each transation)
app = Flask(__name__)

class Coordinator:
    def __init__(self,log_file,db_host,db_user,db_password,db_name,nodes):
        self.num_commits = 0
        self.num_ready = 0
        self.num_aborts = 0
        self.nodes = nodes
        self.num_nodes = len(nodes)+1
        self.node_ids = []
        self.log_file = open(log_file, "a+") # open log file   
        self.db_host = db_host
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.connection = pymysql.connect(host=self.db_host,
                                user=self.db_user,
                                password=self.db_password,
                                db=self.db_name,
                                autocommit=False)
        self.cursor = self.connection.cursor()
        

    def phase1Execute(self,transactionID,query):
        print(Fore.YELLOW + Style.BRIGHT + "Phase 1: Coordinator is executing the query" + Fore.RESET)
        self.log_file.write("Prepare===" + transactionID + "===" + query + "\n")
        self.log_file.flush() 
        print("Write prepared to log file")

        isCoordReady = True
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
        except:
            isCoordReady = False
            print("Coordinator is not prepared to execute the query")
            self.log_file.write("Abort===" + transactionID + "===" + query + "\n")
            self.log_file.flush()
            print("Write abort to log file")
            self.num_aborts += 1
            self.connection.rollback()
            return False
        
        threads = []
        if isCoordReady:
            print("Coordinator is prepared to execute the query")
            self.log_file.write("Commit===" + transactionID + "===" + query + "\n")
            self.log_file.flush()
            print("Write commit to log file")
            self.num_ready += 1
            self.connection.commit()
            for clients in self.nodes:
                t = threading.Thread(target=self.threadExecute1, args=(clients,transactionID,query))
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            return True
        
    def threadExecute1(self,client,transactionID,query):
        currentURL = client + "/phase1Execute"
        data = {"transactionID": transactionID, "query": query}
        print(data)
        try:
            response = requests.post(currentURL, json = data)
            status_ = response.json()['status']
            print(status_)
            if (status_ == ("READY "+query)):
                print(Fore.GREEN + "Node number " + client + " is ready to execute the query" + Fore.RESET)
                self.num_ready += 1
        except:
            print(Fore.RED + "Node number " + client + " is not ready to execute the query" + Fore.RESET)
            self.num_aborts += 1

    def threadDecide(self,client,transactionID,query,decision):
        currentURL = client + "/phase2Execute"
        data = {"transactionID": transactionID, "query": query, "decision": decision}
        try:
            response = requests.post(currentURL, json = data)
        except:
            print(Fore.RED + "Could not connect to node number " + client + Fore.RESET)
            self.num_aborts += 1
            return

        
    def phase2Execute(self,transactionID,query):
        print(Fore.YELLOW + "Phase 2: Coordinator is executing the query" + Fore.RESET)
        while True:
            phase2 = input(Fore.WHITE + "Continue with phase 2? (y/n): "+ Fore.RESET)
            if phase2 == "y":
                break
            
        if self.num_nodes == (self.num_ready):
            print(Fore.GREEN + "All nodes are ready to execute the query" + Fore.RESET)
            self.log_file.write("Commit===" + transactionID + "===" + query + "\n")
            self.log_file.flush()
            print("Write commit to log file")
            self.num_commits += 1
            self.connection.commit()
            for clients in self.nodes:
                t = threading.Thread(target=self.threadDecide, args=(clients,transactionID,query,"COMMIT"))
                t.start()
            return True
        else:
            print(Fore.RED + "Not all nodes are ready to execute the query" + Fore.RESET)
            self.log_file.write("Abort===" + transactionID + "===" + query + "\n")
            self.log_file.flush()
            print("Write abort to log file")
            self.num_aborts += 1
            self.connection.rollback()
            for clients in self.nodes:
                t = threading.Thread(target=self.threadDecide, args=(clients,transactionID,query,"ABORT"))
                t.start()

    @app.route('/getDecision', methods=['POST'])
    def getDecision(self):
        data = request.get_json()
        transactionID = data['transactionID']
        query = data['query']
        # read log file to get status of transaction
        status_list = []
        with open(self.log_file, "r") as f:
            for line in f:
                line = line.split("===")
                if line[1] == transactionID:
                    status_list.append(line[0])

        if "Commit" in status_list:
            return jsonify({"decision": "COMMIT"})
        elif "Abort" in status_list:
            return jsonify({"decision": "ABORT"})
        else:
            return jsonify({"decision": "UNKNOWN"})
        
        
    def ExecuteAll(self):
        time.sleep(2)
        while True:
            query = input(Fore.WHITE + "Enter query: " + Fore.RESET)
            transactionID = str(uuid.uuid4())
            if self.phase1Execute(transactionID,query):
                self.phase2Execute(transactionID,query)

            print(Fore.CYAN + "Number of commits: " + 
                  Fore.RESET + str(self.num_commits))
            print(Fore.CYAN + "Number of aborts: " +
                  Fore.RESET + str(self.num_aborts))

    


if __name__ == '__main__':
    nodes = ["http://localhost:5124","http://localhost:5125"]
    nodeIds = ["5124","5125"]
    coord = Coordinator("log.txt","localhost","ds","Distributed@123","coordinator",nodes)
    th = threading.Thread(target=coord.ExecuteAll, args=())
    print(Fore.YELLOW + "Coordinator is running" + Fore.RESET)
    print(Fore.YELLOW + "Coordinator is listening on port 5000" + Fore.RESET)
    for i in range(len(nodeIds)):
        # Print out a message for each node
        print(Fore.GREEN +
              f"Node {i+1} is listening on port {nodeIds[i]}" + Fore.RESET)


    th.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False,use_reloader=False)


    
