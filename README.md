# Use Case: Student Eating Behavior in correlation to the Student's GPA
## Hochschule Bremen, Submission for course Cloud & Big Data

Eat Smart - with Big Data!

Do donuts for breakfast make you smarter?
After which dish do I write the best grades?

Find out now with the results of this big data analysis from hundreds of data sets!

Implemented by (Tabea Schuster, Leonard Tuturea, Lars Obist, Philipp Moritzer)

![](https://github.com/TabSchu/cloud-eat-smart/blob/develop/documentation/images/EatSmartBigData.png?raw=true)
## Idea

A web application to find out the correlation between food and GPA. Data for the application is generated through simulating student surveys, in which students register their GPA, as well as their favorite cuisine and lunch/breakfast options. The data from the surveys will then get aggregated and the application calculates the average GPA from all submissions of a specific cuisine or meal. These calculated results will then be displayed on the webpage for visitors to find out what kind of food might help them achieve good grades.

## Architecture

![Architecture](https://github.com/TabSchu/cloud-eat-smart/blob/develop/documentation/images/architecture.png?raw=true)

The application runs on a Kubernetes Cluster, in this case minikube/microk8s. Therefore it would be possible to scale the application and react to higher traffic / load by starting more pods of some of the services.

The loadbalancer is provided by Kubernetes with ingress and distributes the traffic to possible multiple instances of the web application.

Multiple Webservers with a running node.js/express application serve the web application to the user.

The Web Application either gets its data from a memcached server instance or directly from the database depending on whether the data is cached. There are multiple memcached instances running in the cluster and there is one database (MySQL)-Server running.
Kafka is the Big Data Messaging service where the website sends its data to. The kafka cluster docks on the spark application also running on this cluster. The Spark Application which in our case runs as a Docker-Container computes the data and sends it directly back to the MySQL Database Server or the checkpoints will be stored in a Data Lake. The Datalake is implemented in a HDFS.

## Workflow

![Workflow](https://github.com/TabSchu/cloud-eat-smart/blob/develop/documentation/images/workflow.png?raw=true)

As shown in the image above, the user clicks on the link to generate multiple new sets of data. A GET-Request on the /survey route generates one set of data. In a real world scenario this could be the insert of a new survey result, after interviewing a group of students. Multiple institutes could insert / generate data at the same time in different instances of the web application. [index.js & *.html]
The datasets will be send to Kafka. [spark-app.py:] Spark computes the data in streamed batches of data.
The result will be written into the MySQL database and the checkpoints will be written to HDFS. 
The webapp visualises the result in a top ten list and charts. First, the app tries to fetch the data for the food and the “food-wiki-page” from the cache. If it is not already cached, the data will be queried from the MySQL DB.


## Generating data

A Data Entry consists of a students GPA, his/her favorite cuisine, his/her favorite lunch, his/her favorite breakfast and a timestamp of the creation of the entry. For each new entry, a random GPA from 1.0 to 4.0 will be generated, the cuisine and meal preferences will then be randomly taken from pre-defined options. In order to produce more interesting results, weighted probabilities are used. The implementation of the data generation can be found under /web-app/data.

```
{ 
	gpa: '2.50', 
	fav_cuisine: 'italian',
	fav_lunch: 'pizza',
	fav_breakfast: 'donuts',
	timestamp: 1604325221 
}
```

## Aggregating the Data

The data will be grouped by favorite cuisine, breakfast and lunch. This is not a chained group by, but three separated queries. These result in three database tables and three different top ten lists / charts for the frontend.
For each group Avg GPA and count will be calculated. The data is not separated on timeframes, as the “study” examines the best overall food for a great GPA, not the changes over time.   
If there exists already an entry for the specific food or cuisine in the database, the new data form the batch and the existing data will be aggregated. 


## Displaying the data in proper HTML


### Chart.js

For a better user experience, the generated data was visualised in charts. The JavaScript library chart.js was used to create bar charts as well as pie charts.
The bar chart enables the user to make a comparison between different meals and their effect on the students GPAs.
The pie chart is used to show which meal is most popular among the students.

### EJS

To get a better separation of concerns, the visualisation of the frontend was separated from the logic in index.js. Therefore we created the index.html and detail.html. The templating language EJS was used to inject the data with javascript into the HTML template.
As a result, the only concerns of the index.js refer to the app logic for example the reaction to the endpoint requests, sending data to kafka querying data from the cache or database.


## Prerequisites

### Running minikube / microk8s

For Windows (Windows Package Manager required): 
```bash
winget install minikube 
```
or (Chocolatey Package Manager required) :	
```bash
choco install minikube 
```

For Mac (Brew Package Manager required): 
```bash
brew install minikube 
```
Linux - Binary Download : 
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

Start Minikube:
```bash
minikube start
```
## Prerequisites
### Enable ingress in minikube

```
minikube addons enable ingress
```
### A running Strimzi.io Kafka operator

```bash
helm repo add strimzi http://strimzi.io/charts/
helm install my-kafka-operator strimzi/strimzi-kafka-operator
kubectl apply -f https://farberg.de/talks/big-data/code/helm-kafka-operator/kafka-cluster-def.yaml
```

### A running Hadoop cluster with YARN (for checkpointing)

```bash
helm delete my-hadoop-cluster # delete existing cluster beforehand, elsewise there might be errors
helm repo add stable https://charts.helm.sh/stable
helm install --namespace=default --set hdfs.dataNode.replicas=1 --set yarn.nodeManager.replicas=1 --set hdfs.webhdfs.enabled=true my-hadoop-cluster stable/hadoop
```



## Deploy

To develop using [Skaffold](https://skaffold.dev/), use `skaffold dev`. 

Microk8s: `skaffold dev --default-repo=localhost:32000`




Get the Minikube IP and open \<ip\>:\<port\> in Browser:

```
minikube ip
```

## Useful commands

### Check database tables via console

```
kubectl exec -ti deployment/mysql-deployment -- mysql -u root --password=mysecretpw -e "SHOW databases; USE popular; SHOW tables; SELECT * FROM food; SELECT * FROM smart_cuisine; SELECT * FROM smart_breakfast; SELECT * FROM smart_lunch;"
```

### Watch the cluster state
```
watch kubectl get all
```

# References

Boilerplate code taken from use-case: https://farberg.de/talks/big-data/code/use-case/ (Date: 13th March 2021), by Prof. Dennis Pfisterer

Therotical knowledge gained by Prof. Dennis Pfisterer's course at Hochschule Bremen - Cloud & Big Data (Wintersemester 20/21)

# License
## Creative Commons CC0 1.0 Universal

CREATIVE COMMONS CORPORATION IS NOT A LAW FIRM AND DOES NOT PROVIDE LEGAL SERVICES. DISTRIBUTION OF THIS DOCUMENT DOES NOT CREATE AN ATTORNEY-CLIENT RELATIONSHIP. CREATIVE COMMONS PROVIDES THIS INFORMATION ON AN "AS-IS" BASIS. CREATIVE COMMONS MAKES NO WARRANTIES REGARDING THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS PROVIDED HEREUNDER, AND DISCLAIMS LIABILITY FOR DAMAGES RESULTING FROM THE USE OF THIS DOCUMENT OR THE INFORMATION OR WORKS PROVIDED HEREUNDER.

### Statement of Purpose

The laws of most jurisdictions throughout the world automatically confer exclusive Copyright and Related Rights (defined below) upon the creator and subsequent owner(s) (each and all, an "owner") of an original work of authorship and/or a database (each, a "Work").

Certain owners wish to permanently relinquish those rights to a Work for the purpose of contributing to a commons of creative, cultural and scientific works ("Commons") that the public can reliably and without fear of later claims of infringement build upon, modify, incorporate in other works, reuse and redistribute as freely as possible in any form whatsoever and for any purposes, including without limitation commercial purposes. These owners may contribute to the Commons to promote the ideal of a free culture and the further production of creative, cultural and scientific works, or to gain reputation or greater distribution for their Work in part through the use and efforts of others.

For these and/or other purposes and motivations, and without any expectation of additional consideration or compensation, the person associating CC0 with a Work (the "Affirmer"), to the extent that he or she is an owner of Copyright and Related Rights in the Work, voluntarily elects to apply CC0 to the Work and publicly distribute the Work under its terms, with knowledge of his or her Copyright and Related Rights in the Work and the meaning and intended legal effect of CC0 on those rights.

1. __Copyright and Related Rights.__ A Work made available under CC0 may be protected by copyright and related or neighboring rights ("Copyright and Related Rights"). Copyright and Related Rights include, but are not limited to, the following:

    i. the right to reproduce, adapt, distribute, perform, display, communicate, and translate a Work;

    ii. moral rights retained by the original author(s) and/or performer(s);

    iii. publicity and privacy rights pertaining to a person's image or likeness depicted in a Work;

    iv. rights protecting against unfair competition in regards to a Work, subject to the limitations in paragraph 4(a), below;

    v. rights protecting the extraction, dissemination, use and reuse of data in a Work;

    vi. database rights (such as those arising under Directive 96/9/EC of the European Parliament and of the Council of 11 March 1996 on the legal protection of databases, and under any national implementation thereof, including any amended or successor version of such directive); and

    vii. other similar, equivalent or corresponding rights throughout the world based on applicable law or treaty, and any national implementations thereof.

2. __Waiver.__ To the greatest extent permitted by, but not in contravention of, applicable law, Affirmer hereby overtly, fully, permanently, irrevocably and unconditionally waives, abandons, and surrenders all of Affirmer's Copyright and Related Rights and associated claims and causes of action, whether now known or unknown (including existing as well as future claims and causes of action), in the Work (i) in all territories worldwide, (ii) for the maximum duration provided by applicable law or treaty (including future time extensions), (iii) in any current or future medium and for any number of copies, and (iv) for any purpose whatsoever, including without limitation commercial, advertising or promotional purposes (the "Waiver"). Affirmer makes the Waiver for the benefit of each member of the public at large and to the detriment of Affirmer's heirs and successors, fully intending that such Waiver shall not be subject to revocation, rescission, cancellation, termination, or any other legal or equitable action to disrupt the quiet enjoyment of the Work by the public as contemplated by Affirmer's express Statement of Purpose.

3. __Public License Fallback.__ Should any part of the Waiver for any reason be judged legally invalid or ineffective under applicable law, then the Waiver shall be preserved to the maximum extent permitted taking into account Affirmer's express Statement of Purpose. In addition, to the extent the Waiver is so judged Affirmer hereby grants to each affected person a royalty-free, non transferable, non sublicensable, non exclusive, irrevocable and unconditional license to exercise Affirmer's Copyright and Related Rights in the Work (i) in all territories worldwide, (ii) for the maximum duration provided by applicable law or treaty (including future time extensions), (iii) in any current or future medium and for any number of copies, and (iv) for any purpose whatsoever, including without limitation commercial, advertising or promotional purposes (the "License"). The License shall be deemed effective as of the date CC0 was applied by Affirmer to the Work. Should any part of the License for any reason be judged legally invalid or ineffective under applicable law, such partial invalidity or ineffectiveness shall not invalidate the remainder of the License, and in such case Affirmer hereby affirms that he or she will not (i) exercise any of his or her remaining Copyright and Related Rights in the Work or (ii) assert any associated claims and causes of action with respect to the Work, in either case contrary to Affirmer's express Statement of Purpose.

4. __Limitations and Disclaimers.__

    a. No trademark or patent rights held by Affirmer are waived, abandoned, surrendered, licensed or otherwise affected by this document.

    b. Affirmer offers the Work as-is and makes no representations or warranties of any kind concerning the Work, express, implied, statutory or otherwise, including without limitation warranties of title, merchantability, fitness for a particular purpose, non infringement, or the absence of latent or other defects, accuracy, or the present or absence of errors, whether or not discoverable, all to the greatest extent permissible under applicable law.

    c. Affirmer disclaims responsibility for clearing rights of other persons that may apply to the Work or any use thereof, including without limitation any person's Copyright and Related Rights in the Work. Further, Affirmer disclaims responsibility for obtaining any necessary consents, permissions or other rights required for any use of the Work.

    d. Affirmer understands and acknowledges that Creative Commons is not a party to this document and has no duty or obligation with respect to this CC0 or use of the Work.

    