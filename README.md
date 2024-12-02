# Kugel

Explore Kubernetes resources using SQLite.

![](./docs/under-construction.jpg)

## Rationale

Filtering and summarizing Kubernetes resources at the command line is a pain.
Kugel can help.

Let's say you want to know who is hogging a GPU pool, based on instance type and a team-specific pod label.
With Kugel that could be

```shell
kugel -a "select owner, sum(gpu_req), sum(cpu_req)
          from pods join nodes on pods.node_name = node.name
          where instance_type = 'a40' and pods.status in ('Running', 'Terminating')
          group by 1 order by 2 desc limit 10"
```

Without Kugel

```shell
nodes=$(kubectl get nodes -o json | jq -r '.items[] 
        | select(.metadata.labels["beta.kubernetes.io/instance-type"] == "a40") | .metadata.name')
kubectl get pods -o json --all-namespaces | jq -r --argjson nodes "$nodes" '
  .items[]
  | select(.spec.nodeName as $node | $nodes | index($node))
  | select(.status.phase == "Running")
  | . as $pod | $pod.spec.containers[]
  | select(.resources.requests["nvidia.com/gpu"] != null)
  | {owner: $pod.metadata.labels["com.mycompany/job-owner"], 
     gpu: .resources.requests["nvidia.com/gpu"], 
     cpu: .resources.requests["cpu"]}
  | group_by(.owner) 
  | map({owner: .[0].owner, 
         gpu: map(.gpu | tonumber) | add, 
         cpu: map(.cpu | if test("m$") then (sub("m$"; "") | tonumber / 1000) else tonumber end) | add})
  | .[] | "\(.owner) \(.gpu) \(.cpu)"' | sort -nrk2 | head -10
```

## Installing

If you don't mind Kugel cluttering your Python with its [dependencies](./requirements.txt), run

```
pip install ...
```

If you do, here's a shell alias to use the Docker image

```shell
kugel() {
    docker run \
        -v $HOME/.kube:/root/.kube 
        -v $HOME/.kugel:/root/.kugel \
        insert-docker-image-here \
        "$@"
}
```

## How it works (important)

Kugel is simple-minded.  It knows `SELECT ... FROM pods` really means 
`kubectl get pods -o json`, and it maps fields from the response to columns
in SQLite.  If you `JOIN` to other resource tables like `nodes` it calls `kubectl get`
for those too.  If you need more columns or tables than are built in, there's a config file for that.

Because Kugel always fetches all resources from a namespace (or everything, if 
`-a/--all-namespaces` is used), it tries
to ease Kubernetes API Server load by **caching responses for 
two minutes**.  This is why it often prints "Data delayed up to ..." messages.

Depending on your cluster size, the cache can be a help or a hindrance.
You can suppress the "delayed" messages with the `-r` / `--reckless` option, or
always update data using the `-u` / `--update` option.  These behaviors, and
the cache expiration time, can be set in the config file as well.

In any case, please be mindful of stale data and server load.

## Learn more

(coming soon)

* Command-line syntax
* Settings
* [Built-in tables and functions](./docs/builtins.md)
* [Adding columns and tables](./docs/extending.md)
* Adding views


