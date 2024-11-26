
from .dbmodel import Table
from .helpers import Resources, ItemHelper, PodHelper, JobHelper


class NodesTable(Table):

    NAME = "nodes"
    RESOURCE_KIND = "nodes"
    SCHEMA = """
        name TEXT,
        provider TEXT,
        node_family TEXT,
        amp_type TEXT,
        cpu_alloc REAL,
        gpu_alloc REAL,
        mem_alloc INTEGER,
        cpu_cap REAL,
        gpu_cap REAL,
        mem_cap INTEGER,
        ns_taints TEXT
    """

    def make_rows(self, kube_data: list[dict]) -> list[tuple]:
        return [(
            node.name,
            node.obj.get("spec", {}).get("providerID"),
            node.label("pathai.com/node-family") or node.label("mle.pathai.com/node-family"),
            node.label("amp.pathai.com/node-type"),
            *Resources.extract(node["status"]["allocatable"]).as_tuple(),
            *Resources.extract(node["status"]["capacity"]).as_tuple(),
            ",".join(taint["key"] for taint in node.obj.get("spec", {}).get("taints", [])
                     if taint["effect"] == "NoSchedule")
        ) for node in map(ItemHelper, kube_data)]


class NodeTaintsTable(Table):

    NAME = "node_taints"
    RESOURCE_KIND = "nodes"
    SCHEMA = """
        name TEXT,
        key TEXT,
        effect TEXT
    """

    def make_rows(self, kube_data: list[dict]) -> list[tuple]:
        nodes = map(ItemHelper, kube_data)
        return [(
            node.name,
            taint["key"],
            taint["effect"],
        ) for node in nodes for taint in node.obj.get("spec", {}).get("taints", [])]


class PodsTable(Table):

    NAME = "pods"
    RESOURCE_KIND = "pods"
    SCHEMA = """
        name TEXT,
        is_daemon INTEGER,
        namespace TEXT,
        node_name TEXT,
        command TEXT,
        status TEXT,
        cpu_req REAL,
        gpu_req REAL,
        mem_req INTEGER,
        cpu_lim REAL,
        gpu_lim REAL,
        mem_lim INTEGER
    """

    def make_rows(self, kube_data: list[dict]) -> list[tuple]:
        return [(
            pod.name,
            1 if pod.is_daemon else 0,
            pod.namespace,
            pod["spec"].get("nodeName"),
            pod.command,
            pod["kubectl_status"],
            *pod.resources("requests").as_tuple(),
            *pod.resources("limits").as_tuple(),
        ) for pod in map(PodHelper, kube_data)]


class JobsTable(Table):

    NAME = "jobs"
    RESOURCE_KIND = "jobs"
    SCHEMA = """
        name TEXT,
        namespace TEXT,
        status TEXT
    """

    def make_rows(self, kube_data: list[dict]) -> list[tuple]:
        return [(
            job.name,
            job.namespace,
            job.status,
        ) for job in map(JobHelper, kube_data)]


class WorkflowsTable(Table):

    NAME = "workflows"
    RESOURCE_KIND = "workflows"
    SCHEMA = """
        name TEXT,
        namespace TEXT,
        url TEXT,
        phase TEXT
    """

    def make_rows(self, kube_data: list[dict]) -> list[tuple]:
        return [(
            w.name,
            w.namespace,
            f'http://app.mle.pathai.com/jabba/workflows/view/{w.label("jabba.pathai.com/workflow-id")}',
            w.label("workflows.argoproj.io/phase"),
        ) for w in map(ItemHelper, kube_data)]
