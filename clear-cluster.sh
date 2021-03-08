microk8s kubectl delete --all deployments
microk8s kubectl delete --all statefulset.apps
microk8s kubectl delete --all services
micrko8s kubectl delete --all apps

helm uninstall my-kafka-operator
microk8s kubectl delete -f kafka-cluster-def.yaml
helm delete my-hadoop-cluster

helm install my-kafka-operator strimzi/strimzi-kafka-operator
microk8s kubectl apply -f kafka-cluster-def.yaml

helm install --namespace=default --set hdfs.dataNode.replicas=1 --set yarn.nodeManager.replicas=1 --set hdfs.webhdfs.enabled=true my-hadoop-cluster stable/hadoop
