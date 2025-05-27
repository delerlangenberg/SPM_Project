import os

# Define the target files and the expected function stubs
base_dir = "D:/Documents/Project/SPM/interface/layout"
targets = {
    "hardware_controls.py": "def launch_hardware_controls():\n    print('Hardware Controls panel not yet implemented')\n",
    "system_diagnostics.py": "def launch_diagnostics():\n    print('Diagnostics panel not yet implemented')\n"
}

for filename, stub in targets.items():
    path = os.path.join(base_dir, filename)

    if not os.path.exists(path):
        # Create file with stub
        with open(path, "w", encoding="utf-8") as f:
            f.write(stub)
        print(f"✅ Created: {filename} with stub.")
    else:
        # Check if function already exists
        with open(path, "r+", encoding="utf-8") as f:
            content = f.read()
            func_name = stub.split('(')[0].split()[1]
            if func_name not in content:
                f.write("\n\n" + stub)
                print(f"✍️  Added missing function: {func_name} to {filename}")
            else:
                print(f"✅ Function {func_name} already present in {filename}")

