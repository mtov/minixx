def build_stages(tasks):
    remaining = {task["name"]: set(task.get("deps", [])) for task in tasks}
    done = set()
    stages = []

    while remaining:
        ready = [
            task["name"]
            for task in tasks
            if task["name"] in remaining and not (remaining[task["name"]] - done)
        ]

        if not ready:
            raise ValueError("dependency cycle")

        stages.append(ready)
        for name in ready:
            done.add(name)
            remaining.pop(name)

    return stages
