# mutating-webhook
A mutating webhook for custom scheduling of KFP argo and workflow-runner pods

## INSTALLATION
1. SSH into the data node
2. Pull the repo and cd into it
3. Create CSR and secret using the script in the dir `./create-signed-cert.sh --service wfr-kfp-mutating-webhook --namespace default --secret admission-tls`
4. Get the caBundle for the webhook `CA_BUNDLE=$(kubectl config view --raw -ojson | jq -r '.clusters[0].cluster."certificate-authority-data"'); sed -i "s/cabundle_placeholder/$CA_BUNDLE/" k8s_objects/mutate-config.yaml`
5. Create the webhook and other objects `kubectl create -f k8s_objects/`

## USAGE
The webhook's deployment contains an environment variable called `NODE_POOL` which holds the target node selector for the mutated pods.
The webhook will mutate the nodeSelector field of pods/jobs that have either of the following labels: `job-type: workflow-runner`, `workflows.argoproj.io/workflow`
The mutation will:
1. Remove the spec.affinity block
2. Add the node selector label that is defined in `NODE_POOL`

## TEST
Create various remote workflows in MLRun, use `with_preemtion` and `with_node_selection` to demo different use-cases. Check the node selectors that the workflow-runner and KFP/argo pods got. 
You may use the following command to list pods and their nodeSelector key: `kubectl get pods --sort-by=.metadata.creationTimestamp -o custom-columns='NAME:.metadata.name,SELECTOR:.spec.nodeSelector'`
Note that job pods will remain untouched.

## LOGS
Logs can be viewed by running `kubectl logs deployments/wfr-kfp-mutating-webhook`
Example:
```
$ kubectl logs deployments/wfr-kfp-mutating-webhook
[2024-11-25 13:06:24,904] INFO: ########## workflow-runner/kfp-argo mutating webhook v1 ##########
[2024-11-25 13:06:24,905] INFO: Started server process [1]
[2024-11-25 13:06:24,905] INFO: Waiting for application startup.
[2024-11-25 13:06:24,906] INFO: Application startup complete.
[2024-11-25 13:06:24,906] INFO: Uvicorn running on https://0.0.0.0:5000 (Press CTRL+C to quit)
[2024-11-25 13:08:07,898] INFO: Applying nodeSelector for Pod/bb-wfr-.
[2024-11-25 13:08:07,898] INFO: Got 'app.iguazio.com/lifecycle: non-preemptible' as nodeSelector label, patching...
INFO:     172.31.0.102:36144 - "POST /mutate?timeout=20s HTTP/1.1" 200 OK
[2024-11-25 13:10:00,091] INFO: Applying nodeSelector for Pod/my-workflow-.
[2024-11-25 13:10:00,091] INFO: Got 'app.iguazio.com/lifecycle: non-preemptible' as nodeSelector label, patching...
INFO:     172.31.1.131:54586 - "POST /mutate?timeout=20s HTTP/1.1" 200 OK
[2024-11-25 13:10:03,714] INFO: Applying nodeSelector for Pod/kfpipeline-296qd-744990100.
[2024-11-25 13:10:03,714] INFO: Got 'app.iguazio.com/lifecycle: non-preemptible' as nodeSelector label, patching...
INFO:     172.31.1.131:54586 - "POST /mutate?timeout=20s HTTP/1.1" 200 OK
INFO:     172.31.1.131:54586 - "POST /mutate?timeout=20s HTTP/1.1" 200 OK
[2024-11-25 13:20:00,101] INFO: Applying nodeSelector for Pod/my-workflow-.
[2024-11-25 13:20:00,102] INFO: Got 'app.iguazio.com/lifecycle: non-preemptible' as nodeSelector label, patching...
INFO:     172.31.1.131:33096 - "POST /mutate?timeout=20s HTTP/1.1" 200 OK
[2024-11-25 13:20:03,706] INFO: Applying nodeSelector for Pod/kfpipeline-25nmp-3714210200.
[2024-11-25 13:20:03,706] INFO: Got 'app.iguazio.com/lifecycle: non-preemptible' as nodeSelector label, patching...
INFO:     172.31.1.131:33096 - "POST /mutate?timeout=20s HTTP/1.1" 200 OK
INFO:     172.31.1.131:33096 - "POST /mutate?timeout=20s HTTP/1.1" 200 OK
```
   


