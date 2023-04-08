# Two-Phase-Commit-Protocol

This is a simple implementation of the two-phase commit protocol. It is a distributed transaction management protocol that ensures that a transaction can be committed or rolled back across multiple distributed resources. The protocol is used in distributed systems to ensure that all the resources involved in a transaction are updated only if all the resources are ready to commit the transaction. If any of the resources is not ready to commit the transaction, then the transaction is rolled back.

## How to run
1. Clone the repository
2. Run the following command in the terminal
``` 
cd Two-Phase-Commit-Protocol
cd coordinator
python3 server.py
```
3. Open a new terminal and run the following command
```
cd Two-Phase-Commit-Protocol
cd managers/site1
python3 client.py
```
4. Follow this also for other sites

5. On the coordinator terminal, you will see the following output
```
    Coordinator is running
    Coordinator is listening on port 5000
    Node 1 is listening on port 5124
    Node 2 is listening on port 5125
    * Serving Flask app 'server'
    * Debug mode: off
    Enter query:
```
6. Enter sql query for the below table and press enter. The query will be executed on all the sites and if all the sites are ready to commit the transaction, Coordinator will be asked to commit the transaction. If any of the sites is not ready to commit the transaction, Coordinator will be asked to abort the transaction.
``` 
    CREATE TABLE student_table(  
        id int NOT NULL AUTO_INCREMENT,  
        name varchar(45) NOT NULL,  
        branch varchar(35) NOT NULL,  
        age int NOT NULL,  
        placement_company varchar(45),
        PRIMARY KEY (id)  
    );  

    INSERT INTO student_table (name, branch, age, placement_company) VALUES ('John', 'CSE', 21, 'Google');
```
7. On the client's terminal, the client will be asked to execute the query on receiving the query from the coordinator. The client will execute the query and send the status of the query to
the coordinator. The coordinator will then ask the other clients to execute the query. If all the clients execute the query successfully, the coordinator will commit the transaction. If any of the clients is not able to execute the query, the coordinator will abort the transaction.


