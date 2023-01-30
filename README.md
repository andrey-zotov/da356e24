Prerequisites:
docker
helm
k8s

.env

`kubectl create secret generic regcred --from-file=.dockerconfigjson=/checkthispath/.docker/config.json --type=kubernetes.io/dockerconfigjson`

localstack:
`helm repo add localstack-repo https://helm.localstack.cloud`
`helm upgrade --install localstack localstack-repo/localstack --set "ingress.enabled=true,ingress.hosts[0].host=localstack,ingress.hosts[0].paths[0].path=/,ingress.hosts[0].paths[0].pathType=Prefix"`
Host: `kubectl get nodes --namespace "default" -o jsonpath="{.items[0].status.addresses[0].address}"`
Port: `kubectl get --namespace "default" -o jsonpath="{.spec.ports[0].nodePort}" services localstack`
Save into .env
`kubectl get pods`
`kubectl port-forward localstack-5bdddb7c8-gf9pv 31566:31566`

`helm upgrade --install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx --namespace ingress-nginx --create-namespace`
`kubectl --namespace ingress-nginx get services -o wide -w ingress-nginx-controller`

`helm upgrade --install metrics-server metrics-server/metrics-server`
`kubectl -n default patch deployment metrics-server --type=json -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]]'`
