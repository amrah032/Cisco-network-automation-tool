import csv
import os
from netmiko import ConnectHandler

csv_file="devices.csv"
out_dir="outputs"
backup_dir=os.path.join(out_dir,"backups")

os.makedirs(out_dir,exist_ok=True)
os.makedirs(backup_dir,exist_ok=True)

def read_load_devices () :
    devices=[]
    with open (csv_file,newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            devices.append({
                "name": row["name"].strip(),
                "host":row["host"].strip(),
                "username" : row["username"].strip(),
                "password":row["password"].strip(),
                "secret":(row.get("secret") or "").strip(),

            })
    return devices

def connect(device) :
    device_info ={
        "device_type":"cisco_ios",
        "host": device["host"],
        "username": device["username"],
        "password": device["password"],
        "secret":device["secret"],


    }

    connect_var=ConnectHandler(**device_info)
    if device["secret"]:
        connect_var.enable()
    return connect_var


def run_show_command_on_all(devices):
    cmd=input("Enter show command on all device: ").strip()
    for i in devices:
        connect_var=connect(i)
        output=connect_var.send_command(cmd)
        connect_var.disconnect()

        path=os.path.join(out_dir,f"{i['name']}.txt")
        with open (path,"w",encoding="utf-8") as f:
            f.write(output)
        print(f"{i['name']}-> saved as : {path}")



def expand_ports(port_text):
    ports = []
    parts = port_text.split(",")

    for part in parts:
        part = part.strip().lower()

        if "-" in part:
            left, right = part.split("-")
            prefix = left.rsplit("/", 1)[0] 
            start = int(left.rsplit("/", 1)[1])
            end = int(right)

            for i in range(start, end + 1):
                ports.append(f"{prefix}/{i}")

        else:
            ports.append(part)

    return ports



def create_vlan_on_all(devices):
    vlan_id = input("Enter VLAN ID: ").strip()
    vlan_name = input("Enter VLAN Name: ").strip()

    for d in devices:
        print(f"\n for [{d['name']}] -> enter ports:  .")
        print("Example: fa0/1, fa0/5 or  fa0/0-3 or gi0/1-2, fa0/10")
        ports_input = input(f"{d['name']} ports: ").strip()

        ports = expand_ports(ports_input)
        if not ports:
            print(f"[{d['name']}] PORT isn't assigned for this device.")
            continue

        cfg = [f"vlan {vlan_id}", 
               f"name {vlan_name}", 
               "exit"]
        
        for p in ports:
            cfg.extend([
                f"interface {p}",
                "switchport mode access",
                f"switchport access vlan {vlan_id}",
                "no shutdown",
                "exit"
            ])

        connect_device = connect(d)
        connect_device.send_config_set(cfg)
        connect_device.save_config()
        connect_device.disconnect()

        print(f"[{d['name']}] VLAN {vlan_id} ({vlan_name}) Created and Assigned to given ports : {', '.join(ports)}")


def create_user_on_all (devices):
    new_user=input("Enter New Username: ").strip()
    new_password=input("Enter password: ").strip()
    privilege=input("Enter Privilege: ").strip()

    creating_user_commmands = [
        f"username {new_user} privilege {privilege} secret {new_password}"
    ]

    for dev in devices:
        connect_device=connect(dev)
        output=connect_device.send_config_set(creating_user_commmands)
        connect_device.save_config()
        connect_device.disconnect()
        print(f"{dev['name']} -> USER IS CREATED ({new_user})")


def take_backup_from_all (devices):
    for i in devices:
        connect_device=connect(i)
        output=connect_device.send_command("show running-config")
        connect_device.disconnect()

        path = os.path.join(backup_dir, f"{i['name']}_running-config.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(output)
        
        print(f"{i['name']} -> BACKUP OKAY ! : {path}")




def main ():
    devices=read_load_devices()

    while True:
        print ("\n ----  CISCO NETWORK AUTOMATION TOOL VERISON 21.0   by amrah")
        print("\n")
        print("SELECT NUMBER FOR AUTO-OPERATIONS") 
        print("\n")
        print("1: apply show command to all")
        print("2: create VLANs")
        print("3: Create users")
        print("4: take backup files for all devices")
        print("0: Exit")

        opt=input("ENTER NUMBER: ").strip()

        if opt == "1":
            run_show_command_on_all(devices)
        elif opt == "2":
            create_vlan_on_all(devices)
        elif opt == "3":
            create_user_on_all(devices)
        elif opt == "4":
            take_backup_from_all(devices)
        elif opt == "0":
            break
        else:
            print("nOt FoUnD ERROr ..// please select available number //- ")


if __name__ == "__main__":
    main()



