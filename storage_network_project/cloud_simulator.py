import time
import random
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import threading

class VMStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"

class CloudletStatus(Enum):
    CREATED = "created"
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class VirtualMachine:
    """Simulated Virtual Machine"""
    vm_id: str
    mips: int  # Million Instructions Per Second
    ram: int  # MB
    bandwidth: int  # Mbps
    storage: int  # GB
    cores: int

    # Runtime state
    status: VMStatus = VMStatus.IDLE
    current_cloudlet: Optional['Cloudlet'] = None
    total_executed: int = 0
    total_execution_time: float = 0
    utilization_history: List[float] = None

    def __post_init__(self):
        if self.utilization_history is None:
            self.utilization_history = []

    def get_utilization(self) -> float:
        """Calculate current utilization percentage"""
        if self.status == VMStatus.BUSY:
            return 100.0
        return 0.0

    def can_execute(self, cloudlet: 'Cloudlet') -> bool:
        """Check if VM can handle this cloudlet"""
        return (self.ram >= cloudlet.required_ram and
                self.storage >= cloudlet.required_storage)

@dataclass
class Cloudlet:
    """Simulated computational task (file transfer job)"""
    cloudlet_id: int
    length: int  # Million Instructions
    file_size: int  # MB
    required_ram: int  # MB
    required_storage: int  # GB
    priority: int = 1

    # Runtime state
    status: CloudletStatus = CloudletStatus.CREATED
    assigned_vm: Optional[str] = None
    submission_time: float = 0
    start_time: float = 0
    finish_time: float = 0
    waiting_time: float = 0
    execution_time: float = 0

    def get_total_time(self) -> float:
        """Total time from submission to completion"""
        if self.finish_time > 0:
            return self.finish_time - self.submission_time
        return 0

class CloudScheduler:
    """Scheduling algorithms for cloudlet-to-VM assignment"""

    @staticmethod
    def round_robin(cloudlet: Cloudlet, vms: List[VirtualMachine]) -> Optional[VirtualMachine]:
        """Simple round-robin scheduling"""
        available_vms = [vm for vm in vms if vm.status == VMStatus.IDLE and vm.can_execute(cloudlet)]
        if not available_vms:
            return None
        return min(available_vms, key=lambda v: v.total_executed)

    @staticmethod
    def first_fit(cloudlet: Cloudlet, vms: List[VirtualMachine]) -> Optional[VirtualMachine]:
        """First available VM that can handle the task"""
        for vm in vms:
            if vm.status == VMStatus.IDLE and vm.can_execute(cloudlet):
                return vm
        return None

    @staticmethod
    def min_min(cloudlet: Cloudlet, vms: List[VirtualMachine]) -> Optional[VirtualMachine]:
        """Select VM with minimum expected completion time"""
        available_vms = [vm for vm in vms if vm.status == VMStatus.IDLE and vm.can_execute(cloudlet)]
        if not available_vms:
            return None

        # Calculate expected completion time for each VM
        completion_times = []
        for vm in available_vms:
            exec_time = cloudlet.length / (vm.mips * vm.cores)
            completion_times.append((vm, exec_time))

        return min(completion_times, key=lambda x: x[1])[0]

