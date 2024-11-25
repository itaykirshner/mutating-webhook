from fastapi import FastAPI, Body
from os import environ
from models import Patch
import logging
import base64
import json

app = FastAPI()

webhook = logging.getLogger(__name__)
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.removeHandler(uvicorn_logger.handlers[0])  # Turn off uvicorn duplicate log
webhook.setLevel(logging.INFO)
logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s")

webhook.info("########## workflow-runner/kfp-argo mutating webhook v1 ##########")
pool = environ.get("NODE_POOL")
if not pool:
    webhook.error("The required environment variable 'NODE_POOL' isn't set. Exiting...")
    exit(1)


def patch(node_pool: str, existing_selector: bool, has_affinity: bool) -> base64:
    label, value = node_pool.replace(" ", "").split(":")
    webhook.info(f"Got '{node_pool}' as nodeSelector label, patching...")

    if existing_selector:
        webhook.info(f"Found already existing node selector, replacing it.")
        patch_operations = [Patch(op="replace", path="/spec/nodeSelector", value={f"{label}": f"{value}"}).dict()]
    else:
        patch_operations = [Patch(op="add", path="/spec/nodeSelector", value={f"{label}": f"{value}"}).dict()]

    # remove affinity (to override with_preemtion)
    if has_affinity:
        patch_operations.append({'op': 'remove', 'path': '/spec/affinity'})

    return base64.b64encode(json.dumps(patch_operations).encode())


def admission_review(uid: str, message: str, existing_selector: bool, has_affinity: bool) -> dict:
    return {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": uid,
            "allowed": True,
            "patchType": "JSONPatch",
            "status": {"message": message},
            "patch": patch(pool, existing_selector, has_affinity).decode(),
        },
    }


@app.post("/mutate")
def mutate_request(request: dict = Body(...)):
    uid = request["request"]["uid"]
    selector = request["request"]["object"]["spec"]
    object_in = request["request"]["object"]

    mutate_pod = False
    has_affinity = False
    try:
        if ("workflows.argoproj.io/workflow" in object_in["metadata"]["labels"]) or (object_in["metadata"]["labels"]["job-type"] == "workflow-runner"):
            mutate_pod = True
        if "affinity" in object_in["spec"]:
            has_affinity = True
    except KeyError:
        pass

    if mutate_pod:
        # notify that the pod is to be mutated. Handle case where "generateName" exists in metadata
        try:
            webhook.info(f'Applying nodeSelector for {object_in["kind"]}/{object_in["metadata"]["name"]}.')
        except KeyError:
            webhook.info(f'Applying nodeSelector for {object_in["kind"]}/{object_in["metadata"]["generateName"]}.')
        return admission_review(
            uid,
            "Successfully added nodeSelector.",
            True if "nodeSelector" in selector else False,
            has_affinity,
        )
