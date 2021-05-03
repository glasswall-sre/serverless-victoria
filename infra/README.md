# Serverless Victoria<br>

## Componenets Deployed<br>

Serverless victoria deployment requires deploying the following broad components.
All deployment uses the Serverless Framework to deploy the infrastructure (https://www.serverless.com/)
Production version of serverless Victoria is setup in the following AWS cloud

**AWS Account - 433250546572**<br>
**AWS Region - eu-west-2 (London)**<br>

### Victoria Security<br><br>

* Victoria Security receives all authentication requests directed towards Victoria (Mostly from Slack users) 
* It checks for user email in the request and matches is the email id is a valid member of **Azure Active Directory Group (SRE Team)**
* All service requests are received by Victoria Security. It checks and verifies Authorization information before passing on requests to Serverless Victoria
* All commnunication between Victoria Security and Serverless Victoria is through http calls.

#### Deployment<br><br>

**AWS**<br>
    * API Gateway
        * API Gateway Id - 6p6epl6baj
        * API Endpoint - authenticate(POST)
        * Stage - dev        
    * Lambda    
        * victoria-authentication-dev-authorisor
    * AWS Secrtes Manager
        * Slack Bot Id
        * Azure credentials etc.

**Azure**<br>
    * Azure Active Directory Group (SRE Team)
    * Users in SRE Team group


### Serverless Victoria<br>

* Serverless victoria is meant to execute victoria cli. It packs victoria cli (A PyPI package) within.
* It exposes an http endpoint to receive Authorized requests, which are mostly consumed by Victoria Security
* This endpoint invokes victoria cli with the parameters passed in and responds back with the result. 

#### Deployment<br><br>

**AWS**<br>
    * API Gateway
        * API Gateway Id - dpwaexj78b
        * API Endpoint - / (POST)
        * Stage - prod        
    * Lambda    
        * serverless-victoria-service-prod-hello
    * AWS Secrtes Manager        
        * Azure credentials etc.

**Azure**<br>
    * Azure Keyvault is used for encryption and decryption    

### Dead Letter Service Bus<br>

* All requests to victoria are processed with azure cli. Encryption, Storage etc are finally invoked on azure.
* Victoria uses **Azure Service Bus** service to put failed requests and messages for consumers to retry.
* Serverless projects like Dead Letter Watcher and Dead Letter Resolver listen the service bus through sunscription and try to resolve failed requests.

#### Deployment<br><br>

**Azure**<br>
    * Service Bus Infrastructure

### Dead Letter Watcher<br>

* Dead Letter Watcher is a serverless project deployed in AWS.
* It exposes an http endpoint that is configured in Azure service bus as a subscriber.
* It subscribes to AWS Service Bus queue and waits for messages
* Once a message is received in the dead letter queue, it picks and deletes the message from the bus and sends the message as a notification to the Slack user or workspace configured with Victoria 

#### Deployment<br><br>

**AWS** <br>
    * API Gateway
        * API Gateway Id - o8l52l2o29
        * API Endpoint - listener (POST)
        * Stage - dev        
    * Lambda    
        * deadletter-watcher-dev-hello 
    * AWS Secrtes Manager
        * Slack Bot Id
        * Azure credentials etc.

### Dead Letter Resolver<br>

* Dead Letter Resolver is a serverless project deployed in AWS.
* Slack users can try to respond to failed messages. Notifications sent by the dead letter watcher to slack users are actionable items. The user may chose to retrigger an event or send and email or delete a request victoria failed. These actions are actioned upon by the dead letter resolver projec
* It exposes an http endpoint that is used by the Slack bot to invoke failed Victoria requests
* Once a message is received by it does nothing for now. It is in not implemented state. It returns a Thanks message to the Slack caller and finishes.

#### Deployment<br><br>

**AWS** <br>
    * API Gateway
        * API Gateway Id - qi5codjfi7
        * API Endpoint - resolve (POST)
        * Stage - dev        
    * Lambda    
        * deadletter-resolver-dev-dl-resolver        