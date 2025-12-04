import random
from cloud_simulator import CloudDatacenter, VirtualMachine, Cloudlet, VMStatus
import time

class SimulationController:
    """Controls the overall cloud simulation"""

    def __init__(self):
        self.datacenter = CloudDatacenter("DC1", scheduling_policy="min_min")
        self.cloudlet_counter = 0
        self.setup_infrastructure()

    def setup_infrastructure(self):
        """Create virtual machines"""
        # Create 5 VMs with different specs (matching your nodes)
        vm_configs = [
            {"vm_id": "VM1", "mips": 1000, "ram": 4096, "bandwidth": 1000, "storage": 15, "cores": 2},
            {"vm_id": "VM2", "mips": 2000, "ram": 8192, "bandwidth": 2000, "storage": 15, "cores": 4},
            {"vm_id": "VM3", "mips": 1500, "ram": 4096, "bandwidth": 1500, "storage": 15, "cores": 2},
            {"vm_id": "VM4", "mips": 2500, "ram": 16384, "bandwidth": 2500, "storage": 15, "cores": 8},
            {"vm_id": "VM5", "mips": 1200, "ram": 8192, "bandwidth": 1200, "storage": 15, "cores": 4},
        ]

        for config in vm_configs:
            vm = VirtualMachine(**config)
            self.datacenter.add_vm(vm)

    def submit_file_transfer(self, file_size_mb: int, priority: int = 1):
        """Submit a file transfer as a cloudlet"""
        # Calculate computational requirements
        # Assume: 1MB file = 100 MI (Million Instructions)
        # Includes: network transfer + checksum calculation + disk write
        length = file_size_mb * 100

        # RAM needed: buffer for file
        required_ram = min(file_size_mb, 512)  # Cap at 512MB buffer

        # Storage needed in GB
        required_storage = file_size_mb / 1024

        cloudlet = Cloudlet(
            cloudlet_id=self.cloudlet_counter,
            length=length,
            file_size=file_size_mb,
            required_ram=required_ram,
            required_storage=required_storage,
            priority=priority
        )

        self.cloudlet_counter += 1
        self.datacenter.submit_cloudlet(cloudlet)

        return cloudlet.cloudlet_id

    def get_vm_status(self):
        """Get status of all VMs"""
        status = []
        for vm in self.datacenter.vms:
            status.append({
                "vm_id": vm.vm_id,
                "status": vm.status.value,
                "mips": vm.mips,
                "cores": vm.cores,
                "ram": vm.ram,
                "current_task": vm.current_cloudlet.cloudlet_id if vm.current_cloudlet else None,
                "total_executed": vm.total_executed,
                "utilization": vm.get_utilization()
            })
        return status

    def get_queue_status(self):
        """Get queued cloudlets"""
        return [{
            "cloudlet_id": c.cloudlet_id,
            "file_size": c.file_size,
            "status": c.status.value,
            "waiting_time": self.datacenter.simulation_time - c.submission_time if c.submission_time > 0 else 0
        } for c in self.datacenter.cloudlet_queue]

    def get_completed_tasks(self):
        """Get completed cloudlets"""
        return [{
            "cloudlet_id": c.cloudlet_id,
            "file_size": c.file_size,
            "vm": c.assigned_vm,
            "waiting_time": c.waiting_time,
            "execution_time": c.execution_time,
            "total_time": c.get_total_time()
        } for c in self.datacenter.completed_cloudlets]

    def get_statistics(self):
        """Get overall statistics"""
        return self.datacenter.get_statistics()

    def start_simulation(self):
        """Start the simulation"""
        import threading
        simulation_thread = threading.Thread(
            target=self.datacenter.run_simulation,
            args=(3600,),  # Run for 1 hour
            daemon=True
        )
        simulation_thread.start()

# Global simulation instance
sim_controller = None

def get_simulation():
    """Get or create simulation controller"""
    global sim_controller
    if sim_controller is None:
        sim_controller = SimulationController()
        sim_controller.start_simulation()
    return sim_controller