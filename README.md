Prerequisites:
docker
helm
k8s

.env

`kubectl create secret generic regcred --from-file=.dockerconfigjson=/checkthispath/.docker/config.json --type=kubernetes.io/dockerconfigjson`

localstack:
`helm repo add localstack-repo https://helm.localstack.cloud`
`helm upgrade --install localstack localstack-repo/localstack`


Do not do this: `helm upgrade --install localstack localstack-repo/localstack --set "ingress.enabled=true,ingress.hosts[0].host=localstack,ingress.hosts[0].paths[0].path=/,ingress.hosts[0].paths[0].pathType=Prefix"`
Host: `kubectl get nodes --namespace "default" -o jsonpath="{.items[0].status.addresses[0].address}"`
Port: `kubectl get --namespace "default" -o jsonpath="{.spec.ports[0].nodePort}" services localstack`
`kubectl get pods`
`kubectl port-forward localstack-5bdddb7c8-gf9pv 31566:31566`

LOCALSTACK_SERVICE_HOST
LOCALSTACK_SERVICE_PORT

`helm upgrade --install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx --namespace ingress-nginx --create-namespace`
`kubectl --namespace ingress-nginx get services -o wide -w ingress-nginx-controller`


`helm upgrade --install metrics-server metrics-server/metrics-server --namespace kube-system`
`kubectl -n kube-system patch deployment metrics-server --type=json -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]]'`

`kubectl exec -it movie-server-57d9dddd59-72kvt -n default -- bash`


Locust helm chart
`helm repo add deliveryhero https://charts.deliveryhero.io/`
```
helm install locust deliveryhero/locust -f ./infra/config/locus-values.yaml

helm install locust deliveryhero/locust --set "ingress.enabled=true,ingress.hosts[0].paths[0].pathType=Prefix,ingress.hosts[0].host=localhost,ingress.hosts[0].paths[0].path=/locust"
     \
    --set ingress.annotations."nginx\.ingress\.kubernetes\.io/rewrite-target"=/\$2

helm install my-release deliveryhero/locust --set ingress.enabled=true \
    --set "ingress.hosts[0].host=localhost,ingress.hosts[0].paths[0].path=/locust(/|\$)(.*),ingress.hosts[0].paths[0].pathType=Prefix" \
    --set ingress.annotations."kubernetes\.io/ingress.class"=nginx \
    --set ingress.annotations."nginx\.ingress\.kubernetes\.io/rewrite-target"=/\$2

    nginx.ingress.kubernetes.io/rewrite-target
    
    nginx.ingress.kubernetes.io/rewrite-target: /$2
    
    --set alertmanager.ingress.annotations."alb\.ingress\.kubernetes\.io/scheme"=internet-facing
```