steps = [
    "PICK OBJECT",
    "SHOW OBJECT",
    "PLACE OBJECT",
    "CLOSE CONTAINER",
    "RAISE HAND"
]

current_step = 0


def validate_activity(activity):

    global current_step

    expected = steps[current_step]

    if activity == expected:

        print("🟢 CORRECT")
        print("Detected:", activity)
        print("Expected:", expected)

        current_step += 1

        if current_step == len(steps):
            print("🎉 EXPERIMENT COMPLETED!")

        return "CORRECT"

    else:

        print("🔴 WRONG SEQUENCE")
        print("Expected:", expected)
        print("Detected:", activity)

        return "WRONG"


# Test
validate_activity("PICK OBJECT")
validate_activity("SHOW OBJECT")
validate_activity("PLACE OBJECT")
validate_activity("CLOSE CONTAINER")
validate_activity("RAISE HAND")
