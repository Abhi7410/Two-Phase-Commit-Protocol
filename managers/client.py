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

app = Flask(__name__)



class Manager:
    def __init__(self,log_file,db_host,db_user,db_password,db_name,node_id,coordinator_url):
        Manager.log_file = open(log_file, "a+") # open log file
        Manager.db_host = db_host
        Manager.db_user = db_user
        Manager.db_password = db_password
        Manager.db_name = db_name
        Manager.node_id = node_id
        Manager.coordinator_url = coordinator_url
        Manager.connection = pymysql.connect(host=Manager.db_host,
                                user=Manager.db_user,
                                password=Manager.db_password,
                                db=Manager.db_name,
                                autocommit=False)
        Manager.cursor = Manager.connection.cursor()
        self = Manager
        

    @app.route('/phase1Execute', methods=['POST'])
    def phase1Execute():
        data = request.get_json()
        transactionID = data['transactionID']
        query = data['query']
        print("Query Received: " + query)
        print("Phase 1: Manager is executing the query")
        isManagerReady = True
        try:
            Manager.cursor.execute(query)
            results = Manager.cursor.fetchall()
            print(results)
        except:
            isManagerReady = False
            print("Manager is not prepared to execute the query")
        
        askOperator = input(Fore.WHITE + "Is the operator ready to commit? (y/n): " + Fore.RESET).lower()

        if askOperator == "y":
            isOperatorReady = True
        else:
            isOperatorReady = False

        if isManagerReady and isOperatorReady:
            print("Manager is ready to execute the query")
            Manager.log_file.write("Ready===" + transactionID + "===" + query + "\n")
            Manager.log_file.flush()
            return jsonify({"status": "READY "+query})
        else:
            print("Manager is not ready to execute the query")
            Manager.log_file.write("No===" + transactionID + "===" + query + "\n")
            Manager.log_file.flush()
            return jsonify({"status": "ABORT "+query})
        
    @app.route('/phase2Execute', methods=['POST'])
    def phase2Execute():
        data = request.get_json()
        transactionID = data['transactionID']
        query = data['query']
        coordinator_decision = data['decision']
        print("Phase 2: Manager is executing the query")
        print("Coordinator decision: " + coordinator_decision)
        if coordinator_decision == "COMMIT":
            print("Committing the transaction")
            Manager.log_file.write("Commit===" + transactionID + "===" + query + "\n")
            Manager.log_file.flush()
            Manager.connection.commit()
            print("Transaction committed by " + Manager.node_id + " manager")
            return jsonify({"status": "COMMIT "+query})
        else:
            print("Aborting the transaction")
            Manager.log_file.write("Abort===" + transactionID + "===" + query + "\n")
            Manager.log_file.flush()
            Manager.connection.rollback()
            print("Transaction aborted by " + Manager.node_id + " manager")
            return jsonify({"status": "ABORT "+query})

    def failureRecovery(self):
        print(Back.RED +"Failure recovery started" +Back.RESET)
        # open the log file and read the last line
        with open(self.log_file.name, "r") as f:
            lines = f.readlines()
            print(lines)
            print(len(lines))
            if len(lines) == 0:
                print("No transaction to recover")
                return
            last_line  = lines[-1][:-1]
            last_line = last_line.split("===")
            last_transactionID = last_line[1]
            last_query = last_line[2]
            last_decision = last_line[0]
            print(Fore.YELLOW + "Last transactionID: " + Fore.RESET+ last_transactionID)
            print(Fore.YELLOW + "Last query: " + Fore.RESET + last_query)
            print(Fore.YELLOW + "Last decision: " + Fore.RESET + last_decision)
            if last_decision == "Ready":
                print("Asking the operator to commit the transaction")
                currURL = self.coordinator_url + "/getDecision"
                data = {"transactionID": last_transactionID, "query": last_query}
                try:
                    response = requests.post(currURL,json=data)
                    decisionByCoordinator = response.json()['decision']
                    print("Decision by coordinator: " + decisionByCoordinator)
                    if decisionByCoordinator == "COMMIT":
                        print("Committing the transaction")
                        self.log_file.write("Commit===" + last_transactionID + "===" + last_query + "\n")
                        self.log_file.flush()
                        self.connection.commit()
                        print("Transaction committed by " + self.node_id + " manager")
                    else:
                        print("Aborting the transaction")
                        self.log_file.write("Abort===" + last_transactionID + "===" + last_query + "\n")
                        self.log_file.flush()
                        self.connection.rollback()
                        print("Transaction aborted by " + self.node_id + " manager")
                except:
                    print("Coordinator is not available")
            elif last_decision == "Commit":
                print("Committing the transaction")
                self.log_file.write("Commit===" + last_transactionID + "===" + last_query + "\n")
                self.log_file.flush()
                self.connection.commit()
                print("Transaction committed by " + self.node_id + " manager")
                print(Back.GREEN + "Failure recovery completed" + Back.RESET)
                return 
            elif last_decision == "Abort":
                print("Aborting the transaction")
                self.log_file.write("Abort===" + last_transactionID + "===" + last_query + "\n")
                self.log_file.flush()
                self.connection.rollback()
                print("Transaction aborted by " + self.node_id + " manager")
            else:
                print("No transaction to recover")
        

    


if __name__ == '__main__':
    manag = Manager("log.txt","localhost","ds","Distributed@123","clientA","1","http://localhost:5000")
    manag.failureRecovery()
    app.run(host='0.0.0.0',port=5124,debug=True)

    # manag2 = Manager("log.txt","localhost","ds","Distributed@123","clientB","2","http://localhost:5000")
    # manag2.failureRecovery()
    # app.run(host='0.0.0.0',port=5125,debug=True)







