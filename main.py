from pathlib import Path
import datetime
import ifcopenshell
from ifcopenshell.api import run
from ifcopenshell.util.element import get_decomposition
from ifcopenshell.util.placement import get_storey_elevation

modelname = "Skylab-STRU"

try:
    dir_path = Path(__file__).parent
    model_url = Path.joinpath(dir_path, 'model', modelname).with_suffix('.ifc')
    model = ifcopenshell.open(model_url)
except OSError:
    try:
        import bpy
        model_url = Path.joinpath(Path(bpy.context.space_data.text.filepath).parent, 'model', modelname).with_suffix('.ifc')
        model = ifcopenshell.open(model_url)
        print(model)
    except OSError:
        print(f"ERROR: please check your model folder : {model_url} does not exist")

# Your script goes here:
# Define a convenience function to add a task chained to a predecessor
def add_task(model, name, predecessor, work_schedule=None, parent=None):
    if work_schedule:
        # Add a construction task
        task = run(
            "sequence.add_task",
            model,
            work_schedule=work_schedule,
            name=name,
            predefined_type="CONSTRUCTION",
        )
    if parent:
        # Add a sub task
        task = run(
            "sequence.add_task",
            model,
            parent_task=parent,
            name=name,
            predefined_type="CONSTRUCTION",
        )
    # Give it a time
    task_time = run("sequence.add_task_time", model, task=task)
    # Arbitrarily set the task's scheduled time duration to be 1 week
    run(
        "sequence.edit_task_time",
        model,
        task_time=task_time,
        attributes={
            "ScheduleStart": datetime.date(2023, 1, 2),
            "ScheduleDuration": "P1W",
        },
    )
    # If a predecessor exists, create a finish to start relationship
    if predecessor:
        run(
            "sequence.assign_sequence",
            model,
            relating_process=predecessor,
            related_process=task,
        )

    return task


# Create a new construction schedule
schedule = run(
    "sequence.add_work_schedule", model, name="Construction of Group 23's Building"
)

# Starting task:
task1 = add_task(model, "Site establishment", None, work_schedule=schedule)
#Assigning different time to a certain task
time = ifcopenshell.api.run("sequence.add_task_time", model, task=task1)
ifcopenshell.api.run("sequence.edit_task_time", model,
  task_time=time, attributes={"ScheduleStart": "2023-01-02", "ScheduleDuration": "P5D"})
start_task = task1
# Next task:
task2 = add_task(model, "Excavations", task1, work_schedule=schedule)
time = ifcopenshell.api.run("sequence.add_task_time", model, task=task2)
ifcopenshell.api.run("sequence.edit_task_time", model,
  task_time=time, attributes={"ScheduleStart": "2023-01-09", "ScheduleDuration": "P15D"})
task3 = add_task(model, "Foundation", task2, work_schedule=schedule)
time = ifcopenshell.api.run("sequence.add_task_time", model, task=task3)
ifcopenshell.api.run("sequence.edit_task_time", model,
  task_time=time, attributes={"ScheduleStart": "2023-01-30", "ScheduleDuration": "P5D"})

# Get all our storeys sorted by elevation ascending.
storeys = sorted(
    model.by_type("IfcBuildingStorey"), key=lambda s: get_storey_elevation(s)
)

# For each storey ...
for storey in storeys:
    task4 = add_task(model, f"Construct {storey.Name}", task3, work_schedule=schedule)
    time = ifcopenshell.api.run("sequence.add_task_time", model, task=task4)
    ifcopenshell.api.run("sequence.edit_task_time", model,
        task_time=time, attributes={"ScheduleStart": "2023-02-06", "ScheduleDuration": "P34D"})
    if storey.Name != "EK_Kælder":
        subtask1 = add_task(
            model, f"\tPrecast Elements Installation {storey.Name}", task4, parent=task4
        )
        time = ifcopenshell.api.run("sequence.add_task_time", model, task=subtask1)
        ifcopenshell.api.run("sequence.edit_task_time", model,
           task_time=time, attributes={"ScheduleStart": "2023-02-06", "ScheduleDuration": "P5D"})
        subtask2 = add_task(model, f"\tServices {storey.Name}", subtask1, parent=task4)
        time = ifcopenshell.api.run("sequence.add_task_time", model, task=subtask2)
        ifcopenshell.api.run("sequence.edit_task_time", model,
           task_time=time, attributes={"ScheduleStart": "2023-02-13", "ScheduleDuration": "P2W"})
        subtask3 = add_task(
        model, f"\tInterior and Exterior {storey.Name}", subtask2, parent=task4
        )
        time = ifcopenshell.api.run("sequence.add_task_time", model, task=subtask3)
        ifcopenshell.api.run("sequence.edit_task_time", model,
           task_time=time, attributes={"ScheduleStart": "2023-03-03", "ScheduleDuration": "P15D"})
        
        if storey.Name == "E4_4. Sal":
            subtask4 = add_task(
                model, f"\tRoofing {storey.Name}", subtask3, parent=task4
            )
            time = ifcopenshell.api.run("sequence.add_task_time", model, task=subtask4)
            ifcopenshell.api.run("sequence.edit_task_time", model,
               task_time=time, attributes={"ScheduleStart": "2023-03-24", "ScheduleDuration": "P1W"})
    for product in get_decomposition(storey):
        run(
            "sequence.assign_product",
            model,
            relating_product=product,
            related_object=task4,
        )

# Final task:
task5 = add_task(model, "Handover", subtask4, work_schedule=schedule)
time = ifcopenshell.api.run("sequence.add_task_time", model, task=task5)
ifcopenshell.api.run("sequence.edit_task_time", model,
    task_time=time, attributes={"ScheduleStart": "2023-04-03", "ScheduleDuration": "P1W"})

# Ask the computer to calculate all the dates for us from the start task.
run("sequence.cascade_schedule", model, task=start_task)

model.write(r"C:\Users\R\Desktop\UNI\41934 BIM\model\Skylab-STRU_remodeled.ifc")
# END