class CloudDatacenter:
    """Simulated datacenter managing VMs and cloudlets"""

    def __init__(self, datacenter_id: str, scheduling_policy: str = "round_robin"):
        self.datacenter_id = datacenter_id
        self.vms: List[VirtualMachine] = []
        self.cloudlet_queue: List[Cloudlet] = []
        self.completed_cloudlets: List[Cloudlet] = []
        self.failed_cloudlets: List[Cloudlet] = []
        self.scheduling_policy = scheduling_policy
        self.simulation_time = 0.0
        self.is_running = False

    def add_vm(self, vm: VirtualMachine):
        """Add a VM to the datacenter"""
        self.vms.append(vm)
        print(f"✅ VM {vm.vm_id} added to datacenter {self.datacenter_id}")

    def submit_cloudlet(self, cloudlet: Cloudlet):
        """Submit a cloudlet for execution"""
        cloudlet.submission_time = self.simulation_time
        cloudlet.status = CloudletStatus.QUEUED
        self.cloudlet_queue.append(cloudlet)
        print(f"📥 Cloudlet {cloudlet.cloudlet_id} submitted (Size: {cloudlet.file_size}MB, Length: {cloudlet.length}MI)")

    def schedule_cloudlets(self):
        """Assign queued cloudlets to available VMs"""
        if not self.cloudlet_queue:
            return

        scheduler = {
            "round_robin": CloudScheduler.round_robin,
            "first_fit": CloudScheduler.first_fit,
            "min_min": CloudScheduler.min_min
        }.get(self.scheduling_policy, CloudScheduler.round_robin)

        i = 0
        while i < len(self.cloudlet_queue):
            cloudlet = self.cloudlet_queue[i]
            vm = scheduler(cloudlet, self.vms)

            if vm:
                # Assign cloudlet to VM
                cloudlet.assigned_vm = vm.vm_id
                cloudlet.status = CloudletStatus.EXECUTING
                cloudlet.start_time = self.simulation_time
                cloudlet.waiting_time = cloudlet.start_time - cloudlet.submission_time

                vm.status = VMStatus.BUSY
                vm.current_cloudlet = cloudlet

                # Calculate execution time
                exec_time = cloudlet.length / (vm.mips * vm.cores)
                cloudlet.execution_time = exec_time

                print(f"🔄 Cloudlet {cloudlet.cloudlet_id} assigned to VM {vm.vm_id} (Est. time: {exec_time:.2f}s)")

                # Remove from queue
                self.cloudlet_queue.pop(i)

                # Simulate execution in background
                threading.Thread(target=self._execute_cloudlet, args=(vm, cloudlet), daemon=True).start()
            else:
                i += 1

    def _execute_cloudlet(self, vm: VirtualMachine, cloudlet: Cloudlet):
        """Simulate cloudlet execution"""
        # Simulate processing time
        time.sleep(cloudlet.execution_time)

        # Complete cloudlet
        cloudlet.finish_time = self.simulation_time + cloudlet.execution_time
        cloudlet.status = CloudletStatus.COMPLETED

        vm.status = VMStatus.IDLE
        vm.current_cloudlet = None
        vm.total_executed += 1
        vm.total_execution_time += cloudlet.execution_time

        self.completed_cloudlets.append(cloudlet)

        print(f"✅ Cloudlet {cloudlet.cloudlet_id} completed on VM {vm.vm_id} (Time: {cloudlet.execution_time:.2f}s)")

        # Try to schedule more cloudlets
        self.schedule_cloudlets()

    def get_statistics(self) -> dict:
        """Get simulation statistics"""
        total_cloudlets = len(self.completed_cloudlets) + len(self.cloudlet_queue) + len(self.failed_cloudlets)
        completed = len(self.completed_cloudlets)

        avg_waiting_time = 0
        avg_execution_time = 0
        avg_total_time = 0

        if self.completed_cloudlets:
            avg_waiting_time = sum(c.waiting_time for c in self.completed_cloudlets) / len(self.completed_cloudlets)
            avg_execution_time = sum(c.execution_time for c in self.completed_cloudlets) / len(self.completed_cloudlets)
            avg_total_time = sum(c.get_total_time() for c in self.completed_cloudlets) / len(self.completed_cloudlets)

        vm_utilization = {}
        for vm in self.vms:
            if self.simulation_time > 0:
                utilization = (vm.total_execution_time / self.simulation_time) * 100
                vm_utilization[vm.vm_id] = utilization
            else:
                vm_utilization[vm.vm_id] = 0

        return {
            "total_cloudlets": total_cloudlets,
            "completed": completed,
            "queued": len(self.cloudlet_queue),
            "failed": len(self.failed_cloudlets),
            "avg_waiting_time": avg_waiting_time,
            "avg_execution_time": avg_execution_time,
            "avg_total_time": avg_total_time,
            "vm_utilization": vm_utilization,
            "simulation_time": self.simulation_time
        }

    def run_simulation(self, duration: float = 60.0):
        """Run simulation for specified duration"""
        self.is_running = True
        start_time = time.time()

        print(f"\n{'='*60}")
        print(f"🚀 Starting Simulation - Datacenter: {self.datacenter_id}")
        print(f"{'='*60}")

        while self.is_running and (time.time() - start_time) < duration:
            self.simulation_time = time.time() - start_time

            # Schedule queued cloudlets
            self.schedule_cloudlets()

            # Update VM utilization history
            for vm in self.vms:
                vm.utilization_history.append(vm.get_utilization())

            time.sleep(0.5)  # Update interval

        print(f"\n{'='*60}")
        print(f"✅ Simulation Complete")
        print(f"{'='*60}")

        return self.get_statistics()