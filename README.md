# Use Case: Popular NASA Shuttle Missions

```json
{ 
	mission: 'sts-10', 
	timestamp: 1604325221 
}
```

## Prerequisites

A running Strimzi.io Kafka operator

```bash
helm repo add strimzi http://strimzi.io/charts/
helm install my-kafka-operator strimzi/strimzi-kafka-operator
kubectl apply -f https://farberg.de/talks/big-data/code/helm-kafka-operator/kafka-cluster-def.yaml
```

A running Hadoop cluster with YARN (for checkpointing)

```bash
helm delete my-hadoop-cluster # delete cluster, elsewise errors after computer restart
# helm repo add stable https://kubernetes-charts.storage.googleapis.com/ -->nolonger available, instead try:
helm repo add stable https://charts.helm.sh/stable
helm install --namespace=default --set hdfs.dataNode.replicas=1 --set yarn.nodeManager.replicas=1 --set hdfs.webhdfs.enabled=true my-hadoop-cluster stable/hadoop
```


## Deploy

To develop using [Skaffold](https://skaffold.dev/), use `skaffold dev`. 




### check database pod via console
# todo: change id to id from your mysql-pod and add more sql queries if yo need
 kubectl exec -ti pod/mysql-deployment-678c94d959-zcrmf  -- mysql -u root --password=mysecretpw -e "SHOW databases; USE popular; SHOW tables; SELECT * FROM student; SELECT * FROM smart_cuisine; " 